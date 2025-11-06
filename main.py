import ast
import argparse
import sys
from src.ast_handler import CodeQualityVisitor
from src.generators import GeneratorFactory, IDocStringGenerator
from src.utils import get_python_files, get_get_changed_files
from src.config import load_config

def process_file(filepath: str, in_place: bool, strategy: str, overwrite_existing: bool, style: str, refactor: bool):
    """
    Process a single Python file for documentation
    """
    print(f"--- Processing {filepath} ---")
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

    generator: IDocStringGenerator = GeneratorFactory.create_generator(
        strategy=strategy, style=style
    )
    
    visitor = CodeQualityVisitor(
        generator=generator, 
        overwrite_existing=overwrite_existing,
        refactor=refactor,
    )
    visitor.visit(tree)

    if visitor.tree_modified:
        new_code = ast.unparse(tree)
        
        if in_place:
            print(f"Writing changes back to {filepath}...")
            try:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_code)
            except IOError as e:
                print(f"Error writing to file: {e}")
        else:
            print("\nModified code (use --in-place to save):")
            print("-" * 40)
            print(new_code)
            print("-" * 40)
    else:
        print("No modifications made.")


def main():
    """Main entry point for the AutoDoc CLI."""

    config = load_config()

    parser = argparse.ArgumentParser(
        description="Analyzes and automatically documents Python files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path", nargs='?', default='.', help="Path to process (file or directory).")
    parser.add_argument("--diff", action="store_true", help="Only process files with git changes.")
    parser.add_argument("--strategy", choices=["mock", "groq"], default=config['strategy'], help="Docstring generation strategy.")
    parser.add_argument("--style", choices=["google", "numpy", "rst"], default=config['style'], help="Docstring style to enforce.")
    parser.add_argument("--in-place", action="store_true", help="Modify files in place.")

    overwrite_default = config.get('overwrite_existing', False)
    refactor_default = config.get('refactor', False)
    parser.add_argument("--overwrite-existing", action="store_true", default=overwrite_default, help="Regenerate poor-quality docstrings.")
    parser.add_argument("--refactor", action="store_true", default=refactor_default, help="Enable AI-powered refactoring (e.g., variable renaming).")
    
    args = parser.parse_args()

    if args.diff:
        print("Processing files with git changes...")
        python_files = get_get_changed_files()
        if python_files is None:
            sys.exit(1)
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

if __name__ == "__main__":
    main()