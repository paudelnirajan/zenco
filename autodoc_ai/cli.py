import argparse
import sys
import os
from textwrap import indent
import traceback
from textwrap import indent
from tree_sitter import QueryCursor
from .generators import GeneratorFactory, IDocstringGenerator
from .utils import get_source_files, get_git_changed_files
from .config import load_config
from .parser import get_language_parser, get_language_queries
from .transformers import CodeTransformer
import textwrap
from .formatters import FormatterFactory

def init_config():
    """
    Guides the user through creating or updating a .env file for API keys.
    This function is safe and will not destroy existing .env content.
    """
    print("--- AutoDoc AI Initial Configuration ---")
    
    env_path = ".env"
    
    api_key = input("Please enter your Groq API key (leave blank to skip): ").strip()
    model_name = input("Enter the model name to use (default: llama-3.3-70b-versatile): ").strip() or "llama-3.3-70b-versatile"

    keys_to_update = {}
    if api_key:
        keys_to_update["GROQ_API_KEY"] = api_key
    if model_name:
        keys_to_update["GROQ_MODEL_NAME"] = model_name

    if not keys_to_update:
        print("No new values provided. Configuration cancelled.")
        return

    if os.path.exists(env_path):
        print(f"Updating existing '{env_path}' file...")
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        # Update existing keys
        for i, line in enumerate(lines):
            for key, value in list(keys_to_update.items()):
                if line.strip().startswith(f"{key}="):
                    lines[i] = f'{key}="{value}"\n'
                    print(f"  - Updated {key}")
                    del keys_to_update[key] 
        
        for key, value in keys_to_update.items():
            lines.append(f'{key}="{value}"\n')
            print(f"  - Added {key}")

        with open(env_path, "w") as f:
            f.writelines(lines)

    else:
        print(f"Creating new '{env_path}' file...")
        with open(env_path, "w") as f:
            for key, value in keys_to_update.items():
                f.write(f'{key}="{value}"\n')
    
    print(f"\nConfiguration saved to '{env_path}'.")


def process_file_with_treesitter(filepath: str, generator: IDocstringGenerator, in_place: bool, overwrite_existing: bool):
    """
    Processes a single file using the Tree-sitter engine to find and
    report undocumented functions.
    """
    print(f"--- Processing {filepath} ---")

    lang = None
    if filepath.endswith('.py'): lang = 'python'
    elif filepath.endswith('.js'): lang = 'javascript'
    elif filepath.endswith('.java'): lang = 'java'
    elif filepath.endswith('.go'): lang = 'go'
    elif filepath.endswith('.cpp') or filepath.endswith('.hpp') or filepath.endswith('.h'): lang = 'cpp'

    parser = get_language_parser(lang)
    if not parser: return

    try:
        with open(filepath, 'rb') as f:
            source_bytes = f.read()
    except IOError as e:
        print(f"Error reading file: {e}"); return

    tree = parser.parse(source_bytes)
    transformer = CodeTransformer(source_bytes)
    queries = get_language_queries(lang)

    all_func_query = queries.get("all_functions")
    documented_funcs_query = queries.get("documented_function")

    if not all_func_query or not documented_funcs_query:
        print(f"Warning: Queries for `{lang}` not fully defined. Skipping.")
        return

    # Use QueryCursor to execute queries (tree-sitter 0.25 API)
    # QueryCursor requires the query in the constructor
    all_func_cursor = QueryCursor(all_func_query)
    documented_func_cursor = QueryCursor(documented_funcs_query)
    
    # Get all functions (matches returns (pattern_index, {capture_name: [nodes]}) tuples)
    all_functions = set()
    for _, captures in all_func_cursor.matches(tree.root_node):
        for node in captures.get('func', []):
            all_functions.add(node)
    
    documented_nodes = {}
    for _, captures in documented_func_cursor.matches(tree.root_node):
        func_nodes = captures.get('func', [])
        doc_nodes = captures.get('docstring', [])
        for i, func_node in enumerate(func_nodes):
            if i < len(doc_nodes):
                documented_nodes[func_node] = doc_nodes[i]
    
    documented_funtions = set(documented_nodes.keys())
    
    # Also manually check for docstrings as a fallback (in case query doesn't match)
    # A function has a docstring if its first statement is a string literal
    for func_node in all_functions:
        body_node = func_node.child_by_field_name("body")
        if body_node and body_node.children:
            first_stmt = body_node.children[0]
            # Check if first statement is an expression statement with a string
            if first_stmt.type == 'expression_statement':
                expr = first_stmt.children[0] if first_stmt.children else None
                if expr and expr.type == 'string':
                    documented_funtions.add(func_node)
                    documented_nodes[func_node] = expr

    undocumented_functions = all_functions - documented_funtions

    for func_node in undocumented_functions:
        # Get function name - different field names for different languages
        name_node = func_node.child_by_field_name('name')  # Python, Java, JS
        if not name_node:
            # For C++, the name is in declarator -> identifier
            declarator = func_node.child_by_field_name('declarator')
            if declarator:
                for child in declarator.children:
                    if child.type == 'identifier':
                        name_node = child
                        break
        
        if name_node:
            func_name = name_node.text.decode('utf8')
            line_num = name_node.start_point[0] + 1
            print(f"L{line_num}:[Docstring] Generating for function `{func_name}`.", flush=True)
            
            docstring = generator.generate(func_node)
            
            # Handle docstring insertion based on language
            # For Python: insert inside the function body
            # For Java/JS/C++: insert before the function declaration
            if lang == 'python':
                body_node = func_node.child_by_field_name("body")
                if body_node and body_node.children:
                    try:
                        # Get the function definition's indentation by reading the source line
                        # This is more reliable than using tree-sitter's start_point
                        source_text = source_bytes.decode('utf8')
                        func_start_line = func_node.start_point[0]
                        func_line = source_text.split('\n')[func_start_line]
                        func_def_indent = len(func_line) - len(func_line.lstrip())
                        
                        # Standard Python indentation is 4 spaces from the function definition
                        # We'll use this consistently to avoid issues with malformed code
                        body_indent_level = func_def_indent + 4
                        indentation_str = ' ' * body_indent_level
                        first_child = body_node.children[0]
                    except Exception as e:
                        print(f"  ERROR in indentation calculation: {e}", flush=True)
                        import traceback
                        traceback.print_exc()
                        continue

                    # Clean the raw docstring from the LLM (remove any existing indentation)
                    docstring_content_raw = docstring.strip()
                    
                    # Use textwrap.dedent to remove common leading whitespace
                    # This handles cases where the LLM returns pre-indented content
                    dedented_content = textwrap.dedent(docstring_content_raw).strip()
                    
                    # Re-indent the cleaned content to match the function's body indentation
                    # indent() adds the prefix to each line, including empty lines
                    indented_content = indent(dedented_content, indentation_str)

                    formatter = FormatterFactory.create_formatter(lang)
                    formatted_docstring = formatter.format(docstring, indentation_str)

                    # Check if first_child is already a docstring
                    is_docstring = (first_child.type == 'expression_statement' and 
                                   first_child.children and 
                                   first_child.children[0].type == 'string')
                    
                    if is_docstring:
                        # Replace the existing docstring
                        # Find the start of the line to replace any incorrect indentation
                        first_stmt_line_num = first_child.start_point[0]
                        lines = source_text.split('\n')
                        line_start_byte = sum(len(line) + 1 for line in lines[:first_stmt_line_num])
                        
                        insertion_point = line_start_byte
                        end_point = first_child.end_byte
                        formatted_docstring = formatted_docstring.rstrip() + '\n' + indentation_str
                        transformer.add_change(
                            start_byte=insertion_point,
                            end_byte=end_point,
                            new_text=formatted_docstring
                        )
                    else:
                        # Insert before the first statement
                        # We need to find the actual start of the line and replace any incorrect indentation
                        # first_child.start_point gives us (line, column)
                        first_stmt_line_num = first_child.start_point[0]
                        first_stmt_col = first_child.start_point[1]
                        
                        # Find the start of this line in the source
                        lines = source_text.split('\n')
                        line_start_byte = sum(len(line) + 1 for line in lines[:first_stmt_line_num])  # +1 for \n
                        
                        # The insertion point is at the start of the line
                        # We'll replace from line start to the actual statement start
                        # This removes any incorrect indentation
                        insertion_point = line_start_byte
                        end_point = first_child.start_byte
                        
                        # Add proper indentation before the statement
                        formatted_docstring = formatted_docstring + indentation_str
                        
                        transformer.add_change(
                            start_byte=insertion_point,
                            end_byte=end_point,
                            new_text=formatted_docstring
                        )
            else:
                # For Java, JavaScript, C++, Go: insert docstring before the function declaration
                source_text = source_bytes.decode('utf8')
                func_start_line = func_node.start_point[0]
                func_line = source_text.split('\n')[func_start_line]
                func_def_indent = len(func_line) - len(func_line.lstrip())
                indentation_str = ' ' * func_def_indent
                
                formatter = FormatterFactory.create_formatter(lang)
                formatted_docstring = formatter.format(docstring, indentation_str)
                
                # Find the start of the line where the function declaration begins
                lines = source_text.split('\n')
                line_start_byte = sum(len(line) + 1 for line in lines[:func_start_line])
                
                # Insert the docstring before the function declaration
                transformer.add_change(
                    start_byte=line_start_byte,
                    end_byte=line_start_byte,
                    new_text=formatted_docstring
                )

    # If overwrite is enabled, process functions that already have docstrings
    if overwrite_existing:
        for func_node, doc_node in documented_nodes.items():
            docstring_text = doc_node.text.decode('utf8')
            
            is_good = generator.evaluate(func_node, docstring_text)
            
            if not is_good:
                name_node = func_node.child_by_field_name('name')
                func_name = name_node.text.decode('utf8') if name_node else 'unknown'
                print(f"L{doc_node.start_point[0]+1}:[Refactor] Regenerating poor-quality docstring for `{func_name}`.")

                new_docstring = generator.generate(func_node)
                
                try:
                    source_text = source_bytes.decode('utf8')
                    func_line = source_text.split('\n')[func_node.start_point[0]]
                    func_def_indent = len(func_line) - len(func_line.lstrip())
                    body_indent_level = func_def_indent + 4
                    indentation_str = ' ' * body_indent_level
                    
                    formatter = FormatterFactory.create_formatter(lang)
                    formatted_docstring = formatter.format(new_docstring, indentation_str).strip()

                    transformer.add_change(
                        start_byte=doc_node.start_byte,
                        end_byte=doc_node.end_byte,
                        new_text=formatted_docstring
                    )
                except Exception as e:
                    print(f"  ERROR processing documented function: {e}", flush=True)
                    continue

    new_code = transformer.apply_changes()
    if in_place:
        if new_code != source_bytes:
            print("  - Writing changes to file.")
            try:
                with open(filepath, 'wb') as f:
                    f.write(new_code)
            except IOError as e:
                print(f"Error writing to file: {e}")
        else:
            print("  - No changes to apply.")
    else:
        # Print to console if not in_place
        print("\n--- Generated Code (Dry Run) ---\n")
        print(new_code.decode('utf8'))


def run_autodoc(args):
    """The main entry point for running the analysis."""
    if args.diff:
        print("Processing files with git changes...")
        source_files = get_git_changed_files()
        if source_files is None: sys.exit(1)
    else:
        source_files = get_source_files(args.path)
    
    if not source_files:
        print("No source files found to process."); return

    print(f"Found {len(source_files)} file(s) to process.")
    
    try:
        generator = GeneratorFactory.create_generator(args.strategy, args.style)
    except ValueError as e:
        print(f"Error: {e}"); sys.exit(1)

    for filepath in source_files:
        process_file_with_treesitter(filepath=filepath, generator=generator,
        in_place=args.in_place,
        overwrite_existing=args.overwrite_existing,
        )
        print("-" * 50)


def main():
    """Main CLI entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        description="AutoDoc AI: A polyglot AI-powered code tool.",
        epilog="For detailed help on a command, run: 'autodoc <command> --help'"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    parser_init = subparsers.add_parser("init", help="Initialize AutoDoc configuration.")
    parser_init.set_defaults(func=lambda args: init_config())

    config = load_config()
    parser_run = subparsers.add_parser("run", help="Analyze and process source code files.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser_run.add_argument("path", nargs='?', default='.', help="Path to process.")
    parser_run.add_argument("--diff", action="store_true", help="Only process git-changed files.")
    parser_run.add_argument("--strategy", choices=["mock", "groq"], default=config.get('strategy', 'mock'))
    parser_run.add_argument("--style", choices=["google", "numpy", "rst"], default=config.get('style', 'google'))
    parser_run.add_argument("--in-place", action="store_true")
    parser_run.add_argument("--overwrite-existing", action="store_true")
    parser_run.add_argument("--refactor", action="store_true")

    parser_run.set_defaults(func=run_autodoc)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()