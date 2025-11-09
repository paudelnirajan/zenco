"""
Magic number replacement processor.
Replaces magic numbers with named constants across all languages.
"""

from typing import Set, Any, Optional, List, Tuple, Dict
from .base import BaseProcessor


class MagicNumberProcessor(BaseProcessor):
    """Replaces magic numbers with named constants, skipping dead code."""
    
    def process(self, generator: Any, dead_functions: Optional[Set[str]] = None) -> None:
        """
        Replace magic numbers with constants, skipping dead code.
        
        Args:
            generator: Generator instance for naming suggestions
            dead_functions: Set of dead function names to skip
        """
        dead_functions = dead_functions or set()
        
        if self.lang == 'python':
            self._process_python(generator, dead_functions)
        elif self.lang == 'javascript':
            self._process_javascript(generator, dead_functions)
        elif self.lang == 'java':
            self._process_java(generator, dead_functions)
        elif self.lang == 'go':
            self._process_go(generator, dead_functions)
        elif self.lang == 'cpp':
            self._process_cpp(generator, dead_functions)
    
    def _process_python(self, generator: Any, dead_functions: Set[str]) -> None:
        """Process Python magic numbers."""
        # Find numeric literals
        def find_numeric_literals(node):
            results = []
            if node.type in ['integer', 'float']:
                results.append(node)
            for child in node.children:
                results.extend(find_numeric_literals(child))
            return results
        
        numeric_nodes = find_numeric_literals(self.tree.root_node)
        magic_numbers = {}
        
        for node in numeric_nodes:
            value = node.text.decode('utf8')
            
            # Skip acceptable numbers
            if value in ['0', '1', '-1', '2', 'True', 'False']:
                continue
            
            # Skip numbers in default parameters
            parent = node.parent
            if parent and parent.type == 'default_parameter':
                continue
            
            # Find containing function
            current = node.parent
            function_node = None
            func_name = None
            while current:
                if current.type == 'function_definition':
                    function_node = current
                    func_name = self.get_function_name(function_node)
                    break
                current = current.parent
            
            # Skip if in dead function
            if func_name and func_name in dead_functions:
                continue
            
            if value not in magic_numbers:
                magic_numbers[value] = []
            magic_numbers[value].append((node, function_node))
        
        # Process magic numbers
        constants_to_add, replacements = self._generate_replacements(
            magic_numbers, generator
        )
        
        # Apply replacements
        self._apply_replacements(replacements)
        
        # Add constants at module level
        if constants_to_add:
            self._add_python_constants(constants_to_add)
    
    def _process_javascript(self, generator: Any, dead_functions: Set[str]) -> None:
        """Process JavaScript magic numbers."""
        def find_js_numbers(node):
            results = []
            if node.type == 'number':
                results.append(node)
            for child in node.children:
                results.extend(find_js_numbers(child))
            return results
        
        magic_numbers = {}
        for node in find_js_numbers(self.tree.root_node):
            value = node.text.decode('utf8')
            if value in ['0', '1', '-1', '2']:
                continue
            
            # Find containing function
            current = node.parent
            func_node = None
            func_name = None
            while current:
                if current.type in ['function_declaration', 'method_definition']:
                    func_node = current
                    func_name = self.get_function_name(func_node)
                    break
                current = current.parent
            
            # Skip if in dead function
            if func_name and func_name in dead_functions:
                continue
            
            if value not in magic_numbers:
                magic_numbers[value] = []
            magic_numbers[value].append((node, func_node))
        
        constants_to_add, replacements = self._generate_replacements(
            magic_numbers, generator
        )
        self._apply_replacements(replacements)
        
        if constants_to_add:
            self._add_javascript_constants(constants_to_add)
    
    def _process_java(self, generator: Any, dead_functions: Set[str]) -> None:
        """Process Java magic numbers."""
        def find_java_numbers(node):
            results = []
            if node.type in ['decimal_integer_literal', 'decimal_floating_point_literal']:
                results.append(node)
            for child in node.children:
                results.extend(find_java_numbers(child))
            return results
        
        magic_numbers = {}
        for node in find_java_numbers(self.tree.root_node):
            value = node.text.decode('utf8')
            if value in ['0', '1', '-1', '2']:
                continue
            
            current = node.parent
            func_node = None
            func_name = None
            while current:
                if current.type == 'method_declaration':
                    func_node = current
                    func_name = self.get_function_name(func_node)
                    break
                current = current.parent
            
            if func_name and func_name in dead_functions:
                continue
            
            if value not in magic_numbers:
                magic_numbers[value] = []
            magic_numbers[value].append((node, func_node))
        
        constants_to_add, replacements = self._generate_replacements(
            magic_numbers, generator
        )
        self._apply_replacements(replacements)
        
        if constants_to_add:
            self._add_java_constants(constants_to_add)
    
    def _process_go(self, generator: Any, dead_functions: Set[str]) -> None:
        """Process Go magic numbers."""
        def find_go_numbers(node):
            results = []
            if node.type in ['int_lit', 'float_lit']:
                results.append(node)
            for child in node.children:
                results.extend(find_go_numbers(child))
            return results
        
        magic_numbers = {}
        for node in find_go_numbers(self.tree.root_node):
            value = node.text.decode('utf8')
            if value in ['0', '1', '-1', '2']:
                continue
            
            current = node.parent
            func_node = None
            func_name = None
            while current:
                if current.type == 'function_declaration':
                    func_node = current
                    func_name = self.get_function_name(func_node)
                    break
                current = current.parent
            
            if func_name and func_name in dead_functions:
                continue
            
            if value not in magic_numbers:
                magic_numbers[value] = []
            magic_numbers[value].append((node, func_node))
        
        constants_to_add, replacements = self._generate_replacements(
            magic_numbers, generator
        )
        self._apply_replacements(replacements)
        
        if constants_to_add:
            self._add_go_constants(constants_to_add)
    
    def _process_cpp(self, generator: Any, dead_functions: Set[str]) -> None:
        """Process C++ magic numbers."""
        def find_cpp_numbers(node):
            results = []
            if node.type == 'number_literal':
                results.append(node)
            for child in node.children:
                results.extend(find_cpp_numbers(child))
            return results
        
        magic_numbers = {}
        for node in find_cpp_numbers(self.tree.root_node):
            value = node.text.decode('utf8')
            if value in ['0', '1', '-1', '2']:
                continue
            
            current = node.parent
            func_node = None
            func_name = None
            while current:
                if current.type == 'function_definition':
                    func_node = current
                    func_name = self.get_function_name(func_node)
                    break
                current = current.parent
            
            if func_name and func_name in dead_functions:
                continue
            
            if value not in magic_numbers:
                magic_numbers[value] = []
            magic_numbers[value].append((node, func_node))
        
        constants_to_add, replacements = self._generate_replacements(
            magic_numbers, generator
        )
        self._apply_replacements(replacements)
        
        if constants_to_add:
            self._add_cpp_constants(constants_to_add)
    
    def _generate_replacements(self, magic_numbers: Dict, generator: Any) -> Tuple[List, List]:
        """Generate constant names and replacement list."""
        constants_to_add = []
        replacements = []
        
        for value, occurrences in magic_numbers.items():
            first_node, first_function = occurrences[0]
            function_code = first_function.text.decode('utf8') if first_function else self.source_text
            
            line_num = first_node.start_point[0] + 1
            print(f"  [MAGIC] Line {line_num}: Found magic number `{value}`", flush=True)
            
            constant_name = generator.suggest_constant_name(function_code, value)
            
            if constant_name:
                print(f"     → Suggested constant: {constant_name}")
                constants_to_add.append((constant_name, value))
                
                for node, _ in occurrences:
                    replacements.append((node, constant_name))
            else:
                print(f"     [WARN]  Could not generate meaningful name, skipping")
        
        return constants_to_add, replacements
    
    def _apply_replacements(self, replacements: List) -> None:
        """Apply replacements in reverse order."""
        replacements.sort(key=lambda x: x[0].start_byte, reverse=True)
        for node, constant_name in replacements:
            self.transformer.add_change(
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                new_text=constant_name
            )
    
    def _add_python_constants(self, constants_to_add: List) -> None:
        """Add constants at module level for Python."""
        lines = self.source_text.split('\n')
        insert_position = 0
        
        # Find end of imports
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('import') and not stripped.startswith('from'):
                insert_position = sum(len(l) + 1 for l in lines[:i])
                break
        
        constants_text = '\n'.join(f"{name} = {value}" for name, value in constants_to_add)
        constants_text += '\n\n'
        
        self.transformer.add_change(
            start_byte=insert_position,
            end_byte=insert_position,
            new_text=constants_text
        )
        print(f"  [ADD] Added {len(constants_to_add)} constant(s) at module level")
    
    def _add_javascript_constants(self, constants_to_add: List) -> None:
        """Add constants at module level for JavaScript."""
        lines = self.source_text.split('\n')
        insert_position = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('//') and not stripped.startswith('import') and not stripped.startswith('const '):
                insert_position = sum(len(l) + 1 for l in lines[:i])
                break
        
        constants_text = '\n'.join(f"const {name} = {value};" for name, value in constants_to_add)
        constants_text += '\n\n'
        
        self.transformer.add_change(
            start_byte=insert_position,
            end_byte=insert_position,
            new_text=constants_text
        )
        print(f"  [ADD] Added {len(constants_to_add)} constant(s) at module level")
    
    def _add_java_constants(self, constants_to_add: List) -> None:
        """Add constants at class level for Java."""
        lines = self.source_text.split('\n')
        insert_position = 0
        
        # Find first line inside class
        for i, line in enumerate(lines):
            if '{' in line and ('class ' in lines[max(0, i-1)] or 'class ' in line):
                insert_position = sum(len(l) + 1 for l in lines[:i+1])
                break
        
        constants_text = '\n    ' + '\n    '.join(
            f"private static final {self._infer_java_type(value)} {name} = {value};"
            for name, value in constants_to_add
        )
        constants_text += '\n'
        
        self.transformer.add_change(
            start_byte=insert_position,
            end_byte=insert_position,
            new_text=constants_text
        )
        print(f"  [ADD] Added {len(constants_to_add)} constant(s) at class level")
    
    def _add_go_constants(self, constants_to_add: List) -> None:
        """Add constants at package level for Go."""
        lines = self.source_text.split('\n')
        insert_position = 0
        
        for i, line in enumerate(lines):
            s = line.strip()
            if s and not (s.startswith('package ') or s.startswith('import ') or s.startswith('//')):
                insert_position = sum(len(l) + 1 for l in lines[:i])
                break
        
        constants_text = '\n'.join(f"const {name} = {value}" for name, value in constants_to_add)
        constants_text += '\n\n'
        
        self.transformer.add_change(
            start_byte=insert_position,
            end_byte=insert_position,
            new_text=constants_text
        )
        print(f"  [ADD] Added {len(constants_to_add)} constant(s) at package level")
    
    def _add_cpp_constants(self, constants_to_add: List) -> None:
        """Add constants at file scope for C++."""
        lines = self.source_text.split('\n')
        insert_position = 0
        
        for i, line in enumerate(lines):
            s = line.strip()
            if s and not s.startswith('#include') and not s.startswith('//') and not s.startswith('using'):
                insert_position = sum(len(l) + 1 for l in lines[:i])
                break
        
        constants_text = '\n'.join(
            f"constexpr {self._infer_cpp_type(value)} {name} = {value};"
            for name, value in constants_to_add
        )
        constants_text += '\n\n'
        
        self.transformer.add_change(
            start_byte=insert_position,
            end_byte=insert_position,
            new_text=constants_text
        )
        print(f"  [ADD] Added {len(constants_to_add)} constant(s) at file scope")
    
    def _infer_java_type(self, value: str) -> str:
        """Infer Java type from value."""
        if '.' in value:
            return 'double'
        return 'int'
    
    def _infer_cpp_type(self, value: str) -> str:
        """Infer C++ type from value."""
        if '.' in value:
            return 'double'
        return 'int'
