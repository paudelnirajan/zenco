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
        never_called = [(name, ln) for (name, ln) in func_defs if name not in func_calls]
        for name, ln in never_called:
            print(f"  • Function never called: {name} (line {ln})")
            dead_functions.add(name)  # Add to dead set for filtering
        
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
        
        # Apply deletions if in_place
        if in_place and to_delete_lines:
            for ln in sorted(to_delete_lines, reverse=True):
                line_start = sum(len(l) + 1 for l in lines[:ln-1])
                line_end = line_start + len(lines[ln-1]) + 1
                self.transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
            print(f"  [REMOVE]  Removed {len(to_delete_lines)} unused import line(s)")
        
        if in_place and strict and unused_vars:
            for _, ln, _ in sorted(unused_vars, key=lambda x: x[1], reverse=True):
                line_start = sum(len(l) + 1 for l in lines[:ln-1])
                line_end = line_start + len(lines[ln-1]) + 1
                self.transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
            print(f"  [REMOVE]  Strict: Removed {len(unused_vars)} unused variable(s)")
        
        return dead_functions
    
    def _process_javascript(self, in_place: bool, strict: bool) -> Set[str]:
        """JavaScript dead code detection."""
        dead_functions = set()
        print("\n  [CLEANUP] Dead Code Report (JavaScript):")
        
        # 1. Find all function declarations and variable declarations
        # We'll look for:
        # - function_declaration (name)
        # - variable_declarator (name)
        # - arrow_function (assigned to variable)
        
        definitions = {}  # name -> node
        
        def find_definitions(node):
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf8')
                    definitions[name] = {'node': node, 'type': 'function', 'line': node.start_point[0] + 1}
            
            elif node.type == 'variable_declarator':
                name_node = node.child_by_field_name('name')
                if name_node and name_node.type == 'identifier':
                    name = name_node.text.decode('utf8')
                    definitions[name] = {'node': node, 'type': 'variable', 'line': node.start_point[0] + 1}
            
            for child in node.children:
                find_definitions(child)

        find_definitions(self.tree.root_node)
        
        # 2. Find all usages
        used_names = set()
        
        def find_usages(node):
            # If it's an identifier and NOT a declaration name, it's a usage
            if node.type == 'identifier':
                parent = node.parent
                is_decl = False
                
                if parent.type == 'function_declaration' and parent.child_by_field_name('name') == node:
                    is_decl = True
                elif parent.type == 'variable_declarator' and parent.child_by_field_name('name') == node:
                    is_decl = True
                elif parent.type == 'property_identifier':
                    is_decl = True # Object property definition, not usage of variable
                
                if not is_decl:
                    used_names.add(node.text.decode('utf8'))
            
            for child in node.children:
                find_usages(child)
                
        find_usages(self.tree.root_node)
        
        # 3. Identify dead code
        unused_items = []
        for name, info in definitions.items():
            if name not in used_names:
                # Skip 'main' or common entry points if needed, but for now be strict
                unused_items.append((name, info))
        
        # 4. Report and collect
        for name, info in unused_items:
            if info['type'] == 'function':
                print(f"  • Function never called: {name} (line {info['line']})")
                dead_functions.add(name)
            else:
                print(f"  • Unused variable: {name} (line {info['line']})")
        
        # 5. Remove if in_place (Basic removal)
        if in_place and unused_items:
            # Sort reverse to avoid offset issues
            unused_items.sort(key=lambda x: x[1]['node'].start_byte, reverse=True)
            
            removed_count = 0
            for name, info in unused_items:
                node = info['node']
                # For variables, we might need to remove the whole statement if it's `let x = 1;`
                # For functions, remove the whole definition
                
                target_node = node
                if info['type'] == 'variable':
                    # If it's `const x = 1;`, the variable_declarator is inside a lexical_declaration
                    if node.parent.type == 'lexical_declaration':
                        target_node = node.parent
                
                self.transformer.add_change(
                    start_byte=target_node.start_byte,
                    end_byte=target_node.end_byte,
                    new_text=''
                )
                removed_count += 1
            
            if removed_count > 0:
                print(f"  [REMOVE] Removed {removed_count} unused item(s)")
                
        return dead_functions
    
    def _process_java(self, in_place: bool, strict: bool) -> Set[str]:
        """Java dead code detection."""
        dead_functions = set()
        print("\n  [CLEANUP] Dead Code Report (Java):")
        
        # 1. Find declarations (private methods, private fields, local variables)
        definitions = {}  # name -> {node, type, line}
        
        def get_name_from_declarator(declarator_node):
            name_node = declarator_node.child_by_field_name('name')
            if not name_node:
                for child in declarator_node.children:
                    if child.type == 'identifier':
                        name_node = child
                        break
            return name_node

        def find_definitions(node):
            # Private Methods
            if node.type == 'method_declaration':
                modifiers = node.child_by_field_name('modifiers')
                if not modifiers:
                    for child in node.children:
                        if child.type == 'modifiers':
                            modifiers = child
                            break
                
                is_private = False
                if modifiers:
                    for child in modifiers.children:
                        if child.text.decode('utf8') == 'private':
                            is_private = True
                            break
                
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf8')
                    if is_private:
                        # print(f"DEBUG: Found private method {name}")
                        definitions[name] = {'node': node, 'type': 'private method', 'line': node.start_point[0] + 1}

            # Private Fields
            elif node.type == 'field_declaration':
                modifiers = node.child_by_field_name('modifiers')
                if not modifiers:
                    for child in node.children:
                        if child.type == 'modifiers':
                            modifiers = child
                            break
                
                is_private = False
                if modifiers:
                    for child in modifiers.children:
                        if child.text.decode('utf8') == 'private':
                            is_private = True
                            break
                
                if is_private:
                    # Fields can be multiple: private int x, y;
                    for child in node.children:
                        if child.type == 'variable_declarator':
                            name_node = get_name_from_declarator(child)
                            if name_node:
                                name = name_node.text.decode('utf8')
                                # print(f"DEBUG: Found private field {name}")
                                definitions[name] = {'node': child, 'type': 'private field', 'line': name_node.start_point[0] + 1}

            # Local Variables
            elif node.type == 'local_variable_declaration':
                for child in node.children:
                    if child.type == 'variable_declarator':
                        name_node = get_name_from_declarator(child)
                        if name_node:
                            name = name_node.text.decode('utf8')
                            # print(f"DEBUG: Found local variable {name}")
                            definitions[name] = {'node': node, 'type': 'local variable', 'line': name_node.start_point[0] + 1}
            
            for child in node.children:
                find_definitions(child)
                
        find_definitions(self.tree.root_node)
        
        # 2. Find usages
        used_names = set()
        
        def find_usages(node):
            # Check for identifiers that are NOT part of a declaration
            if node.type == 'identifier':
                parent = node.parent
                is_decl = False
                
                # Check if this identifier is defining a method, field, or variable
                if parent.type == 'method_declaration' and parent.child_by_field_name('name') == node:
                    is_decl = True
                elif parent.type == 'variable_declarator' and get_name_from_declarator(parent) == node:
                    is_decl = True
                elif parent.type == 'class_declaration' and parent.child_by_field_name('name') == node:
                    is_decl = True
                
                if not is_decl:
                    # print(f"DEBUG: Found usage {node.text.decode('utf8')}")
                    used_names.add(node.text.decode('utf8'))
            
            for child in node.children:
                find_usages(child)
        
        find_usages(self.tree.root_node)
        
        # 3. Identify dead code
        unused_items = []
        for name, info in definitions.items():
            if name not in used_names:
                unused_items.append((name, info))
        
        # 4. Report
        for name, info in unused_items:
            print(f"  • Unused {info['type']}: {name} (line {info['line']})")
            if info['type'] == 'private method':
                dead_functions.add(name)
            
        # 5. Remove if in_place
        if in_place and unused_items:
            unused_items.sort(key=lambda x: x[1]['node'].start_byte, reverse=True)
            removed_count = 0
            for name, info in unused_items:
                node = info['node']
                target_node = node
                if info['type'] == 'private field':
                    if node.parent.type == 'field_declaration':
                        target_node = node.parent

                self.transformer.add_change(
                    start_byte=target_node.start_byte,
                    end_byte=target_node.end_byte,
                    new_text=''
                )
                removed_count += 1
            
            if removed_count > 0:
                print(f"  [REMOVE] Removed {removed_count} unused item(s)")
                
        return dead_functions
    
    def _process_go(self, in_place: bool, strict: bool) -> Set[str]:
        """Go dead code detection."""
        dead_functions = set()
        print("\n  [CLEANUP] Dead Code Report (Go):")
        
        # 1. Find unexported functions (lowercase start)
        unexported_functions = {}  # name -> node
        
        def find_functions(node):
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf8')
                    # In Go, lowercase first letter means unexported (private to package)
                    if name and name[0].islower() and name != 'main' and name != 'init':
                        unexported_functions[name] = {'node': node, 'line': node.start_point[0] + 1}
            
            for child in node.children:
                find_functions(child)
        
        find_functions(self.tree.root_node)
        
        # 2. Find usages
        used_names = set()
        
        def find_usages(node):
            if node.type == 'call_expression':
                function_node = node.child_by_field_name('function')
                if function_node:
                    if function_node.type == 'identifier':
                        used_names.add(function_node.text.decode('utf8'))
                    elif function_node.type == 'selector_expression':
                        field = function_node.child_by_field_name('field')
                        if field:
                            used_names.add(field.text.decode('utf8'))
            
            for child in node.children:
                find_usages(child)
        
        find_usages(self.tree.root_node)
        
        # 3. Identify dead code
        unused_functions = []
        for name, info in unexported_functions.items():
            if name not in used_names:
                unused_functions.append((name, info))
        
        # 4. Report
        for name, info in unused_functions:
            print(f"  • Unused unexported function: {name} (line {info['line']})")
            dead_functions.add(name)
            
        # 5. Remove if in_place
        if in_place and unused_functions:
            unused_functions.sort(key=lambda x: x[1]['node'].start_byte, reverse=True)
            removed_count = 0
            for name, info in unused_functions:
                node = info['node']
                self.transformer.add_change(
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    new_text=''
                )
                removed_count += 1
            
            if removed_count > 0:
                print(f"  [REMOVE] Removed {removed_count} unused function(s)")
                
        return dead_functions
    
    def _process_cpp(self, in_place: bool, strict: bool) -> Set[str]:
        """C++ dead code detection."""
        dead_functions = set()
        print("\n  [CLEANUP] Dead Code Report (C++):")
        
        # 1. Find static functions (internal linkage)
        static_functions = {}  # name -> node
        
        def find_static_functions(node):
            if node.type == 'function_definition':
                storage_class = node.child_by_field_name('storage_class')
                if not storage_class:
                    for child in node.children:
                        if child.type == 'storage_class_specifier':
                            storage_class = child
                            break
                
                is_static = False
                if storage_class and storage_class.text.decode('utf8') == 'static':
                    is_static = True
                
                if is_static:
                    declarator = node.child_by_field_name('declarator')
                    if declarator:
                        # Handle pointer declarators, etc.
                        while declarator.type in ['pointer_declarator', 'reference_declarator', 'function_declarator']:
                            declarator = declarator.child_by_field_name('declarator')
                        
                        if declarator.type == 'identifier':
                            name = declarator.text.decode('utf8')
                            static_functions[name] = {'node': node, 'line': node.start_point[0] + 1}
            
            for child in node.children:
                find_static_functions(child)
        
        find_static_functions(self.tree.root_node)
        
        # 2. Find usages
        used_names = set()
        
        def find_usages(node):
            if node.type == 'call_expression':
                function_node = node.child_by_field_name('function')
                if function_node:
                    if function_node.type == 'identifier':
                        used_names.add(function_node.text.decode('utf8'))
                    elif function_node.type == 'field_expression':
                        field = function_node.child_by_field_name('field')
                        if field:
                            used_names.add(field.text.decode('utf8'))
            
            for child in node.children:
                find_usages(child)
        
        find_usages(self.tree.root_node)
        
        # 3. Identify dead code
        unused_functions = []
        for name, info in static_functions.items():
            if name not in used_names:
                unused_functions.append((name, info))
        
        # 4. Report
        for name, info in unused_functions:
            print(f"  • Unused static function: {name} (line {info['line']})")
            dead_functions.add(name)
            
        # 5. Remove if in_place
        if in_place and unused_functions:
            unused_functions.sort(key=lambda x: x[1]['node'].start_byte, reverse=True)
            removed_count = 0
            for name, info in unused_functions:
                node = info['node']
                self.transformer.add_change(
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    new_text=''
                )
                removed_count += 1
            
            if removed_count > 0:
                print(f"  [REMOVE] Removed {removed_count} unused static function(s)")
                
        return dead_functions
