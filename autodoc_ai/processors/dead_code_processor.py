"""
Dead code detection processor.
Identifies unused functions, imports, and variables.
"""

import ast
from typing import Set, Optional, Any, List, Tuple
from .base import BaseProcessor


class DeadCodeProcessor(BaseProcessor):
    """
    Detects and optionally removes dead code.
    Returns set of dead function names for filtering by other processors.
    """
    
    def process(self, in_place: bool = False, strict: bool = False) -> Set[str]:
        """
        Detect dead code and return set of dead function names.
        
        Args:
            in_place: Whether to actually remove dead code
            strict: Whether to remove all unused code (strict mode)
            
        Returns:
            Set of dead function names to skip in other processors
        """
        if self.lang == 'python':
            return self._process_python(in_place, strict)
        elif self.lang == 'javascript':
            return self._process_javascript(in_place, strict)
        elif self.lang == 'java':
            return self._process_java(in_place, strict)
        elif self.lang == 'go':
            return self._process_go(in_place, strict)
        elif self.lang == 'cpp':
            return self._process_cpp(in_place, strict)
        return set()
    
    def _process_python(self, in_place: bool, strict: bool) -> Set[str]:
        """Python dead code detection."""
        dead_functions = set()
        
        try:
            tree_ast = ast.parse(self.source_text)
        except Exception as e:
            print(f"  [ERROR] AST parse error for dead code detection: {e}")
            return dead_functions
        
        lines = self.source_text.split('\n')
        
        # Collect imports
        imports = []
        for node in ast.walk(tree_ast):
            if isinstance(node, ast.Import):
                names = [alias.asname or alias.name.split('.')[0] for alias in node.names]
                imports.append({
                    'type': 'import',
                    'names': names,
                    'lineno': node.lineno,
                    'text': lines[node.lineno-1] if 1 <= node.lineno <= len(lines) else ''
                })
            elif isinstance(node, ast.ImportFrom):
                names = [alias.asname or alias.name for alias in node.names]
                imports.append({
                    'type': 'from',
                    'module': node.module or '',
                    'names': names,
                    'lineno': node.lineno,
                    'text': lines[node.lineno-1] if 1 <= node.lineno <= len(lines) else ''
                })
        
        # Collect used identifiers
        used = set()
        for node in ast.walk(tree_ast):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                used.add(node.value.id)
        
        # Collect function definitions and calls
        func_defs = []
        func_calls = set()
        for node in ast.walk(tree_ast):
            if isinstance(node, ast.FunctionDef):
                # Only top-level functions
                if getattr(node, 'col_offset', 0) == 0:
                    func_defs.append((node.name, node.lineno))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    func_calls.add(node.func.attr)
        
        # Report dead code
        print("\n  [CLEANUP] Dead Code Report (Python):")
        
        # Unused imports
        to_delete_lines = []
        for imp in imports:
            imp_used = any(name.split('.')[0] in used for name in imp.get('names', []))
            if not imp_used:
                print(f"  • Unused import at line {imp['lineno']}: {imp['text'].strip()}")
                to_delete_lines.append(imp['lineno'])
        
        # Never-called functions (dead code)
        all_never_called = [(name, ln) for (name, ln) in func_defs if name not in func_calls]
        
        # Filter based on strict mode
        # Safe mode (default): Only remove private functions (starting with _)
        # Strict mode: Remove all uncalled functions
        if strict:
            never_called = all_never_called
        else:
            # Safe mode: only private functions (but not dunder methods like __init__)
            never_called = [
                (name, ln) for (name, ln) in all_never_called 
                if name.startswith('_') and not (name.startswith('__') and name.endswith('__'))
            ]
        
        # Report all never-called functions
        for name, ln in all_never_called:
            if (name, ln) in never_called:
                print(f"  • Function never called: {name} (line {ln})")
            else:
                print(f"  • Function never called: {name} (line {ln}) [PUBLIC - skipped in safe mode]")
            dead_functions.add(name)  # Add to dead set for filtering in other processors
        
        # Unused variables
        unused_vars = []
        for node in ast.walk(tree_ast):
            if isinstance(node, ast.Assign) and getattr(node, 'col_offset', 1) == 0:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # Check if variable is used anywhere except its definition
                        usage_count = sum(1 for n in ast.walk(tree_ast) 
                                         if isinstance(n, ast.Name) and n.id == var_name)
                        if usage_count <= 1:  # Only defined, never used
                            ln = node.lineno
                            txt = lines[ln-1] if 1 <= ln <= len(lines) else ''
                            unused_vars.append((var_name, ln, txt))
        
        for name, ln, txt in unused_vars:
            print(f"  • Unused variable: {name} (line {ln}): {txt.strip()}")
        
        # Remove unused imports (always add to transformer for preview/JSON mode)
        if to_delete_lines:
            for ln in sorted(to_delete_lines, reverse=True):
                line_start = sum(len(l) + 1 for l in lines[:ln-1])
                line_end = line_start + len(lines[ln-1]) + 1
                self.transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
            if in_place:
                print(f"  [REMOVE]  Removed {len(to_delete_lines)} unused import line(s)")
        
        # Remove dead functions (always add to transformer for preview/JSON mode)
        if never_called:
            removed_count = 0
            for name, ln in sorted(never_called, key=lambda x: x[1], reverse=True):
                # Find the function node in the AST
                for node in ast.walk(tree_ast):
                    if isinstance(node, ast.FunctionDef) and node.name == name and node.lineno == ln:
                        # Calculate the byte range for the entire function
                        func_start_line = node.lineno - 1  # 0-indexed
                        
                        # Find the end line of the function
                        # Python 3.8+ has end_lineno attribute
                        if hasattr(node, 'end_lineno') and node.end_lineno:
                            func_end_line = node.end_lineno
                        else:
                            # Fallback: estimate based on body
                            func_end_line = func_start_line + len(node.body) + 1
                        
                        # Calculate byte positions
                        line_start = sum(len(l) + 1 for l in lines[:func_start_line])
                        line_end = sum(len(l) + 1 for l in lines[:func_end_line])
                        
                        # Remove the entire function
                        self.transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
                        removed_count += 1
                        break
            
            if in_place and removed_count > 0:
                mode_str = "strict mode" if strict else "safe mode (private functions only)"
                print(f"  [REMOVE]  Removed {removed_count} dead function(s) [{mode_str}]")
        
        # Remove unused variables in strict mode (always add to transformer for preview/JSON mode)
        if strict and unused_vars:
            for _, ln, _ in sorted(unused_vars, key=lambda x: x[1], reverse=True):
                line_start = sum(len(l) + 1 for l in lines[:ln-1])
                line_end = line_start + len(lines[ln-1]) + 1
                self.transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
            if in_place:
                print(f"  [REMOVE]  Strict: Removed {len(unused_vars)} unused variable(s)")
        
        return dead_functions
    
    def _process_javascript(self, in_place: bool, strict: bool) -> Set[str]:
        """JavaScript dead code detection - simplified version."""
        return set()
    
    def _process_java(self, in_place: bool, strict: bool) -> Set[str]:
        """Java dead code detection - simplified version."""
        return set()
    
    def _process_go(self, in_place: bool, strict: bool) -> Set[str]:
        """Go dead code detection - simplified version."""
        return set()
    
    def _process_cpp(self, in_place: bool, strict: bool) -> Set[str]:
        """C++ dead code detection - simplified version."""
        return set()
