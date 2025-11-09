import argparse
import sys
import os
from textwrap import indent
import traceback
from textwrap import indent
from tree_sitter import Language, Query
from .generators import GeneratorFactory, IDocstringGenerator
from .utils import get_source_files, get_git_changed_files
from .config import load_config
from .parser import get_language_parser, get_language_queries, LANGUAGES
from .transformers import CodeTransformer
import textwrap
from .formatters import FormatterFactory

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    rprint = print

try:
    import colorama
    colorama.init()
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

def cprint(text, color=None, style=None):
    """Colorful print with fallback to regular print"""
    if RICH_AVAILABLE:
        if color or style:
            rprint(f"[{color or ''} {style or ''}]{text}[/]")
        else:
            rprint(text)
    elif COLORAMA_AVAILABLE and color:
        colors = {
            'red': colorama.Fore.RED,
            'green': colorama.Fore.GREEN,
            'blue': colorama.Fore.BLUE,
            'yellow': colorama.Fore.YELLOW,
            'magenta': colorama.Fore.MAGENTA,
            'cyan': colorama.Fore.CYAN,
            'white': colorama.Fore.WHITE,
        }
        print(f"{colors.get(color, '')}{text}{colorama.Style.RESET_ALL}")
    else:
        print(text)

def init_config():
    """
    Guides the user through creating or updating a .env file for API keys.
    Supports multiple LLM providers interactively.
    """
    print("\n" + "="*70)
    print("  🚀 AutoDoc AI - Initial Configuration Wizard")
    print("="*70)
    print("\nThis wizard will help you set up your preferred AI provider.")
    print("Your API key will be stored securely in a local .env file.\n")
    
    print("📋 Supported LLM Providers:")
    print("  1. Groq        - Fast inference, generous free tier")
    print("  2. OpenAI      - GPT-4, GPT-4o-mini (requires paid account)")
    print("  3. Anthropic   - Claude 3.5 Sonnet (requires paid account)")
    print("  4. Google      - Gemini Pro/Flash (free tier available)")
    
    provider_choice = input("\n👉 Select your LLM provider (1-4) [default: 1]: ").strip() or "1"
    
    provider_map = {
        "1": ("groq", "GROQ_API_KEY", "GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
        "2": ("openai", "OPENAI_API_KEY", "OPENAI_MODEL_NAME", "gpt-4o-mini"),
        "3": ("anthropic", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL_NAME", "claude-3-5-sonnet-latest"),
        "4": ("gemini", "GEMINI_API_KEY", "GEMINI_MODEL_NAME", "gemini-1.5-pro"),
    }
    
    if provider_choice not in provider_map:
        print("Invalid choice. Defaulting to Groq.")
        provider_choice = "1"
    
    provider_name, api_key_var, model_var, default_model = provider_map[provider_choice]
    
    print(f"\n{'─'*70}")
    print(f"📝 Configuring {provider_name.upper()}")
    print(f"{'─'*70}")
    
    # Provider-specific instructions
    if provider_name == "groq":
        print("ℹ️  Get your free API key at: https://console.groq.com/keys")
    elif provider_name == "openai":
        print("ℹ️  Get your API key at: https://platform.openai.com/api-keys")
    elif provider_name == "anthropic":
        print("ℹ️  Get your API key at: https://console.anthropic.com/")
    elif provider_name == "gemini":
        print("ℹ️  Get your API key at: https://aistudio.google.com/app/apikey")
    
    api_key = input(f"\n🔑 Enter your {provider_name.upper()} API key: ").strip()
    
    if not api_key:
        print("\n[ERROR] API key is required. Configuration cancelled.")
        return
    
    model_name = input(f"🤖 Enter model name [default: {default_model}]: ").strip() or default_model
    
    keys_to_update = {
        api_key_var: api_key,
        model_var: model_name,
        "AUTODOC_PROVIDER": provider_name,  # Store the selected provider
    }
    
    env_path = ".env"
    
    if os.path.exists(env_path):
        print(f"\n📝 Updating existing '{env_path}' file...")
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        # Update existing keys
        updated_keys = set()
        for i, line in enumerate(lines):
            for key, value in keys_to_update.items():
                if line.strip().startswith(f"{key}="):
                    lines[i] = f'{key}="{value}"\n'
                    print(f"  ✓ Updated {key}")
                    updated_keys.add(key)
        
        # Add new keys that weren't found
        for key, value in keys_to_update.items():
            if key not in updated_keys:
                lines.append(f'{key}="{value}"\n')
                print(f"  ✓ Added {key}")
        
        with open(env_path, "w") as f:
            f.writelines(lines)
    else:
        print(f"\n📝 Creating new '{env_path}' file...")
        with open(env_path, "w") as f:
            for key, value in keys_to_update.items():
                f.write(f'{key}="{value}"\n')
                print(f"  ✓ Added {key}")
    
    print(f"\n{'='*70}")
    print(f"  [OK] Configuration Complete!")
    print(f"{'='*70}")
    print(f"\n📊 Your Settings:")
    print(f"  • Provider: {provider_name.upper()}")
    print(f"  • Model: {model_name}")
    print(f"  • Config file: {env_path}")
    
    print(f"\n🚀 Next Steps:")
    print(f"  1. Test your setup:")
    print(f"     autodoc run examples/test.py")
    print(f"\n  2. Add type hints to your code:")
    print(f"     autodoc run . --add-type-hints --in-place")
    print(f"\n  3. Generate docstrings:")
    print(f"     autodoc run src/ --in-place")
    
    print(f"\n💡 Tips:")
    print(f"  • Use --help to see all available options")
    print(f"  • Change providers anytime: autodoc run --provider <name>")
    print(f"  • Run 'autodoc init' again to reconfigure")
    print(f"\n{'='*70}\n")


def process_file_with_treesitter(filepath: str, generator: IDocstringGenerator, in_place: bool, overwrite_existing: bool, add_type_hints: bool = False, fix_magic_numbers: bool = False, docstrings_enabled: bool = False, dead_code: bool = False, dead_code_strict: bool = False):
    """
    Processes a single file using the Tree-sitter engine to find and
    report undocumented functions, add type hints, and fix magic numbers.
    """

    lang = None
    if filepath.endswith('.py'): lang = 'python'
    elif filepath.endswith('.js'): lang = 'javascript'
    elif filepath.endswith('.java'): lang = 'java'
    elif filepath.endswith('.go'): lang = 'go'
    elif filepath.endswith('.cpp') or filepath.endswith('.hpp') or filepath.endswith('.h'): lang = 'cpp'

    parser = get_language_parser(lang)
    if not parser: return
    
    # Get the language object for Query constructor
    language = LANGUAGES.get(lang)
    if not language: return

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

    # Use Query API to execute queries
    all_func_query_obj = Query(language, all_func_query)
    documented_func_query_obj = Query(language, documented_funcs_query)
    
    # Get all functions (matches returns (pattern_index, {capture_name: [nodes]}) tuples)
    all_functions = set()
    for _, captures in all_func_query_obj.matches(tree.root_node):
        for node in captures.get('func', []):
            all_functions.add(node)
    
    documented_nodes = {}
    for _, captures in documented_func_query_obj.matches(tree.root_node):
        func_nodes = captures.get('func', [])
        doc_nodes = captures.get('docstring', [])
        for i, func_node in enumerate(func_nodes):
            if i < len(doc_nodes):
                documented_nodes[func_node] = doc_nodes[i]
    
    documented_functions = set(documented_nodes.keys())
    
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
                    documented_functions.add(func_node)
                    documented_nodes[func_node] = expr

    undocumented_functions = all_functions - documented_functions

    for func_node in undocumented_functions:
        if not docstrings_enabled:
            break
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
            print(f"  📝 Line {line_num}: Generating docstring for `{func_name}()`", flush=True)
            
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
    if docstrings_enabled and overwrite_existing:
        for func_node, doc_node in documented_nodes.items():
            docstring_text = doc_node.text.decode('utf8')
            
            is_good = generator.evaluate(func_node, docstring_text)
            
            if not is_good:
                name_node = func_node.child_by_field_name('name')
                func_name = name_node.text.decode('utf8') if name_node else 'unknown'
                print(f"  🔄 Line {doc_node.start_point[0]+1}: Improving docstring for `{func_name}()` (low quality detected)")

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

    # Process type hints if enabled (Python only for now)
    if add_type_hints and lang == 'python':
        typed_funcs_query = queries.get("functions_with_type_hints")
        
        # Track which typing imports are needed
        typing_imports_needed = set()
        
        if typed_funcs_query:
            typed_func_query_obj = Query(language, typed_funcs_query)
            functions_with_hints = set()
            
            for _, captures in typed_func_query_obj.matches(tree.root_node):
                for node in captures.get('func', []):
                    functions_with_hints.add(node)
            
            # Find functions without type hints
            functions_without_hints = all_functions - functions_with_hints
            
            for func_node in functions_without_hints:
                name_node = func_node.child_by_field_name('name')
                if not name_node:
                    continue
                
                func_name = name_node.text.decode('utf8')
                
                # Skip special methods like __init__, __str__, etc.
                if func_name.startswith('__') and func_name.endswith('__'):
                    continue
                
                line_num = name_node.start_point[0] + 1
                print(f"  🏷️  Line {line_num}: Adding type hints to `{func_name}()`", flush=True)
                
                try:
                    type_hints = generator.generate_type_hints(func_node)
                    
                    if not type_hints or (not type_hints.get('parameters') and not type_hints.get('return_type')):
                        print(f"     ⚠️  Could not infer types for `{func_name}()`")
                        continue
                    
                    # Build the new function signature with type hints
                    source_text = source_bytes.decode('utf8')
                    
                    # Get the parameters node
                    params_node = func_node.child_by_field_name('parameters')
                    if not params_node:
                        continue
                    
                    # Build new parameter list with type hints
                    new_params = []
                    for param_child in params_node.children:
                        if param_child.type == 'identifier':
                            param_name = param_child.text.decode('utf8')
                            type_hint = type_hints.get('parameters', {}).get(param_name)
                            
                            if type_hint:
                                new_params.append(f"{param_name}: {type_hint}")
                            else:
                                new_params.append(param_name)
                        elif param_child.type in ['(', ')', ',']:
                            # Keep delimiters as-is
                            continue
                        elif param_child.type == 'default_parameter':
                            # Handle parameters with default values
                            param_id = param_child.child_by_field_name('name')
                            param_default = param_child.child_by_field_name('value')
                            
                            if param_id:
                                param_name = param_id.text.decode('utf8')
                                type_hint = type_hints.get('parameters', {}).get(param_name)
                                default_val = param_default.text.decode('utf8') if param_default else ''
                                
                                if type_hint:
                                    new_params.append(f"{param_name}: {type_hint} = {default_val}")
                                else:
                                    new_params.append(f"{param_name} = {default_val}")
                        elif param_child.type == 'typed_parameter':
                            # Already has type hint, keep as-is
                            new_params.append(param_child.text.decode('utf8'))
                        elif param_child.type == 'typed_default_parameter':
                            # Already has type hint with default, keep as-is
                            new_params.append(param_child.text.decode('utf8'))
                    
                    # Build the new function definition line
                    return_type = type_hints.get('return_type')
                    params_str = ', '.join(new_params)
                    
                    # Find the colon that ends the function signature
                    colon_found = False
                    colon_byte = None
                    for child in func_node.children:
                        if child.type == ':':
                            colon_found = True
                            colon_byte = child.start_byte
                            break
                    
                    if not colon_found:
                        continue
                    
                    # Build the replacement text for the signature
                    if return_type:
                        new_signature = f"def {func_name}({params_str}) -> {return_type}:"
                        # Check if return type needs typing imports
                        for typing_type in ['List', 'Dict', 'Tuple', 'Set', 'Optional', 'Union', 'Any', 'Callable']:
                            if typing_type in return_type:
                                typing_imports_needed.add(typing_type)
                    else:
                        new_signature = f"def {func_name}({params_str}):"
                    
                    # Check if parameter types need typing imports
                    for param_type in type_hints.get('parameters', {}).values():
                        if param_type:
                            for typing_type in ['List', 'Dict', 'Tuple', 'Set', 'Optional', 'Union', 'Any', 'Callable']:
                                if typing_type in param_type:
                                    typing_imports_needed.add(typing_type)
                    
                    # Find the start of 'def' keyword
                    def_start = func_node.start_byte
                    
                    # Replace from 'def' to ':' (inclusive)
                    transformer.add_change(
                        start_byte=def_start,
                        end_byte=colon_byte + 1,
                        new_text=new_signature
                    )
                    
                except Exception as e:
                    print(f"  ERROR adding type hints to `{func_name}`: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Add typing import if needed
            if typing_imports_needed:
                source_text = source_bytes.decode('utf8')
                
                # Check if typing import already exists
                has_typing_import = 'from typing import' in source_text or 'import typing' in source_text
                
                if not has_typing_import:
                    # Add the import at the beginning of the file
                    imports_str = ', '.join(sorted(typing_imports_needed))
                    import_statement = f"from typing import {imports_str}\n\n"
                    
                    # Find the position to insert (after any existing imports or at the start)
                    # For simplicity, we'll insert at the very beginning
                    transformer.add_change(
                        start_byte=0,
                        end_byte=0,
                        new_text=import_statement
                    )
                    print(f"  📦 Added typing import: {imports_str}")

    # Process magic numbers if enabled
    if fix_magic_numbers and lang == 'python':
        numeric_query = queries.get("numeric_literals")
        
        if numeric_query:
            numeric_query_obj = Query(language, numeric_query)
            
            # Collect all magic numbers with their context
            magic_numbers = {}  # {value: [(node, function_context), ...]}
            
            for _, captures in numeric_query_obj.matches(tree.root_node):
                for node in captures.get('number', []):
                    value = node.text.decode('utf8')
                    
                    # Skip acceptable numbers
                    if value in ['0', '1', '-1', '2', 'True', 'False']:
                        continue
                    
                    # Skip numbers in default parameter values (already named)
                    parent = node.parent
                    if parent and parent.type == 'default_parameter':
                        continue
                    
                    # Find the containing function for context
                    current = node.parent
                    function_node = None
                    while current:
                        if current.type == 'function_definition':
                            function_node = current
                            break
                        current = current.parent
                    
                    if function_node:
                        if value not in magic_numbers:
                            magic_numbers[value] = []
                        magic_numbers[value].append((node, function_node))
            
            # Process each unique magic number
            constants_to_add = []  # [(constant_name, value), ...]
            replacements = []  # [(node, constant_name), ...]
            
            for value, occurrences in magic_numbers.items():
                # Use the first occurrence's function for context
                first_node, first_function = occurrences[0]
                function_code = first_function.text.decode('utf8')
                
                line_num = first_node.start_point[0] + 1
                print(f"  🔢 Line {line_num}: Found magic number `{value}`", flush=True)
                
                # Get LLM suggestion for constant name
                constant_name = generator.suggest_constant_name(function_code, value)
                
                if constant_name:
                    print(f"     → Suggested constant: {constant_name}")
                    constants_to_add.append((constant_name, value))
                    
                    # Mark all occurrences for replacement
                    for node, _ in occurrences:
                        replacements.append((node, constant_name))
                else:
                    print(f"     ⚠️  Could not generate meaningful name, skipping")
            
            # Apply replacements (in reverse order to maintain byte offsets)
            replacements.sort(key=lambda x: x[0].start_byte, reverse=True)
            for node, constant_name in replacements:
                transformer.add_change(
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    new_text=constant_name
                )
            
            # Add constant definitions at the top of the file
            if constants_to_add:
                source_text = source_bytes.decode('utf8')
                
                # Find where to insert constants (after imports, before first function/class)
                # For simplicity, insert after any existing imports or at the start
                insert_position = 0
                
                # Try to find the end of imports
                lines = source_text.split('\n')
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and not stripped.startswith('import') and not stripped.startswith('from'):
                        # Found first non-import, non-comment line
                        insert_position = sum(len(l) + 1 for l in lines[:i])
                        break
                
                # Build constant definitions
                constants_text = '\n'.join(f"{name} = {value}" for name, value in constants_to_add)
                constants_text += '\n\n'
                
                transformer.add_change(
                    start_byte=insert_position,
                    end_byte=insert_position,
                    new_text=constants_text
                )
                
                print(f"  📦 Added {len(constants_to_add)} constant(s) at module level")

    elif fix_magic_numbers and lang == 'javascript':
        numeric_query = queries.get("numeric_literals")
        if numeric_query:
            numeric_query_obj = Query(language, numeric_query)
            magic_numbers = {}
            for _, captures in numeric_query_obj.matches(tree.root_node):
                for node in captures.get('number', []):
                    value = node.text.decode('utf8')
                    if value in ['0', '1', '-1', '2']:
                        continue
                    # Find containing function if available for context
                    current = node.parent
                    func_node = None
                    while current:
                        if current.type in ['function_declaration', 'method_definition']:
                            func_node = current
                            break
                        current = current.parent
                    if value not in magic_numbers:
                        magic_numbers[value] = []
                    magic_numbers[value].append((node, func_node))

            constants_to_add = []
            replacements = []
            for value, occ in magic_numbers.items():
                first_node, func_node = occ[0]
                context_code = func_node.text.decode('utf8') if func_node else source_bytes.decode('utf8')
                print(f"  🔢 Line {first_node.start_point[0] + 1}: Found magic number `{value}`")
                const_name = generator.suggest_constant_name(context_code, value) or None
                if const_name:
                    print(f"     → Suggested constant: {const_name}")
                    constants_to_add.append((const_name, value))
                    for node, _ in occ:
                        replacements.append((node, const_name))
                else:
                    print("     ⚠️  Could not generate meaningful name, skipping")

            replacements.sort(key=lambda x: x[0].start_byte, reverse=True)
            for node, const_name in replacements:
                transformer.add_change(start_byte=node.start_byte, end_byte=node.end_byte, new_text=const_name)

            if constants_to_add:
                # Insert after import/require lines
                text = source_bytes.decode('utf8')
                lines = text.split('\n')
                insert_pos = 0
                for i, line in enumerate(lines):
                    s = line.strip()
                    if s and not (s.startswith('import ') or s.startswith('from ') or s.startswith('require(') or s.startswith('//')):
                        insert_pos = sum(len(l) + 1 for l in lines[:i])
                        break
                consts_text = '\n'.join(f"const {n} = {v};" for n, v in constants_to_add) + '\n\n'
                transformer.add_change(start_byte=insert_pos, end_byte=insert_pos, new_text=consts_text)
                print(f"  📦 Added {len(constants_to_add)} constant(s) at module level")

    elif fix_magic_numbers and lang == 'java':
        numeric_query = queries.get("numeric_literals")
        if numeric_query:
            numeric_query_obj = Query(language, numeric_query)
            magic_numbers = {}
            for _, captures in numeric_query_obj.matches(tree.root_node):
                for node in captures.get('number', []):
                    value = node.text.decode('utf8')
                    if value in ['0', '1', '-1', '2']:
                        continue
                    # Ascend to method and class
                    current = node.parent
                    method_node = None
                    class_node = None
                    while current:
                        if current.type == 'method_declaration' and not method_node:
                            method_node = current
                        if current.type in ['class_declaration', 'class_declaration_simple', 'normal_class_declaration']:
                            class_node = current
                            break
                        current = current.parent
                    if class_node is None:
                        continue
                    if value not in magic_numbers:
                        magic_numbers[value] = []
                    magic_numbers[value].append((node, method_node, class_node))

            constants_to_add_by_class = {}  # class_node -> [(name, value, type_hint)]
            replacements = []
            for value, occ in magic_numbers.items():
                first_node, method_node, class_node = occ[0]
                ctx = (method_node.text.decode('utf8') if method_node else class_node.text.decode('utf8'))
                print(f"  🔢 Line {first_node.start_point[0] + 1}: Found magic number `{value}`")
                const_name = generator.suggest_constant_name(ctx, value)
                if const_name:
                    print(f"     → Suggested constant: {const_name}")
                    # Determine type: simple heuristic
                    type_kw = 'double' if ('.' in value or 'e' in value.lower()) else 'int'
                    constants_list = constants_to_add_by_class.setdefault(class_node, [])
                    constants_list.append((const_name, value, type_kw))
                    for node, _, _ in occ:
                        replacements.append((node, const_name))
                else:
                    print("     ⚠️  Could not generate meaningful name, skipping")

            replacements.sort(key=lambda x: x[0].start_byte, reverse=True)
            for node, const_name in replacements:
                transformer.add_change(start_byte=node.start_byte, end_byte=node.end_byte, new_text=const_name)

            # Insert inside each class, after opening brace
            for class_node, consts in constants_to_add_by_class.items():
                class_start = class_node.start_byte
                class_text = class_node.text.decode('utf8')
                # Find the first '{' relative position
                brace_rel = class_text.find('{')
                if brace_rel == -1:
                    continue
                insert_pos = class_start + brace_rel + 1
                const_lines = '\n'.join(f"    private static final {t} {n} = {v};" for n, v, t in consts) + '\n'
                transformer.add_change(start_byte=insert_pos, end_byte=insert_pos, new_text='\n' + const_lines)
                print(f"  📦 Added {len(consts)} constant(s) in class")

    elif fix_magic_numbers and lang == 'go':
        numeric_query = queries.get("numeric_literals")
        if numeric_query:
            numeric_query_obj = Query(language, numeric_query)
            magic_numbers = {}
            for _, captures in numeric_query_obj.matches(tree.root_node):
                for node in captures.get('number', []):
                    value = node.text.decode('utf8')
                    if value in ['0', '1', '-1', '2']:
                        continue
                    current = node.parent
                    func_node = None
                    while current:
                        if current.type == 'function_declaration':
                            func_node = current
                            break
                        current = current.parent
                    magic_numbers.setdefault(value, []).append((node, func_node))

            constants_to_add = []
            replacements = []
            for value, occ in magic_numbers.items():
                first_node, func_node = occ[0]
                ctx = func_node.text.decode('utf8') if func_node else source_bytes.decode('utf8')
                print(f"  🔢 Line {first_node.start_point[0] + 1}: Found magic number `{value}`")
                const_name = generator.suggest_constant_name(ctx, value)
                if const_name:
                    print(f"     → Suggested constant: {const_name}")
                    constants_to_add.append((const_name, value))
                    for node, _ in occ:
                        replacements.append((node, const_name))
                else:
                    print("     ⚠️  Could not generate meaningful name, skipping")

            replacements.sort(key=lambda x: x[0].start_byte, reverse=True)
            for node, const_name in replacements:
                transformer.add_change(start_byte=node.start_byte, end_byte=node.end_byte, new_text=const_name)

            if constants_to_add:
                text = source_bytes.decode('utf8')
                lines = text.split('\n')
                insert_pos = 0
                # After package and imports
                for i, line in enumerate(lines):
                    s = line.strip()
                    if s and not (s.startswith('package ') or s.startswith('import ') or s.startswith('//')):
                        insert_pos = sum(len(l) + 1 for l in lines[:i])
                        break
                consts_text = '\n'.join(f"const {n} = {v}" for n, v in constants_to_add) + '\n\n'
                transformer.add_change(start_byte=insert_pos, end_byte=insert_pos, new_text=consts_text)
                print(f"  📦 Added {len(constants_to_add)} constant(s) at package level")

    elif fix_magic_numbers and lang == 'cpp':
        numeric_query = queries.get("numeric_literals")
        if numeric_query:
            numeric_query_obj = Query(language, numeric_query)
            magic_numbers = {}
            for _, captures in numeric_query_obj.matches(tree.root_node):
                for node in captures.get('number', []):
                    value = node.text.decode('utf8')
                    if value in ['0', '1', '-1', '2']:
                        continue
                    current = node.parent
                    func_node = None
                    while current:
                        if current.type == 'function_definition':
                            func_node = current
                            break
                        current = current.parent
                    magic_numbers.setdefault(value, []).append((node, func_node))

            constants_to_add = []
            replacements = []
            for value, occ in magic_numbers.items():
                first_node, func_node = occ[0]
                ctx = func_node.text.decode('utf8') if func_node else source_bytes.decode('utf8')
                print(f"  🔢 Line {first_node.start_point[0] + 1}: Found magic number `{value}`")
                const_name = generator.suggest_constant_name(ctx, value)
                if const_name:
                    print(f"     → Suggested constant: {const_name}")
                    constants_to_add.append((const_name, value))
                    for node, _ in occ:
                        replacements.append((node, const_name))
                else:
                    print("     ⚠️  Could not generate meaningful name, skipping")

            replacements.sort(key=lambda x: x[0].start_byte, reverse=True)
            for node, const_name in replacements:
                transformer.add_change(start_byte=node.start_byte, end_byte=node.end_byte, new_text=const_name)

            if constants_to_add:
                text = source_bytes.decode('utf8')
                lines = text.split('\n')
                insert_pos = 0
                # After includes
                for i, line in enumerate(lines):
                    s = line.strip()
                    if s and not (s.startswith('#include') or s.startswith('//')):
                        insert_pos = sum(len(l) + 1 for l in lines[:i])
                        break
                consts_text = '\n'.join(f"constexpr auto {n} = {v};" for n, v in constants_to_add) + '\n\n'
                transformer.add_change(start_byte=insert_pos, end_byte=insert_pos, new_text=consts_text)
                print(f"  📦 Added {len(constants_to_add)} constant(s) at file scope")

    # Dead code detection/removal (Python)
    if dead_code and lang == 'python':
        import ast
        source_text = source_bytes.decode('utf8')
        tree_ast = None
        try:
            tree_ast = ast.parse(source_text)
        except Exception as e:
            print(f"  [ERROR] AST parse error for dead code detection: {e}")
            tree_ast = None
        if tree_ast:
            # Collect imports
            imports = []  # list of dict{name, lineno, type: 'import'|'from', line_text}
            lines = source_text.split('\n')
            for node in ast.walk(tree_ast):
                if isinstance(node, ast.Import):
                    names = [alias.asname or alias.name.split('.')[0] for alias in node.names]
                    imports.append({
                        'type': 'import',
                        'names': names,
                        'lineno': node.lineno,
                        'col': node.col_offset,
                        'text': lines[node.lineno-1] if 1 <= node.lineno <= len(lines) else ''
                    })
                elif isinstance(node, ast.ImportFrom):
                    # skip relative imports where module is None
                    names = [alias.asname or alias.name for alias in node.names]
                    imports.append({
                        'type': 'from',
                        'module': node.module or '',
                        'names': names,
                        'lineno': node.lineno,
                        'col': node.col_offset,
                        'text': lines[node.lineno-1] if 1 <= node.lineno <= len(lines) else ''
                    })

            # Collect identifiers usage (simple heuristic)
            used = set()
            for node in ast.walk(tree_ast):
                if isinstance(node, ast.Name):
                    used.add(node.id)
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    used.add(node.value.id)

            # Functions defined and called
            func_defs = []
            func_calls = set()
            for node in ast.walk(tree_ast):
                if isinstance(node, ast.FunctionDef):
                    # Consider only top-level functions (skip class methods)
                    if getattr(node, 'col_offset', 0) == 0:
                        func_defs.append((node.name, node.lineno))
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                        func_calls.add(node.func.attr)

            # Report and optionally remove unused imports
            print("\n  🧹 Dead Code Report (Python):")
            to_delete_lines = []
            unused_imports_count = 0
            for imp in imports:
                imp_used = any(name.split('.')[0] in used for name in imp.get('names', []))
                if not imp_used:
                    unused_imports_count += 1
                    print(f"  • Unused import at line {imp['lineno']}: {imp['text'].strip()}")
                    # Mark whole line for deletion (safe only when all names unused)
                    to_delete_lines.append(imp['lineno'])

            # Report never-called functions
            never_called = [(name, ln) for (name, ln) in func_defs if name not in func_calls]
            for name, ln in never_called:
                print(f"  • Function never called: {name} (line {ln})")

            # Detect unused top-level variables (simple heuristic)
            unused_vars = []
            for node in ast.walk(tree_ast):
                if isinstance(node, ast.Assign):
                    if getattr(node, 'col_offset', 1) == 0:  # top-level
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                var_name = target.id
                                if var_name not in used:
                                    # Get line text
                                    ln = node.lineno
                                    txt = lines[ln-1] if 1 <= ln <= len(lines) else ''
                                    unused_vars.append((var_name, ln, txt))
            for name, ln, txt in unused_vars:
                print(f"  • Unused variable: {name} (line {ln}): {txt.strip()}")

            if in_place and to_delete_lines:
                # Delete lines in reverse order
                for ln in sorted(to_delete_lines, reverse=True):
                    line_start = sum(len(l) + 1 for l in lines[:ln-1])
                    line_end = line_start + len(lines[ln-1]) + 1  # include newline
                    transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
                print(f"  ✂️  Removed {len(to_delete_lines)} unused import line(s)")

            if in_place and unused_vars:
                for _, ln, _ in sorted(unused_vars, key=lambda x: x[1], reverse=True):
                    line_start = sum(len(l) + 1 for l in lines[:ln-1])
                    line_end = line_start + len(lines[ln-1]) + 1
                    transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
                print(f"  ✂️  Removed {len(unused_vars)} unused top-level variable assignment(s)")

            # Strict mode: delete never-called private functions (name starts with '_')
            if in_place and dead_code_strict:
                removed_funcs = 0
                for name, ln in sorted(never_called, key=lambda x: x[1], reverse=True):
                    if name.startswith('_'):
                        # Find block range: use end_lineno if available
                        func_node = None
                        for node in ast.walk(tree_ast):
                            if isinstance(node, ast.FunctionDef) and node.name == name and getattr(node, 'lineno', 0) == ln:
                                func_node = node
                                break
                        if func_node is None:
                            continue
                        end_ln = getattr(func_node, 'end_lineno', None)
                        if end_ln is None and func_node.body:
                            end_ln = func_node.body[-1].lineno
                        if end_ln is None:
                            continue
                        start_byte = sum(len(l) + 1 for l in lines[:ln-1])
                        end_byte = sum(len(l) + 1 for l in lines[:end_ln])
                        transformer.add_change(start_byte=start_byte, end_byte=end_byte, new_text='')
                        removed_funcs += 1
                if removed_funcs:
                    print(f"  ✂️  Strict: Removed {removed_funcs} private never-called function(s)")

            # Strict mode: remove unused local variables (simple, safe cases)
            if in_place and dead_code_strict:
                removed_locals = 0
                try:
                    # Iterate over all functions (including nested)
                    for func_node in [n for n in ast.walk(tree_ast) if isinstance(n, ast.FunctionDef)]:
                        # Names used (reads) in the function body
                        used_in_func = set()
                        for sub in ast.walk(func_node):
                            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                                used_in_func.add(sub.id)

                        # Collect simple local assignments inside this function
                        local_assign_lines = []  # (lineno)
                        for sub in ast.walk(func_node):
                            if isinstance(sub, ast.Assign):
                                # local if indented more than def line
                                if getattr(sub, 'col_offset', 0) > getattr(func_node, 'col_offset', 0):
                                    if len(sub.targets) == 1 and isinstance(sub.targets[0], ast.Name):
                                        var_name = sub.targets[0].id
                                        val = sub.value
                                        # Only simple literal initializers (numbers, strings, booleans, None)
                                        is_simple = isinstance(val, ast.Constant)
                                        if is_simple and var_name not in used_in_func:
                                            local_assign_lines.append(sub.lineno)

                        # Remove lines in reverse order to maintain positions
                        for ln in sorted(set(local_assign_lines), reverse=True):
                            if 1 <= ln <= len(lines):
                                line_start = sum(len(l) + 1 for l in lines[:ln-1])
                                line_end = line_start + len(lines[ln-1]) + 1
                                transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
                                removed_locals += 1
                except Exception as e:
                    print(f"  ⚠️  Python local-var strict removal error: {e}")
                if removed_locals:
                    print(f"  ✂️  Strict: Removed {removed_locals} unused local variable declaration(s)")

    # Dead code detection/removal (JavaScript)
    if dead_code and lang == 'javascript':
        source_text = source_bytes.decode('utf8')
        lines = source_text.split('\n')
        # Collect imported names and lines
        imported = []  # list of (name, lineno)
        import_lines = set()
        # Collect top-level const/let names
        top_level_vars = []  # list of (name, lineno)
        # Strict-mode local candidates inside functions
        local_candidates_js = []  # (func_node, decl_node, name, lineno)
        try:
            # Traverse root children to find import and top-level lexical declarations
            for child in tree.root_node.children:
                if child.type == 'import_declaration':
                    import_lines.add(child.start_point[0] + 1)
                    # Get text of the import line
                    text = source_text[child.start_byte:child.end_byte]
                    # Naive parse of imported names
                    # import { a, b as c } from 'x';  import x from 'y';
                    names = []
                    if '{' in text:
                        inner = text.split('{',1)[1].split('}',1)[0]
                        for spec in inner.split(','):
                            name = spec.strip().split(' as ')[-1].strip()
                            if name:
                                names.append(name)
                    else:
                        # default import
                        after_import = text[len('import'):].strip()
                        default_name = after_import.split('from')[0].strip().strip(',')
                        if default_name and not default_name.startswith('*'):
                            names.append(default_name)
                    for n in names:
                        imported.append((n, child.start_point[0] + 1))
                elif child.type in ['lexical_declaration', 'variable_declaration']:
                    # Only top-level
                    # Extract declarators
                    text = source_text[child.start_byte:child.end_byte]
                    # Very simple split: const name = ...; or let name = ...;
                    decl = text.strip().rstrip(';')
                    if 'const ' in decl or 'let ' in decl:
                        after_kw = decl.split('const ',1)[-1] if 'const ' in decl else decl.split('let ',1)[-1]
                        # Support multiple declarators: a = 1, b = 2
                        for part in after_kw.split(','):
                            name = part.strip().split('=')[0].strip()
                            # filter valid identifiers
                            if name and name.replace('_','').replace('$','').isalnum():
                                top_level_vars.append((name, child.start_point[0] + 1))
                # Also collect local declarations within function bodies for strict mode
                if child.type == 'function_declaration':
                    func_node = child
                    # find body block
                    body = None
                    for c2 in func_node.children:
                        if c2.type == 'statement_block' or c2.type == 'formal_parameters':
                            # continue search
                            pass
                    body = func_node.child_by_field_name('body')
                    if body:
                        stack = [body]
                        while stack:
                            cur = stack.pop()
                            for ch in cur.children:
                                stack.append(ch)
                            # variable_declaration or lexical_declaration
                            if cur.type in ['variable_declaration', 'lexical_declaration']:
                                text = source_text[cur.start_byte:cur.end_byte].strip()
                                # only single declarator conservatively: no comma in declaration (before ';')
                                head = text.split(';',1)[0]
                                if ',' in head:
                                    continue
                                # simple initializer: avoid '(' which suggests a call
                                if '(' in head:
                                    continue
                                # extract identifier name
                                # patterns: const name = 1; let name = 'x'; var name = 2;
                                kw_split = None
                                if head.startswith('const '):
                                    kw_split = head[len('const '):]
                                elif head.startswith('let '):
                                    kw_split = head[len('let '):]
                                elif head.startswith('var '):
                                    kw_split = head[len('var '):]
                                if kw_split is None:
                                    continue
                                ident = kw_split.split('=')[0].strip()
                                if ident and ident.replace('_','').replace('$','').isalnum():
                                    local_candidates_js.append((func_node, cur, ident, cur.start_point[0] + 1))
        except Exception as e:
            print(f"  ⚠️  JS scanning error: {e}")

        # Build usage map via naive search (exclude declaration/import lines)
        used = set()
        decl_lines = {ln for _, ln in top_level_vars}
        skip_lines = set(import_lines) | decl_lines
        for i, line in enumerate(lines, start=1):
            if i in skip_lines:
                continue
            # Ignore single-line comments
            line = line.split('//')[0]
            tokens = [t for t in line.replace('(', ' ').replace(')', ' ').replace(';', ' ').replace('.', ' ').split()]
            for t in tokens:
                used.add(t)

        # Unused imports
        unused_imports = [(n, ln) for (n, ln) in imported if n not in used]
        if unused_imports:
            print("\n  🧹 Dead Code Report (JavaScript):")
            for n, ln in unused_imports:
                print(f"  • Unused import: {n} (line {ln})")
        if in_place and unused_imports:
            # Remove entire import lines (dedupe by line)
            del_lines = sorted({ln for _, ln in unused_imports}, reverse=True)
            for ln in del_lines:
                line_start = sum(len(l) + 1 for l in lines[:ln-1])
                line_end = line_start + len(lines[ln-1]) + 1
                transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
            print(f"  ✂️  Removed {len(del_lines)} unused import line(s)")

        # Unused top-level const/let
        unused_vars_js = [(n, ln) for (n, ln) in top_level_vars if n not in used]
        for n, ln in unused_vars_js:
            print(f"  • Unused top-level variable: {n} (line {ln})")
        if in_place and unused_vars_js:
            for n, ln in sorted(unused_vars_js, key=lambda x: x[1], reverse=True):
                # Remove the entire line (conservative)
                line_start = sum(len(l) + 1 for l in lines[:ln-1])
                line_end = line_start + len(lines[ln-1]) + 1
                transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
            print(f"  ✂️  Removed {len(unused_vars_js)} unused top-level variable declaration(s)")

        # Strict: remove unused local variables inside functions (conservative)
        if dead_code_strict and in_place and local_candidates_js:
            removed_locals = 0
            for func_node, decl_node, name, ln in sorted(local_candidates_js, key=lambda x: x[3], reverse=True):
                # Determine function absolute line range
                func_start_line = func_node.start_point[0] + 1
                func_end_line = func_node.end_point[0] + 1
                appears_elsewhere = False
                for abs_ln in range(func_start_line, func_end_line + 1):
                    if abs_ln == ln:
                        continue
                    line = lines[abs_ln - 1] if 1 <= abs_ln <= len(lines) else ''
                    line = line.split('//')[0]
                    if name in line:
                        appears_elsewhere = True
                        break
                if appears_elsewhere:
                    continue
                # Remove the declaration node range
                transformer.add_change(start_byte=decl_node.start_byte, end_byte=decl_node.end_byte, new_text='')
                removed_locals += 1
            if removed_locals:
                print(f"  ✂️  Strict: Removed {removed_locals} unused local variable declaration(s)")

    # Dead code detection/removal (Java)
    if dead_code and lang == 'java':
        source_text = source_bytes.decode('utf8')
        lines = source_text.split('\n')
        # Collect imports, private fields, methods
        import_lines = []  # (lineno, text, short_name)
        private_fields = []  # (node, name, lineno)
        private_methods = []  # (node, name, lineno)
        local_candidates_java = []  # (method_node, decl_node, name, lineno)
        try:
            # Imports: import_declaration
            for child in tree.root_node.children:
                if child.type == 'import_declaration':
                    ln = child.start_point[0] + 1
                    text = source_text[child.start_byte:child.end_byte]
                    # short name is after last '.' and before ';'
                    body = text.replace('import', '').replace(';', '').strip()
                    short = body.split('.')[-1].strip()
                    if short:
                        import_lines.append((ln, text, short))
            # Walk to find fields and methods
            def walk(n):
                for c in n.children:
                    # Field declaration with private modifier
                    if c.type == 'field_declaration':
                        mods = ''.join(source_text[m.start_byte:m.end_byte] for m in c.children if m.type == 'modifiers')
                        if 'private' in mods:
                            # ensure single declarator
                            declarators = [d for d in c.children if d.type == 'variable_declarator']
                            if len(declarators) == 1:
                                decl = declarators[0]
                                # name is identifier under declarator
                                name_node = None
                                for cc in decl.children:
                                    if cc.type == 'identifier':
                                        name_node = cc; break
                                if name_node:
                                    private_fields.append((c, name_node.text.decode('utf8'), c.start_point[0] + 1))
                    # Method declaration with private modifier
                    if c.type == 'method_declaration':
                        mods = ''.join(source_text[m.start_byte:m.end_byte] for m in c.children if m.type == 'modifiers')
                        if 'private' in mods:
                            name_node = c.child_by_field_name('name')
                            if name_node:
                                private_methods.append((c, name_node.text.decode('utf8'), c.start_point[0] + 1))
                        # Collect local variable declarations for strict mode
                        body = c.child_by_field_name('body')
                        if body:
                            # Traverse body to find local_variable_declaration
                            stack = [body]
                            while stack:
                                cur = stack.pop()
                                for ch in cur.children:
                                    stack.append(ch)
                                if cur.type == 'local_variable_declaration':
                                    # Ensure single variable_declarator and simple literal initializer
                                    text = source_text[cur.start_byte:cur.end_byte]
                                    head = text.split(';',1)[0]
                                    if ',' in head:
                                        continue
                                    if '(' in head:
                                        continue
                                    # find variable_declarator -> identifier
                                    decls = [cc for cc in cur.children if cc.type == 'variable_declarator']
                                    if len(decls) == 1:
                                        decl = decls[0]
                                        id_node = None
                                        for cc in decl.children:
                                            if cc.type == 'identifier':
                                                id_node = cc; break
                                        if id_node is not None:
                                            local_candidates_java.append((c, cur, id_node.text.decode('utf8'), cur.start_point[0] + 1))
                    walk(c)
            walk(tree.root_node)

            # Build used identifiers set, excluding import and declaration lines
            skip_lines = {ln for (ln, _, _) in import_lines} | {ln for (_, _, ln) in private_fields} | {ln for (_, _, ln) in private_methods}
            used = set()
            for i, line in enumerate(lines, start=1):
                if i in skip_lines:
                    continue
                # Ignore single-line comments
                line = line.split('//')[0]
                tokens = [t for t in line.replace('(', ' ').replace(')', ' ').replace(';', ' ').replace('.', ' ').split()]
                for t in tokens:
                    used.add(t)

            # Unused imports
            unused_imports = [(ln, text, name) for (ln, text, name) in import_lines if name not in used]
            if unused_imports:
                print("\n  🧹 Dead Code Report (Java):")
                for ln, text, name in unused_imports:
                    print(f"  • Unused import: {name} (line {ln})")
            if in_place and unused_imports:
                for ln, _, _ in sorted(unused_imports, key=lambda x: x[0], reverse=True):
                    line_start = sum(len(l) + 1 for l in lines[:ln-1])
                    line_end = line_start + len(lines[ln-1]) + 1
                    transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
                print(f"  ✂️  Removed {len(unused_imports)} unused import line(s)")

            # Unused private fields (single declarator only)
            unused_fields = [(node, name, ln) for (node, name, ln) in private_fields if name not in used]
            for _, name, ln in unused_fields:
                print(f"  • Unused private field: {name} (line {ln})")
            if in_place and unused_fields:
                for node, _, _ in sorted(unused_fields, key=lambda x: x[2], reverse=True):
                    start_byte = node.start_byte
                    end_byte = node.end_byte
                    transformer.add_change(start_byte=start_byte, end_byte=end_byte, new_text='')
                print(f"  ✂️  Removed {len(unused_fields)} unused private field(s)")

            # Strict: private never-called methods
            if dead_code_strict and in_place and private_methods:
                # Build called method names (very naive: look for identifier + '(' tokens)
                called = set()
                for i, line in enumerate(lines, start=1):
                    if i in skip_lines:
                        continue
                    parts = line.split('//')[0].replace('.', ' ').split()
                    for pm_name in [n for (_, n, _) in private_methods]:
                        if pm_name + '(' in line or f" {pm_name} (" in line:
                            called.add(pm_name)
                to_remove = [(node, name, ln) for (node, name, ln) in private_methods if name not in called]
                for _, name, ln in to_remove:
                    print(f"  • Strict: private method never called: {name} (line {ln})")
                if to_remove:
                    for node, _, _ in sorted(to_remove, key=lambda x: x[2], reverse=True):
                        transformer.add_change(start_byte=node.start_byte, end_byte=node.end_byte, new_text='')
                    print(f"  ✂️  Strict: Removed {len(to_remove)} private never-called method(s)")
            # Strict: remove unused local variables inside methods (conservative)
            if dead_code_strict and in_place and local_candidates_java:
                removed_locals = 0
                for method_node, decl_node, name, ln in sorted(local_candidates_java, key=lambda x: x[3], reverse=True):
                    # Determine method absolute line range
                    m_start = method_node.start_point[0] + 1
                    m_end = method_node.end_point[0] + 1
                    appears = False
                    for abs_ln in range(m_start, m_end + 1):
                        if abs_ln == ln:
                            continue
                        line = lines[abs_ln - 1] if 1 <= abs_ln <= len(lines) else ''
                        line = line.split('//')[0]
                        if name in line:
                            appears = True
                            break
                    if appears:
                        continue
                    transformer.add_change(start_byte=decl_node.start_byte, end_byte=decl_node.end_byte, new_text='')
                    removed_locals += 1
                if removed_locals:
                    print(f"  ✂️  Strict: Removed {removed_locals} unused local variable declaration(s)")
        except Exception as e:
            print(f"  ⚠️  Java dead-code scan error: {e}")

    # Dead code detection/removal (Go)
    if dead_code and lang == 'go':
        source_text = source_bytes.decode('utf8')
        lines = source_text.split('\n')
        try:
            # Collect imports (handle single and block)
            import_specs = []  # list of (node, pkg_name, lineno)
            for child in tree.root_node.children:
                if child.type == 'import_declaration':
                    # import_declaration has children: 'import' token, optional '(', multiple import_spec, optional ')'
                    for spec in child.children:
                        if spec.type == 'import_spec':
                            # import spec like: name? string_lit
                            alias = None
                            path = None
                            for sp in spec.children:
                                if sp.type == 'identifier' and alias is None:
                                    alias = sp.text.decode('utf8')
                                if sp.type == 'interpreted_string_literal':
                                    path = sp.text.decode('utf8').strip('"')
                            if path:
                                pkg = alias if alias else (path.split('/')[-1] if '/' in path else path)
                                import_specs.append((spec, pkg, spec.start_point[0] + 1))

            # Collect top-level var/const single-name specs
            top_level_specs = []  # list of (node, name, lineno)
            def walk_go(n, parent=None):
                for c in n.children:
                    # Top-level var/const declarations
                    if parent is tree.root_node and c.type in ['var_declaration', 'const_declaration']:
                        # var_declaration -> var_spec (may be multiple); remove only single-name specs
                        for vs in c.children:
                            if vs.type in ['var_spec', 'const_spec']:
                                # identifiers list under vs
                                ids = [cc for cc in vs.children if cc.type == 'identifier']
                                if len(ids) == 1:
                                    name = ids[0].text.decode('utf8')
                                    top_level_specs.append((vs, name, vs.start_point[0] + 1))
                    # Functions: function_declaration nodes
                    if c.type == 'function_declaration' and parent is tree.root_node:
                        # Strict local declarations inside this function
                        body = None
                        for cc in c.children:
                            if cc.type == 'block':
                                body = cc; break
                        if body is not None:
                            # Traverse body to find local declarations
                            stack = [body]
                            while stack:
                                cur = stack.pop()
                                for ch in cur.children:
                                    stack.append(ch)
                                    # short_var_declaration: a := 1
                                    if ch.type == 'short_var_declaration':
                                        # Single left identifier and simple literal on right
                                        # Extract identifier and check rhs for basic_lit
                                        left_ids = [cc for cc in ch.children if cc.type == 'identifier']
                                        has_call = '(' in source_text[ch.start_byte:ch.end_byte].split(';',1)[0]
                                        if len(left_ids) == 1 and not has_call:
                                            name = left_ids[0].text.decode('utf8')
                                            # mark candidate via tuple (func_node, decl_node, name, lineno)
                                            local_candidates.append((c, ch, name, ch.start_point[0] + 1))
                                    # var_declaration inside function (var x = 1)
                                    if ch.type == 'var_declaration':
                                        for vs in ch.children:
                                            if vs.type == 'var_spec':
                                                ids = [iii for iii in vs.children if iii.type == 'identifier']
                                                has_call = '(' in source_text[vs.start_byte:vs.end_byte].split(';',1)[0]
                                                if len(ids) == 1 and not has_call:
                                                    name = ids[0].text.decode('utf8')
                                                    local_candidates.append((c, vs, name, vs.start_point[0] + 1))
                    walk_go(c, n)

            local_candidates = []  # filled in walk_go for strict mode
            walk_go(tree.root_node)

            # Build used token set, excluding declaration/import spec lines
            skip_lines = {ln for (_, _, ln) in import_specs} | {ln for (_, _, ln) in top_level_specs}
            used = set()
            for i, line in enumerate(lines, start=1):
                if i in skip_lines:
                    continue
                # Ignore single-line comments
                line = line.split('//')[0]
                tokens = [t for t in line.replace('.', ' ').replace('(', ' ').replace(')', ' ').replace(';',' ').split()]
                for t in tokens:
                    used.add(t)

            # Unused imports
            unused_imps = [(spec, pkg, ln) for (spec, pkg, ln) in import_specs if pkg not in used]
            if unused_imps:
                print("\n  🧹 Dead Code Report (Go):")
                for _, pkg, ln in unused_imps:
                    print(f"  • Unused import: {pkg} (line {ln})")
            if in_place and unused_imps:
                # Remove individual import_spec nodes
                for spec, _, _ in sorted(unused_imps, key=lambda x: x[2], reverse=True):
                    transformer.add_change(start_byte=spec.start_byte, end_byte=spec.end_byte, new_text='')
                print(f"  ✂️  Removed {len(unused_imps)} unused import spec(s)")

            # Unused top-level var/const (single identifier only)
            unused_top = [(node, name, ln) for (node, name, ln) in top_level_specs if name not in used]
            for _, name, ln in unused_top:
                print(f"  • Unused top-level identifier: {name} (line {ln})")
            if in_place and unused_top:
                for node, _, _ in sorted(unused_top, key=lambda x: x[2], reverse=True):
                    transformer.add_change(start_byte=node.start_byte, end_byte=node.end_byte, new_text='')
                print(f"  ✂️  Removed {len(unused_top)} unused top-level var/const spec(s)")

            # Strict: remove unused local variables (simple literal initializers)
            if dead_code_strict and in_place and local_candidates:
                removed_locals = 0
                for func_node, decl_node, name, ln in sorted(local_candidates, key=lambda x: x[3], reverse=True):
                    # Build function range lines
                    func_start = func_node.start_point[0] + 1
                    func_end = func_node.end_point[0] + 1
                    appears = False
                    for abs_ln in range(func_start, func_end + 1):
                        if abs_ln == ln:
                            continue
                        line = lines[abs_ln - 1] if 1 <= abs_ln <= len(lines) else ''
                        line = line.split('//')[0]
                        if name in line:
                            appears = True
                            break
                    if appears:
                        continue
                    # Remove declaration node
                    transformer.add_change(start_byte=decl_node.start_byte, end_byte=decl_node.end_byte, new_text='')
                    removed_locals += 1
                if removed_locals:
                    print(f"  ✂️  Strict: Removed {removed_locals} unused local variable declaration(s)")
        except Exception as e:
            print(f"  ⚠️  Go dead-code scan error: {e}")

    # Dead code detection/removal (C++)
    if dead_code and lang == 'cpp':
        source_text = source_bytes.decode('utf8')
        lines = source_text.split('\n')
        # Collect top-level variable declarations and static functions
        top_level_vars = []  # (node, name, lineno)
        static_functions = []  # (node, name, lineno)
        # Local unused variables (strict mode handling)
        local_unused_candidates = []  # (func_node, decl_node, name, decl_line)
        try:
            def walk_cpp(n, parent=None):
                for c in n.children:
                    # Top-level variable declarations: parent is translation_unit
                    if c.type in ['declaration', 'init_declarator'] and n.type == 'translation_unit':
                        # find identifier under declarator
                        name_node = None
                        for cc in c.children:
                            if cc.type == 'init_declarator':
                                for ccc in cc.children:
                                    if ccc.type == 'identifier':
                                        name_node = ccc
                            elif cc.type == 'identifier':
                                name_node = cc
                        if name_node:
                            top_level_vars.append((c, name_node.text.decode('utf8'), c.start_point[0] + 1))
                    # Static functions: function_definition under TU and has 'static' keyword
                    if c.type == 'function_definition' and n.type == 'translation_unit':
                        text = source_text[c.start_byte:c.end_byte]
                        name_node = None
                        # find identifier in declarator
                        decl = c.child_by_field_name('declarator')
                        if decl:
                            for cc in decl.children:
                                if cc.type == 'identifier':
                                    name_node = cc; break
                        if name_node:
                            if 'static' in text.split('{',1)[0]:
                                static_functions.append((c, name_node.text.decode('utf8'), c.start_point[0] + 1))
                        # Collect local declarations within this function body (for strict mode)
                        body = c.child_by_field_name('body')
                        if body:
                            # Traverse body to find simple local declarations
                            nodes = [body]
                            while nodes:
                                cur = nodes.pop()
                                for ch in cur.children:
                                    nodes.append(ch)
                                # declaration nodes inside function body
                                if cur.type == 'declaration':
                                    # Try to get the init_declarator and identifier
                                    id_node = None
                                    init_text = source_text[cur.start_byte:cur.end_byte]
                                    # Skip likely complex initializers (calls) by presence of '(' before ';'
                                    if '(' in init_text.split(';',1)[0]:
                                        continue
                                    for ch in cur.children:
                                        if ch.type == 'init_declarator':
                                            for ccc in ch.children:
                                                if ccc.type == 'identifier':
                                                    id_node = ccc; break
                                        elif ch.type == 'identifier' and id_node is None:
                                            id_node = ch
                                    if id_node is not None:
                                        var_name = id_node.text.decode('utf8')
                                        local_unused_candidates.append((c, cur, var_name, cur.start_point[0] + 1))
                    walk_cpp(c, n)
            walk_cpp(tree.root_node)

            # Build used token set excluding their own lines and includes
            skip_lines = {ln for (_, _, ln) in top_level_vars} | {ln for (_, _, ln) in static_functions}
            used = set()
            for i, line in enumerate(lines, start=1):
                if i in skip_lines:
                    continue
                if line.strip().startswith('#include'):
                    continue
                # Ignore single-line comments
                line = line.split('//')[0]
                tokens = [t for t in line.replace('(', ' ').replace(')', ' ').replace(';',' ').replace('.', ' ').split()]
                for t in tokens:
                    used.add(t)

            # Unused top-level variables
            unused_vars = [(node, name, ln) for (node, name, ln) in top_level_vars if name not in used]
            for _, name, ln in unused_vars:
                print(f"\n  🧹 Dead Code Report (C++):\n  • Unused global variable: {name} (line {ln})")
            if in_place and unused_vars:
                for node, _, _ in sorted(unused_vars, key=lambda x: x[2], reverse=True):
                    transformer.add_change(start_byte=node.start_byte, end_byte=node.end_byte, new_text='')
                print(f"  ✂️  Removed {len(unused_vars)} unused global variable declaration(s)")

            # Strict: static never-called functions
            if dead_code_strict and in_place and static_functions:
                called = set()
                for i, line in enumerate(lines, start=1):
                    if i in skip_lines:
                        continue
                    # Ignore single-line comments
                    line = line.split('//')[0]
                    for _, name, _ in static_functions:
                        if name + '(' in line:
                            called.add(name)
                to_remove = [(node, name, ln) for (node, name, ln) in static_functions if name not in called]
                for _, name, ln in to_remove:
                    print(f"  • Strict: static function never called: {name} (line {ln})")
                if to_remove:
                    for node, _, _ in sorted(to_remove, key=lambda x: x[2], reverse=True):
                        transformer.add_change(start_byte=node.start_byte, end_byte=node.end_byte, new_text='')
                    print(f"  ✂️  Strict: Removed {len(to_remove)} static never-called function(s)")

            # Strict: remove unused local variables inside functions (conservative)
            if dead_code_strict and in_place and local_unused_candidates:
                removed_locals = 0
                for func_node, decl_node, name, ln in sorted(local_unused_candidates, key=lambda x: x[3], reverse=True):
                    # Build function body text without the declaration line
                    func_text = source_text[func_node.start_byte:func_node.end_byte]
                    # If name appears elsewhere in function body (excluding its declaration line), skip
                    # Cheap check: scan all lines in function range except decl line
                    func_lines = func_text.split('\n')
                    # Determine absolute line range of the function
                    func_start_line = func_node.start_point[0] + 1
                    func_end_line = func_node.end_point[0] + 1
                    appears_elsewhere = False
                    for abs_ln in range(func_start_line, func_end_line + 1):
                        if abs_ln == ln:
                            continue
                        line = lines[abs_ln - 1] if 1 <= abs_ln <= len(lines) else ''
                        # token boundary check
                        if f"{name}" in line:
                            appears_elsewhere = True
                            break
                    if appears_elsewhere:
                        continue
                    # Remove the declaration line
                    line_start = sum(len(l) + 1 for l in lines[:ln-1])
                    line_end = line_start + len(lines[ln-1]) + 1
                    transformer.add_change(start_byte=line_start, end_byte=line_end, new_text='')
                    removed_locals += 1
                if removed_locals:
                    print(f"  ✂️  Strict: Removed {removed_locals} unused local variable declaration(s)")
        except Exception as e:
            print(f"  ⚠️  C++ dead-code scan error: {e}")

    new_code = transformer.apply_changes()
    if in_place:
        if new_code != source_bytes:
            print("\n  💾 Saving changes to file...")
            try:
                with open(filepath, 'wb') as f:
                    f.write(new_code)
                print("  [OK] File updated successfully!")
            except IOError as e:
                print(f"  [ERROR] Error writing to file: {e}")
        else:
            print("\n  ℹ️  No changes needed for this file.")
    else:
        # Print to console if not in_place
        print("\n  👁️  Preview of Changes (Dry Run):")
        print(f"  {'─'*66}\n")
        print(new_code.decode('utf8'))


def run_autodoc(args):
    """The main entry point for running the analysis."""
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit("🤖 [bold blue]AutoDoc AI[/bold blue] - Code Analysis & Enhancement", 
                               border_style="blue", padding=(1, 2)))
    else:
        cprint(f"\n{'='*70}", 'cyan')
        cprint(f"  🤖 AutoDoc AI - Code Analysis & Enhancement", 'blue', 'bold')
        cprint(f"{'='*70}\n", 'cyan')
    
    # Determine which features are enabled (opt-in)
    docstrings_enabled = getattr(args, 'docstrings', False) or getattr(args, 'overwrite_existing', False)
    hints_enabled = getattr(args, 'add_type_hints', False)
    magic_enabled = getattr(args, 'fix_magic_numbers', False)
    dead_code_enabled = getattr(args, 'dead_code', False)
    dead_code_strict_enabled = getattr(args, 'dead_code_strict', False)
    refactor_enabled = getattr(args, 'refactor', False)
    refactor_strict_enabled = getattr(args, 'refactor_strict', False)

    # Umbrella flags: --refactor turns on all non-strict features; --refactor-strict also enables strict dead-code
    if refactor_enabled or refactor_strict_enabled:
        docstrings_enabled = True or docstrings_enabled
        hints_enabled = True or hints_enabled
        magic_enabled = True or magic_enabled
        dead_code_enabled = True or dead_code_enabled
        if refactor_strict_enabled:
            dead_code_strict_enabled = True or dead_code_strict_enabled

    # Show what features are enabled
    features = []
    if docstrings_enabled:
        features.append("Docstrings")
        if args.overwrite_existing:
            features.append("Docstring Improvement")
    if hints_enabled:
        features.append("Type Hints")
    if magic_enabled:
        features.append("Magic Number Replacement")
    if dead_code_enabled:
        features.append("Dead Code")
    if refactor_enabled or refactor_strict_enabled:
        # Print umbrella banner explicitly listing what refactor mode enables
        umbrella = ["Docstrings", "Type Hints", "Magic Numbers", "Dead Code"]
        if refactor_strict_enabled:
            umbrella.append("Strict Dead Code")
        cprint(f"🧰 Refactor mode enabled → {', '.join(umbrella)}", 'green')

    if not any([docstrings_enabled, hints_enabled, magic_enabled, dead_code_enabled]):
        cprint("⚠️  No features selected. Use one or more of: --docstrings, --overwrite-existing, --add-type-hints, --fix-magic-numbers, --dead-code, --dead-code-strict, --refactor, --refactor-strict", 'yellow')
        return
    
    print(f"📋 Active Features: {', '.join(features)}")
    print(f"📝 Docstring Style: {args.style}")
    
    if args.diff:
        print(f"🔍 Mode: Git-changed files only\n")
        print("Scanning for modified files...")
        source_files = get_git_changed_files()
        if source_files is None: 
            print("[ERROR] Error: Not a git repository or no changes found.")
            sys.exit(1)
    else:
        print(f"📂 Target: {args.path}\n")
        print("Scanning for source files...")
        source_files = get_source_files(args.path)
    
    if not source_files:
        print("\n⚠️  No source files found to process.")
        print("💡 Tip: Make sure you're in the right directory or specify a path.")
        return

    print(f"✓ Found {len(source_files)} file(s) to process.\n")
    
    # Show provider info
    provider = getattr(args, 'provider', None) or os.getenv('AUTODOC_PROVIDER', 'groq')
    model = getattr(args, 'model', None)
    if args.strategy != 'mock':
        print(f"🤖 Using: {provider.upper()}" + (f" ({model})" if model else ""))
        if not args.in_place:
            print(f"👁️  Mode: Dry-run (preview only - use --in-place to save changes)")
        else:
            print(f"💾 Mode: In-place (files will be modified)")
        print()
    
    try:
        generator = GeneratorFactory.create_generator(
            args.strategy,
            args.style,
            getattr(args, 'provider', None),
            getattr(args, 'model', None),
        )
    except ValueError as e:
        print(f"[ERROR] Error: {e}")
        print(f"[TIP] Tip: Run 'autodoc init' to configure your provider.")
        sys.exit(1)

    print(f"{'─'*70}\n")
    
    for i, filepath in enumerate(source_files, 1):
        print(f"[{i}/{len(source_files)}] Processing: {filepath}")
        process_file_with_treesitter(
            filepath=filepath,
            generator=generator,
            in_place=args.in_place,
            overwrite_existing=args.overwrite_existing,
            add_type_hints=hints_enabled,
            fix_magic_numbers=magic_enabled,
            docstrings_enabled=docstrings_enabled,
            dead_code=dead_code_enabled,
            dead_code_strict=dead_code_strict_enabled,
        )
        print(f"{'─'*70}\n")
    
    # Summary
    print(f"{'='*70}")
    print(f"  [OK] Processing Complete!")
    print(f"{'='*70}")
    print(f"\n📊 Summary:")
    print(f"  • Files processed: {len(source_files)}")
    print(f"  • Mode: {'Modified files' if args.in_place else 'Preview only'}")
    if not args.in_place:
        print(f"\n💡 To apply changes, add the --in-place flag")
    print(f"\n{'='*70}\n")


def main():
    """Main CLI entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        prog="autodoc",
        description="""
╔══════════════════════════════════════════════════════════════════════╗
║                   🤖 AutoDoc AI v0.1.4                               ║
║          AI-Powered Code Documentation & Enhancement Tool            ║
╚══════════════════════════════════════════════════════════════════════╝

AutoDoc AI automatically generates docstrings, adds type hints, and 
improves code quality using Large Language Models (LLMs).

Supports: Python, JavaScript, Java, Go, C++
        """,
        epilog="""
Examples:
  # First-time setup
  autodoc init

  # Add docstrings to a file (preview)
  autodoc run myfile.py --docstrings

  # Add type hints and save changes
  autodoc run . --add-type-hints --in-place

  # Full quality pass on changed files
  autodoc run . --diff --add-type-hints --overwrite-existing --in-place

For more help: https://github.com/paudelnirajan/autodoc
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="Available Commands",
        description="Choose a command to get started",
        help="Command description",
        required=True
    )

    # Init command
    parser_init = subparsers.add_parser(
        "init",
        help="Set up your LLM provider (Groq, OpenAI, Anthropic, Gemini)",
        description="Interactive wizard to configure your preferred AI provider and API key.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser_init.set_defaults(func=lambda args: init_config())

    # Run command
    config = load_config()
    parser_run = subparsers.add_parser(
        "run",
        help="Analyze and enhance your code with AI",
        description="""
Analyze source code files and apply AI-powered improvements:
  • Generate missing docstrings
  • Add type hints to functions
  • Improve existing documentation
  • Refactor poorly named variables/functions

By default, runs in preview mode. Use --in-place to save changes.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes for a single file
  autodoc run src/main.py

  # Add type hints to entire project
  autodoc run . --add-type-hints --in-place

  # Process only Git-changed files
  autodoc run . --diff --in-place

  # Use a specific provider
  autodoc run . --provider gemini --in-place
        """
    )
    
    parser_run.add_argument(
        "path",
        nargs='?',
        default='.',
        help="File or directory to process (default: current directory)"
    )
    
    parser_run.add_argument(
        "--diff",
        action="store_true",
        help="Only process files changed in Git (useful for pre-commit hooks)"
    )
    
    parser_run.add_argument(
        "--strategy",
        choices=["mock", "groq"],
        default=config.get('strategy', 'mock'),
        help="Use 'groq' for real LLM, 'mock' for testing without API calls"
    )
    
    parser_run.add_argument(
        "--style",
        choices=["google", "numpy", "rst"],
        default=config.get('style', 'google'),
        help="Docstring format style (google=Google-style, numpy=NumPy-style, rst=Sphinx)"
    )
    
    parser_run.add_argument(
        "--in-place",
        action="store_true",
        help="⚠️  Modify files directly (default: preview only)"
    )
    
    parser_run.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Regenerate poor-quality docstrings that already exist"
    )
    
    parser_run.add_argument(
        "--refactor",
        action="store_true",
        help="Umbrella flag: enable all non-strict features (docstrings, type hints, magic numbers, dead code). Does not imply --in-place."
    )
    parser_run.add_argument(
        "--refactor-strict",
        action="store_true",
        help="Umbrella flag: same as --refactor plus strict dead-code removal. Does not imply --in-place."
    )
    
    parser_run.add_argument(
        "--provider",
        choices=["groq", "openai", "anthropic", "gemini"],
        default=None,
        help="LLM provider to use (default: reads from .env AUTODOC_PROVIDER)"
    )
    
    parser_run.add_argument(
        "--model",
        default=None,
        metavar="MODEL_NAME",
        help="Override default model (e.g., gpt-4, claude-3-5-sonnet-latest, gemini-1.5-pro)"
    )
    
    parser_run.add_argument(
        "--docstrings",
        action="store_true",
        help="Generate missing docstrings (opt-in)"
    )

    parser_run.add_argument(
        "--add-type-hints",
        action="store_true",
        help="Generate and add Python type hints to functions (infers types from code)"
    )
    
    parser_run.add_argument(
        "--fix-magic-numbers",
        action="store_true",
        help="Replace magic numbers with named constants (e.g., 0.15 → TAX_RATE)"
    )

    parser_run.add_argument(
        "--dead-code",
        action="store_true",
        help="Report dead code (unused imports, never-called functions). Removes unused imports with --in-place"
    )

    parser_run.add_argument(
        "--dead-code-strict",
        action="store_true",
        help="Strict mode: also delete never-called private functions (e.g., _helper) when used with --in-place (Python only)"
    )

    parser_run.set_defaults(func=run_autodoc)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()