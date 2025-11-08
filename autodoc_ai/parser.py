from tree_sitter import Parser, Query, Language
from tree_sitter_python import language as python_language
from tree_sitter_javascript import language as javascript_language

LANGUAGES = {
   "python": Language(python_language()),
   "javascript": Language(javascript_language()),
}

def get_language_parser(language_name: str) -> Parser | None:
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
            "all_functions": Query(
                language,
                "(function_definition) @func"
            ),
            "documented_function": Query(
                language,
                """
                (function_definition
                  body: (block (expression_statement (string) @docstring))
                ) @func
                """
            ),
        }
    if language_name == 'javascript':
        return {
            "all_functions": Query(
                language,
                "(function_declaration) @func"
            ),
            "documented_function": Query(
                language,
                """
                (
                  (comment) @doc_comment
                  .
                  (function_declaration) @func
                )
                (#match? @doc_comment "^/\\\\*\\\\*")
                """
            ),
        }
    return {}