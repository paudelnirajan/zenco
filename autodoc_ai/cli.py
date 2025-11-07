import ast
import argparse
import sys
import os
import subprocess
from .ast_handler import CodeQualityVisitor
from .generators import GeneratorFactory, IDocstringGenerator
from .utils import get_python_files, get_git_changed_files
from .config import load_config

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

def process_file(filepath: str, in_place: bool, strategy: str, overwrite_existing: bool, style: str, refactor: bool):
    """Processes a single Python file for documentation and formatting."""
    print(f"--- Processing {filepath} ---")

    if in_place:
        print("Running 'black' formatter as a pre-processing step...")
        try:
            subprocess.run(["black", filepath], check=True, capture_output=True)
        except FileNotFoundError:
            print("Warning: 'black' command not found. Cannot pre-format file.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: 'black' failed to format the file, it may have severe syntax errors. Error: {e.stderr.decode()}")

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            source_code = file.read()
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"Error reading file: {e}")
        return

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(f"Error parsing AST: {e}")
        return

    generator: IDocstringGenerator = GeneratorFactory.create_generator(
        strategy=strategy, style=style
    )
    
    visitor = CodeQualityVisitor(
        generator=generator, 
        overwrite_existing=overwrite_existing,
        refactor=refactor
    )
    visitor.visit(tree)

    if visitor.tree_modified:
        new_code = ast.unparse(tree)
        
        if in_place:
            print(f"Writing changes back to {filepath}...")
            try:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_code)
                
                print("Running 'black' formatter for final cleanup...")
                subprocess.run(["black", filepath], check=True, capture_output=True, text=True)
                print("Formatting complete.")

            except IOError as e:
                print(f"Error writing to file: {e}")
        else:
            print("\nModified code (use --in-place to save):")
            try:
                formatted_code = subprocess.check_output(["black", "-"], input=new_code, text=True)
                print("-" * 40)
                print(formatted_code)
                print("-" * 40)
            except (FileNotFoundError, subprocess.CalledProcessError):
                 print("-" * 40)
                 print(new_code) 
                 print("-" * 40)
    else:
        print("No modifications made.")



def run_autodoc(args):
    """The main entry point for running the analysis and refactoring."""
    if args.diff:
        print("Processing files with git changes...")
        python_files = get_git_changed_files()
        if python_files is None: sys.exit(1)
    else:
        python_files = get_python_files(args.path)
    
    if not python_files:
        print("No Python files found to process.")
        return

    print(f"Found {len(python_files)} Python file(s) to process.")
    
    for filepath in python_files:
        process_file(
            filepath=filepath,
            in_place=args.in_place,
            strategy=args.strategy,
            overwrite_existing=args.overwrite_existing,
            style=args.style,
            refactor=args.refactor
        )
        print("-" * 50)


def main():
    """Main CLI entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        description="AutoDoc AI: An AI-powered tool to document, refactor, and format Python code.",
        epilog="For detailed help on a command, run: 'autodoc <command> --help' (e.g., 'autodoc run --help')"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    parser_init = subparsers.add_parser("init", help="Initialize AutoDoc configuration (create .env file).")
    parser_init.set_defaults(func=lambda args: init_config())

    config = load_config()
    parser_run = subparsers.add_parser("run", help="Analyze and process Python files.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser_run.add_argument("path", nargs='?', default='.', help="Path to process (file or directory).")
    parser_run.add_argument("--diff", action="store_true", help="Only process files with git changes.")
    parser_run.add_argument("--strategy", choices=["mock", "groq"], default=config['strategy'], help="Docstring generation strategy.")
    parser_run.add_argument("--style", choices=["google", "numpy", "rst"], default=config['style'], help="Docstring style to enforce.")
    parser_run.add_argument("--in-place", action="store_true", help="Modify files in place.")
    
    overwrite_default = config.get('overwrite_existing', False)
    refactor_default = config.get('refactor', False)
    parser_run.add_argument("--overwrite-existing", action="store_true", default=overwrite_default, help="Regenerate poor-quality docstrings.")
    parser_run.add_argument("--refactor", action="store_true", default=refactor_default, help="Enable AI-powered refactoring.")
    parser_run.set_defaults(func=run_autodoc)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()