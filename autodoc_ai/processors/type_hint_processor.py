"""
Type hint addition processor.
Adds type hints to Python functions, skipping dead code.
"""

from typing import Set, Any, Optional, Dict
from .base import BaseProcessor


class TypeHintProcessor(BaseProcessor):
    """Adds type hints to Python functions, skipping dead code."""
    
    def process(self, generator: Any, dead_functions: Optional[Set[str]] = None) -> None:
        """
        Add type hints to functions, skipping dead code.
        
        Args:
            generator: Generator instance for AI-powered type inference
            dead_functions: Set of dead function names to skip
        """
        if self.lang != 'python':
            return  # Type hints only for Python currently
        
        dead_functions = dead_functions or set()
        typing_imports_needed = set()
        
        # Get all functions
        all_functions = self.get_function_nodes()
        
        # Find functions with type hints
        functions_with_hints = set()
        for func_node in all_functions:
            if func_node.child_by_field_name('return_type'):
                functions_with_hints.add(func_node)
        
        # Find functions without type hints
        functions_without_hints = all_functions - functions_with_hints
        
        processed_count = 0
        skipped_count = 0
        
        for func_node in functions_without_hints:
            name_node = func_node.child_by_field_name('name')
            if not name_node:
                continue
            
            func_name = name_node.text.decode('utf8')
            
            # Skip dead functions!
            if func_name in dead_functions:
                skipped_count += 1
                continue
            
            # Skip special methods like __init__, __str__, etc.
            if func_name.startswith('__') and func_name.endswith('__'):
                continue
            
            line_num = name_node.start_point[0] + 1
            print(f"  [TYPE] Line {line_num}: Adding type hints to `{func_name}()`", flush=True)
            
            try:
                type_hints = generator.generate_type_hints(func_node)
                
                if not type_hints or (not type_hints.get('parameters') and not type_hints.get('return_type')):
                    print(f"     [WARN] Could not infer types for `{func_name}()`")
                    continue
                
                # Build new function signature
                new_signature, needed_imports = self._build_new_signature(
                    func_node, func_name, type_hints
                )
                
                if new_signature:
                    # Find the colon that ends the function signature
                    colon_byte = None
                    for child in func_node.children:
                        if child.type == ':':
                            colon_byte = child.start_byte
                            break
                    
                    if colon_byte:
                        # Replace from 'def' to ':' (inclusive)
                        self.transformer.add_change(
                            start_byte=func_node.start_byte,
                            end_byte=colon_byte + 1,
                            new_text=new_signature
                        )
                        typing_imports_needed.update(needed_imports)
                        processed_count += 1
                
            except Exception as e:
                print(f"  [ERROR] Adding type hints to `{func_name}`: {e}", flush=True)
                continue
        
        # Add typing import if needed
        if typing_imports_needed:
            self._add_typing_import(typing_imports_needed)
        
        if skipped_count > 0:
            print(f"  [TYPE] Processed {processed_count} functions, skipped {skipped_count} dead functions")
    
    def _build_new_signature(self, func_node: Any, func_name: str, 
                            type_hints: Dict[str, Any]) -> tuple:
        """
        Build new function signature with type hints.
        
        Returns:
            Tuple of (new_signature, needed_typing_imports)
        """
        params_node = func_node.child_by_field_name('parameters')
        if not params_node:
            return None, set()
        
        needed_imports = set()
        new_params = []
        
        for param_child in params_node.children:
            if param_child.type == 'identifier':
                param_name = param_child.text.decode('utf8')
                type_hint = type_hints.get('parameters', {}).get(param_name)
                
                if type_hint:
                    new_params.append(f"{param_name}: {type_hint}")
                    self._check_typing_imports(type_hint, needed_imports)
                else:
                    new_params.append(param_name)
                    
            elif param_child.type in ['(', ')', ',']:
                continue
                
            elif param_child.type == 'default_parameter':
                param_id = param_child.child_by_field_name('name')
                param_default = param_child.child_by_field_name('value')
                
                if param_id:
                    param_name = param_id.text.decode('utf8')
                    type_hint = type_hints.get('parameters', {}).get(param_name)
                    default_val = param_default.text.decode('utf8') if param_default else ''
                    
                    if type_hint:
                        new_params.append(f"{param_name}: {type_hint} = {default_val}")
                        self._check_typing_imports(type_hint, needed_imports)
                    else:
                        new_params.append(f"{param_name} = {default_val}")
                        
            elif param_child.type == 'typed_parameter':
                # Already has type hint
                new_params.append(param_child.text.decode('utf8'))
                
            elif param_child.type == 'typed_default_parameter':
                # Already has type hint with default
                new_params.append(param_child.text.decode('utf8'))
        
        # Build signature
        return_type = type_hints.get('return_type')
        params_str = ', '.join(new_params)
        
        if return_type:
            new_signature = f"def {func_name}({params_str}) -> {return_type}:"
            self._check_typing_imports(return_type, needed_imports)
        else:
            new_signature = f"def {func_name}({params_str}):"
        
        return new_signature, needed_imports
    
    def _check_typing_imports(self, type_str: str, needed_imports: Set[str]) -> None:
        """Check if type string requires typing module imports."""
        typing_types = ['List', 'Dict', 'Tuple', 'Set', 'Optional', 
                       'Union', 'Any', 'Callable']
        for typing_type in typing_types:
            if typing_type in type_str:
                needed_imports.add(typing_type)
    
    def _add_typing_import(self, typing_imports_needed: Set[str]) -> None:
        """Add typing import statement at the beginning of the file."""
        # Check if typing import already exists
        has_typing_import = ('from typing import' in self.source_text or 
                           'import typing' in self.source_text)
        
        if not has_typing_import:
            imports_str = ', '.join(sorted(typing_imports_needed))
            import_statement = f"from typing import {imports_str}\n\n"
            
            self.transformer.add_change(
                start_byte=0,
                end_byte=0,
                new_text=import_statement
            )
            print(f"  [ADD] Added typing import: {imports_str}")
