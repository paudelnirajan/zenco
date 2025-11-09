from tree_sitter import Parser, Query, Language
from typing import Optional
from tree_sitter_python import language as python_language
from tree_sitter_javascript import language as javascript_language
from tree_sitter_java import language as java_language
from tree_sitter_go import language as go_language
from tree_sitter_cpp import language as cpp_language

LANGUAGES = {
   "python": Language(python_language()),
   "javascript": Language(javascript_language()),
   "java": Language(java_language()),
   "go": Language(go_language()),
   "cpp": Language(cpp_language()),
}

def get_language_parser(language_name: str) -> Optional[Parser]:
    """Returns a pre-configured Tree-sitter parser for a given language."""
    language = LANGUAGES.get(language_name)
    if not language:
        print(f"Error: Grammar for '{language_name}' not found.")
        print(f"Please make sure you have run 'pip install tree-sitter-{language_name}'.")
        return None
    
    parser = Parser(language)
    return parser

def get_language_queries(language_name: str) -> dict:
    """Returns a dictionary of Tree-sitter queries for a given language."""
    language = LANGUAGES.get(language_name)
    if not language:
        return {}

    if language_name == 'python':
        return {
            "all_functions": "(function_definition) @func",
            "documented_function": """
                (function_definition
                  body: (block (expression_statement (string) @docstring))
                ) @func
                """,
            "functions_with_type_hints": """
                (function_definition
                  return_type: (_)
                ) @func
                """,
            "numeric_literals": """
                [
                  (integer) @number
                  (float) @number
                ]
                """
        }
    if language_name == 'javascript':
        return {
            "all_functions": "(function_declaration) @func",
            "documented_function": """
                (
                  (comment) @docstring
                  .
                  (function_declaration) @func
                )
                (#match? @docstring "^/\\\\*\\\\*")
                """,
            "numeric_literals": "(number) @number"
        }

    if language_name == 'java':
        return {
            "all_functions": "(method_declaration) @func",
            "documented_function": """
                (
                    (block_comment)+ @docstring
                    .
                    (method_declaration) @func
                )
                """,
            "numeric_literals": """
                [
                  (decimal_integer_literal) @number
                  (decimal_floating_point_literal) @number
                  (hex_integer_literal) @number
                  (octal_integer_literal) @number
                  (binary_integer_literal) @number
                ]
                """
        }

    if language_name == 'go':
        return {
            "all_functions": "(function_declaration) @func",
            "documented_function": """
                (
                  (comment) @doc_comment
                  .
                  (function_declaration) @func
                )
                """,
            "numeric_literals": """
                [
                  (int_lit) @number
                  (float_lit) @number
                ]
                """
        }

    if language_name == 'cpp':
        return {
            "all_functions": "(function_definition) @func",
            "documented_function": """
                (
                  (comment) @docstring
                  .
                  (function_definition) @func
                )
                """,
            "numeric_literals": "(number_literal) @number"
        }
        
    return {}