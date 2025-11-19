"""
Docstring generation processor.
Handles generating and improving docstrings for all supported languages.
"""

import textwrap
from typing import Set, Any, Optional, Dict
from .base import BaseProcessor
from ..formatters import FormatterFactory


def indent(text: str, prefix: str) -> str:
    """Add prefix to each line in text."""
    lines = text.split('\n')
    return '\n'.join(prefix + line if line.strip() else '' for line in lines)


class DocstringProcessor(BaseProcessor):
    """Generates docstrings for undocumented functions, skipping dead code."""
    
    def process(self, generator: Any, overwrite_existing: bool = False, 
                dead_functions: Optional[Set[str]] = None, check_drift: bool = False) -> None:
        """
        Generate docstrings for functions, skipping dead code.
        
        Args:
            generator: Docstring generator instance
            overwrite_existing: Whether to improve existing docstrings
            dead_functions: Set of dead function names to skip
            check_drift: Whether to check for docstring drift
        """
        dead_functions = dead_functions or set()
        
        # Get all functions
        all_functions = self.get_function_nodes()
        
        # Find documented functions
        documented_functions = set()
        documented_nodes = {}
        
        for func_node in all_functions:
            body_node = func_node.child_by_field_name("body")
            if body_node and body_node.children:
                first_stmt = body_node.children[0]
                if first_stmt.type == 'expression_statement':
                    expr = first_stmt.children[0] if first_stmt.children else None
                    if expr and expr.type == 'string':
                        documented_functions.add(func_node)
                        documented_nodes[func_node] = expr
        
        undocumented_functions = all_functions - documented_functions
        
        # Process undocumented functions, skipping dead code
        processed_count = 0
        skipped_count = 0
        
        for func_node in undocumented_functions:
            func_name = self.get_function_name(func_node)
            
            # Skip dead functions!
            if func_name and func_name in dead_functions:
                skipped_count += 1
                continue
            
            if func_name:
                self._generate_docstring_for_function(func_node, func_name, generator)
                processed_count += 1
        
        # Process existing docstrings if overwrite is enabled OR drift check is enabled
        if overwrite_existing or check_drift:
            improved_count = self._improve_existing_docstrings(
                documented_nodes, generator, dead_functions, 
                check_drift=check_drift,
                overwrite_existing=overwrite_existing
            )
            if improved_count > 0:
                print(f"  [DOC] Improved/Fixed {improved_count} existing docstring(s)")
        
        if skipped_count > 0:
            print(f"  [DOC] Processed {processed_count} functions, skipped {skipped_count} dead functions")
    
    def _generate_docstring_for_function(self, func_node: Any, func_name: str, generator: Any) -> None:
        """Generate and insert docstring for a single function."""
        name_node = func_node.child_by_field_name('name')
        if not name_node:
            # For C++, check declarator
            declarator = func_node.child_by_field_name('declarator')
            if declarator:
                for child in declarator.children:
                    if child.type == 'identifier':
                        name_node = child
                        break
        
        if not name_node:
            return
        
        line_num = name_node.start_point[0] + 1
        print(f"  [DOC] Line {line_num}: Generating docstring for `{func_name}()`", flush=True)
        
        docstring = generator.generate(func_node)
        
        # Insert docstring based on language
        if self.lang == 'python':
            self._insert_python_docstring(func_node, docstring)
        else:
            self._insert_other_language_docstring(func_node, docstring)
    
    def _insert_python_docstring(self, func_node: Any, docstring: str) -> None:
        """Insert docstring for Python function."""
        body_node = func_node.child_by_field_name("body")
        if not body_node or not body_node.children:
            return
        
        try:
            # Calculate indentation
            func_start_line = func_node.start_point[0]
            func_line = self.source_text.split('\n')[func_start_line]
            func_def_indent = len(func_line) - len(func_line.lstrip())
            body_indent_level = func_def_indent + 4
            indentation_str = ' ' * body_indent_level
            first_child = body_node.children[0]
            
            # Clean and format docstring
            docstring_content_raw = docstring.strip()
            dedented_content = textwrap.dedent(docstring_content_raw).strip()
            indented_content = indent(dedented_content, indentation_str)
            
            formatter = FormatterFactory.create_formatter(self.lang)
            formatted_docstring = formatter.format(docstring, indentation_str)
            
            # Check if first child is already a docstring
            is_docstring = (first_child.type == 'expression_statement' and 
                           first_child.children and 
                           first_child.children[0].type == 'string')
            
            if is_docstring:
                # Replace existing docstring
                first_stmt_line_num = first_child.start_point[0]
                lines = self.source_text.split('\n')
                line_start_byte = sum(len(line) + 1 for line in lines[:first_stmt_line_num])
                
                insertion_point = line_start_byte
                end_point = first_child.end_byte
                formatted_docstring = formatted_docstring.rstrip() + '\n' + indentation_str
                self.transformer.add_change(
                    start_byte=insertion_point,
                    end_byte=end_point,
                    new_text=formatted_docstring
                )
            else:
                # Insert before first statement
                first_stmt_line_num = first_child.start_point[0]
                lines = self.source_text.split('\n')
                line_start_byte = sum(len(line) + 1 for line in lines[:first_stmt_line_num])
                
                insertion_point = line_start_byte
                end_point = first_child.start_byte
                formatted_docstring = formatted_docstring + indentation_str
                
                self.transformer.add_change(
                    start_byte=insertion_point,
                    end_byte=end_point,
                    new_text=formatted_docstring
                )
        except Exception as e:
            print(f"  [ERROR] Docstring insertion failed: {e}", flush=True)
    
    def _insert_other_language_docstring(self, func_node: Any, docstring: str) -> None:
        """Insert docstring for Java/JavaScript/C++/Go (before function)."""
        func_start_line = func_node.start_point[0]
        func_line = self.source_text.split('\n')[func_start_line]
        func_def_indent = len(func_line) - len(func_line.lstrip())
        indentation_str = ' ' * func_def_indent
        
        formatter = FormatterFactory.create_formatter(self.lang)
        formatted_docstring = formatter.format(docstring, indentation_str)
        
        # Find start of line
        lines = self.source_text.split('\n')
        line_start_byte = sum(len(line) + 1 for line in lines[:func_start_line])
        
        # Insert before function
        self.transformer.add_change(
            start_byte=line_start_byte,
            end_byte=line_start_byte,
            new_text=formatted_docstring
        )
    
    def _check_drift(self, func_node: Any, docstring: str) -> bool:
        """
        Check if docstring has drifted from code (heuristic check).
        Returns True if drift is detected.
        """
        import re
        
        # 1. Extract parameters from code
        code_params = set()
        params_node = func_node.child_by_field_name('parameters')
        if params_node:
            for child in params_node.children:
                if child.type in ('identifier', 'typed_parameter', 'default_parameter', 'typed_default_parameter'):
                    # Extract name based on node type
                    if child.type == 'identifier':
                        code_params.add(child.text.decode('utf8'))
                    elif child.type == 'typed_parameter':
                        name_node = child.child_by_field_name('name') or child.children[0]
                        code_params.add(name_node.text.decode('utf8'))
                    elif child.type == 'default_parameter':
                        name_node = child.child_by_field_name('name') or child.children[0]
                        code_params.add(name_node.text.decode('utf8'))
                    elif child.type == 'typed_default_parameter':
                        name_node = child.child_by_field_name('name') or child.children[0]
                        code_params.add(name_node.text.decode('utf8'))
        
        # Remove 'self' or 'cls' for methods
        code_params.discard('self')
        code_params.discard('cls')
        
        # 2. Extract parameters from docstring (Heuristic)
        doc_params = set()
        
        # Google Style: Args: \n param (type): desc
        google_matches = re.findall(r'^\s*(\w+)\s*\(.*?\):\s', docstring, re.MULTILINE)
        doc_params.update(google_matches)
        
        # NumPy Style: param : type
        # We need to be careful not to match section headers like 'Args:', 'Parameters:', etc.
        # A simple heuristic: section headers usually don't have a type definition on the same line in NumPy style,
        # OR they are one of the standard headers.
        
        numpy_potential = re.findall(r'^\s*(\w+)\s*:\s', docstring, re.MULTILINE)
        ignore_headers = {'Args', 'Arguments', 'Parameters', 'Returns', 'Yields', 'Raises', 'Attributes', 'Example', 'Examples', 'Note', 'Notes', 'Todo'}
        
        for match in numpy_potential:
            if match not in ignore_headers:
                doc_params.add(match)
        
        # Sphinx/Epytext: :param name: desc or @param name: desc
        sphinx_matches = re.findall(r'[:@]param\s+(\w+)', docstring)
        doc_params.update(sphinx_matches)
        
        # 3. Compare
        # If docstring has no params but code does, it might just be a summary docstring (acceptable?)
        # Let's be strict: if docstring mentions ANY params, it must match code params.
        if not doc_params and code_params:
            # If code has params but docstring mentions none, it's a weak signal (could be summary only).
            # But if we want "Smart" drift detection, we might flag this if it's a long function.
            # For now, let's only flag if there is an INTERSECTION mismatch (documented params don't match code params)
            return False
            
        if doc_params:
            # Check for missing params in docstring
            missing_in_doc = code_params - doc_params
            # Check for extra params in docstring (deleted from code)
            extra_in_doc = doc_params - code_params
            
            if missing_in_doc or extra_in_doc:
                print(f"  [DRIFT] Parameter mismatch for function.")
                if missing_in_doc:
                    print(f"    - Missing in doc: {', '.join(missing_in_doc)}")
                if extra_in_doc:
                    print(f"    - Extra in doc: {', '.join(extra_in_doc)}")
                return True
                
        return False

    def _improve_existing_docstrings(self, documented_nodes: Dict[Any, Any], 
                                    generator: Any, dead_functions: Set[str],
                                    check_drift: bool = False,
                                    overwrite_existing: bool = False) -> int:
        """Improve existing docstrings that are low quality or drifted."""
        improved_count = 0
        
        for func_node, doc_node in documented_nodes.items():
            func_name = self.get_function_name(func_node)
            
            # Skip dead functions
            if func_name and func_name in dead_functions:
                continue
            
            docstring_text = doc_node.text.decode('utf8')
            
            # Check for drift if requested
            is_drifted = False
            if check_drift:
                is_drifted = self._check_drift(func_node, docstring_text)
                if is_drifted:
                    print(f"  [DRIFT] Line {doc_node.start_point[0]+1}: Detected drift for `{func_name}()`")
            
            # If drifted, we force regeneration. If not, we check quality ONLY if overwrite is enabled.
            should_regenerate = is_drifted
            
            if not should_regenerate and overwrite_existing:
                is_good = generator.evaluate(func_node, docstring_text)
                if not is_good:
                    print(f"  [IMPROVE] Line {doc_node.start_point[0]+1}: Improving docstring for `{func_name}()` (low quality detected)")
                    should_regenerate = True
            
            if should_regenerate:
                new_docstring = generator.generate(func_node)
                
                try:
                    func_line = self.source_text.split('\n')[func_node.start_point[0]]
                    func_def_indent = len(func_line) - len(func_line.lstrip())
                    body_indent_level = func_def_indent + 4
                    indentation_str = ' ' * body_indent_level
                    
                    formatter = FormatterFactory.create_formatter(self.lang)
                    formatted_docstring = formatter.format(new_docstring, indentation_str).strip()
                    
                    self.transformer.add_change(
                        start_byte=doc_node.start_byte,
                        end_byte=doc_node.end_byte,
                        new_text=formatted_docstring
                    )
                    improved_count += 1
                except Exception as e:
                    print(f"  [ERROR] Improving docstring failed: {e}", flush=True)
        
        return improved_count
