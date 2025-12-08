import argparse
import sys
import os
import getpass
from pathlib import Path
from textwrap import indent
import traceback
from autodoc_ai.transformers import CodeTransformer
from autodoc_ai.formatters import FormatterFactory
from autodoc_ai.generators import GeneratorFactory, IDocstringGenerator
from autodoc_ai.processors import (
    DeadCodeProcessor,
    DocstringProcessor,
    TypeHintProcessor,
    MagicNumberProcessor
)
from .utils import get_source_files, get_git_changed_files
from .config import load_config
from .parser import get_language_parser, get_language_queries, LANGUAGES
from .transformers import CodeTransformer
import textwrap
from .formatters import FormatterFactory

# Fix Windows Unicode encoding issues
if sys.platform.startswith("win"):
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
    except Exception:
        pass

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
    print("  [SETUP] Zenco AI - Initial Configuration Wizard")
    print("="*70)
    print("\nThis wizard will help you set up your preferred AI provider.")
    print("Your API key will be stored securely in a local .env file.\n")
    
    print("[INFO] Supported LLM Providers:")
    print("  1. Groq        - Fast inference, generous free tier")
    print("  2. OpenAI      - GPT-4, GPT-4o-mini (requires paid account)")
    print("  3. Anthropic   - Claude 3.5 Sonnet (requires paid account)")
    print("  4. Google      - Gemini Pro/Flash (free tier available)")
    
    provider_choice = input("\n[SELECT] Select your LLM provider (1-4) [default: 1]: ").strip() or "1"
    
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
    
    print(f"\n{'-'*70}")
    print(f"[CONFIG] Configuring {provider_name.upper()}")
    print(f"{'-'*70}")
    
    # Provider-specific instructions
    if provider_name == "groq":
        print("[INFO] Get your free API key at: https://console.groq.com/keys")
    elif provider_name == "openai":
        print("[INFO] Get your API key at: https://platform.openai.com/api-keys")
    elif provider_name == "anthropic":
        print("[INFO] Get your API key at: https://console.anthropic.com/")
    elif provider_name == "gemini":
        print("[INFO] Get your API key at: https://aistudio.google.com/app/apikey")
    
    api_key = getpass.getpass(f"\n[INPUT] Enter your {provider_name.upper()} API key (input hidden): ").strip()
    
    if not api_key:
        print("\n[ERROR] API key is required. Configuration cancelled.")
        return
    
    # Show confirmation with masked key (first 4 chars + asterisks)
    masked_key = api_key[:4] + "*" * (len(api_key) - 4) if len(api_key) > 4 else "*" * len(api_key)
    print(f"[CONFIRM] API key received: {masked_key}")
    
    model_name = input(f"[INPUT] Enter model name [default: {default_model}]: ").strip() or default_model
    
    keys_to_update = {
        api_key_var: api_key,
        model_var: model_name,
        "ZENCO_PROVIDER": provider_name,  # Store the selected provider
    }
    
    env_path = ".env"
    
    if os.path.exists(env_path):
        print(f"\n[UPDATE] Updating existing '{env_path}' file...")
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
        print(f"\n[CREATE] Creating new '{env_path}' file...")
        with open(env_path, "w") as f:
            for key, value in keys_to_update.items():
                f.write(f'{key}="{value}"\n')
                print(f"  ✓ Added {key}")
    
    print(f"\n{'='*70}")
    print(f"  [OK] Configuration Complete!")
    print(f"{'='*70}")
    print(f"\n[SUMMARY] Your Settings:")
    print(f"  • Provider: {provider_name.upper()}")
    print(f"  • Model: {model_name}")
    print(f"  • Config file: {env_path}")
    
    print(f"\n[NEXT] Next Steps:")
    print(f"  1. Test your setup:")
    print(f"     zenco run examples/test.py")
    print(f"\n  2. Add type hints to your code:")
    print(f"     zenco run . --add-type-hints --in-place")
    print(f"\n  3. Generate docstrings:")
    print(f"     zenco run src/ --in-place")
    
    print(f"\n[TIPS] Tips:")
    print(f"  • Use --help to see all available options")
    print(f"  • Change providers anytime: zenco run --provider <name>")
    print(f"  • Run 'zenco init' again to reconfigure")
    print(f"\n{'='*70}\n")


def process_file_with_treesitter(filepath: str, generator: IDocstringGenerator, in_place: bool, overwrite_existing: bool, add_type_hints: bool = False, fix_magic_numbers: bool = False, docstrings_enabled: bool = False, dead_code: bool = False, dead_code_strict: bool = False, json_mode: bool = False):
    """
    Processes a single file using the Tree-sitter engine to find and
    report undocumented functions, add type hints, and fix magic numbers.
    
    Returns:
        Dict[str, Any]: Processing results containing filepath, language, success status,
                       original/modified content, changes list, stats, and error info.
                       Returns None in non-JSON mode for backward compatibility.
    """
    
    # Initialize result structure for JSON mode
    result = {
        "filepath": filepath,
        "language": None,
        "success": False,
        "original_content": "",
        "modified_content": "",
        "changes": [],
        "stats": {
            "docstrings_added": 0,
            "type_hints_added": 0,
            "magic_numbers_fixed": 0,
            "dead_code_removed": 0
        },
        "error": None
    }

    lang = None
    if filepath.endswith('.py'): lang = 'python'
    elif filepath.endswith('.js'): lang = 'javascript'
    elif filepath.endswith('.java'): lang = 'java'
    elif filepath.endswith('.go'): lang = 'go'
    elif filepath.endswith('.cpp') or filepath.endswith('.hpp') or filepath.endswith('.h'): lang = 'cpp'

    result["language"] = lang

    parser = get_language_parser(lang)
    if not parser:
        if json_mode:
            result["error"] = f"No parser available for language: {lang}"
            return result
        return
    
    # Get the language object for Query constructor
    language = LANGUAGES.get(lang)
    if not language:
        if json_mode:
            result["error"] = f"Language not supported: {lang}"
            return result
        return

    try:
        with open(filepath, 'rb') as f:
            source_bytes = f.read()
    except IOError as e:
        error_msg = f"Error reading file: {e}"
        if json_mode:
            result["error"] = error_msg
            return result
        print(error_msg)
        return

    # Store original content
    result["original_content"] = source_bytes.decode('utf-8')

    tree = parser.parse(source_bytes)
    transformer = CodeTransformer(source_bytes)
    
    # ============================================================================
    # MODULAR PROCESSOR ARCHITECTURE - EXECUTION PRIORITY
    # ============================================================================
    # Process in optimal order:
    # 1. Dead code detection FIRST → get set of functions to skip
    # 2. Docstrings → only for live functions (saves LLM calls)
    # 3. Type hints → only for live functions
    # 4. Magic numbers → only for live functions
    # ============================================================================
    
    dead_function_names = set()
    
    # Context manager to suppress stdout in JSON mode
    from contextlib import contextmanager
    import sys
    import os

    @contextmanager
    def suppress_stdout():
        if json_mode:
            with open(os.devnull, "w") as devnull:
                old_stdout = sys.stdout
                sys.stdout = devnull
                try:
                    yield
                finally:
                    sys.stdout = old_stdout
        else:
            yield

    # Step 1: Detect dead code FIRST (execution priority optimization)
    if dead_code:
        try:
            with suppress_stdout():
                dead_processor = DeadCodeProcessor(lang, tree, source_bytes, transformer)
                dead_function_names = dead_processor.process(in_place=in_place, strict=dead_code_strict)
            
            if dead_function_names:
                result["stats"]["dead_code_removed"] = len(dead_function_names)
                for func_name in dead_function_names:
                    result["changes"].append({
                        "type": "dead_code",
                        "function": func_name,
                        "description": f"Removed dead function: {func_name}"
                    })
                if not json_mode:
                    print(f"  [PRIORITY] Found {len(dead_function_names)} dead functions to skip in other processors")
        except Exception as e:
            error_msg = f"Dead code detection failed: {e}"
            if not json_mode:
                print(f"  [WARN] {error_msg}")
                import traceback
                traceback.print_exc()
    
    # Step 2: Generate docstrings (skipping dead code)
    if docstrings_enabled:
        try:
            with suppress_stdout():
                docstring_processor = DocstringProcessor(lang, tree, source_bytes, transformer)
                docstring_changes = docstring_processor.process(
                    generator=generator,
                    overwrite_existing=overwrite_existing,
                    dead_functions=dead_function_names
                )
            
            if docstring_changes:
                result["changes"].extend(docstring_changes)
                result["stats"]["docstrings_added"] = len(docstring_changes)
                
        except Exception as e:
            error_msg = f"Docstring processing failed: {e}"
            if not json_mode:
                print(f"  [ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
    
    # Step 3: Add type hints (skipping dead code)
    if add_type_hints:
        try:
            with suppress_stdout():
                type_hint_processor = TypeHintProcessor(lang, tree, source_bytes, transformer)
                type_hint_changes = type_hint_processor.process(
                    generator=generator,
                    dead_functions=dead_function_names
                )
            
            if type_hint_changes:
                result["changes"].extend(type_hint_changes)
                result["stats"]["type_hints_added"] = len(type_hint_changes)
                
        except Exception as e:
            error_msg = f"Type hint processing failed: {e}"
            if not json_mode:
                print(f"  [ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
    
    # Step 4: Replace magic numbers (skipping dead code)
    if fix_magic_numbers:
        try:
            with suppress_stdout():
                magic_number_processor = MagicNumberProcessor(lang, tree, source_bytes, transformer)
                magic_changes = magic_number_processor.process(
                    generator=generator,
                    dead_functions=dead_function_names
                )
            
            if magic_changes:
                result["changes"].extend(magic_changes)
                result["stats"]["magic_numbers_fixed"] = len(magic_changes)
                
        except Exception as e:
            error_msg = f"Magic number processing failed: {e}"
            if not json_mode:
                print(f"  [ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
    
    # ============================================================================
    # Apply all transformations and save/preview
    # ============================================================================
    new_code = transformer.apply_changes()
    result["modified_content"] = new_code.decode('utf-8')
    result["success"] = True
    
    if in_place:
        if new_code != source_bytes:
            if not json_mode:
                print("\n  [SAVE] Saving changes to file...")
            try:
                with open(filepath, 'wb') as f:
                    f.write(new_code)
                if not json_mode:
                    print("  [OK] File updated successfully!")
            except IOError as e:
                error_msg = f"Error writing to file: {e}"
                if not json_mode:
                    print(f"  [ERROR] {error_msg}")
                result["error"] = error_msg
                result["success"] = False
        else:
            if not json_mode:
                print("\n  [INFO] No changes needed for this file.")
    else:
        # Print to console if not in_place and not in json_mode
        if not json_mode:
            print("\n  [PREVIEW] Preview of Changes (Dry Run):")
            print(f"  {'-'*66}\n")
            print(new_code.decode('utf8'))
    
    return result if json_mode else None



def run_autodoc(args):
    """The main entry point for running the analysis."""
    # Detect JSON mode early to suppress all non-JSON output
    json_mode = getattr(args, 'json', False)
    
    if not json_mode:
        if RICH_AVAILABLE:
            console = Console()
            console.print(Panel.fit("Zenco AI - Code Analysis & Enhancement", 
                                   border_style="blue", padding=(1, 2)))
        else:
            cprint(f"\n{'='*70}", 'cyan')
            cprint(f"  Zenco AI - Code Analysis & Enhancement", 'blue', 'bold')
            cprint(f"{'='*70}\n", 'cyan')
    
    # Check if this is first-time use and show helpful setup message
    dotenv_path = Path(os.getcwd()) / '.env'
    
    # Load environment variables from .env if it exists
    if dotenv_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
    
    # Check if any API keys are configured
    has_api_keys = any([
        os.getenv("GROQ_API_KEY"),
        os.getenv("OPENAI_API_KEY"), 
        os.getenv("ANTHROPIC_API_KEY"),
        os.getenv("GEMINI_API_KEY")
    ])
    
    if not json_mode and (not dotenv_path.exists() or not has_api_keys):
        cprint("First time using Zenco? Run 'zenco init' to set up your AI provider!", 'yellow', 'bold')
        cprint("   This will configure your API key and enable real AI-powered analysis.\n", 'yellow')
    
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
    
    # Strict mode implies enabled
    if dead_code_strict_enabled:
        dead_code_enabled = True

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
    if not json_mode:
        if refactor_enabled or refactor_strict_enabled:
            # Print umbrella banner explicitly listing what refactor mode enables
            umbrella = ["Docstrings", "Type Hints", "Magic Numbers", "Dead Code"]
            if refactor_strict_enabled:
                umbrella.append("Strict Dead Code")
            cprint(f"[REFACTOR] Refactor mode enabled -> {', '.join(umbrella)}", 'green')

    if not any([docstrings_enabled, hints_enabled, magic_enabled, dead_code_enabled]):
        if not json_mode:
            cprint("[WARN]  No features selected. Use one or more of: --docstrings, --overwrite-existing, --add-type-hints, --fix-magic-numbers, --dead-code, --dead-code-strict, --refactor, --refactor-strict", 'yellow')
        return
    
    if not json_mode:
        print(f"[FEATURES] Active Features: {', '.join(features)}")
        print(f"[STYLE] Docstring Style: {args.style}")
    
    if args.diff:
        if not json_mode:
            print(f"[MODE] Git-changed files only\n")
            print("Scanning for modified files...")
        source_files = get_git_changed_files()
        if source_files is None: 
            if not json_mode:
                print("[ERROR] Error: Not a git repository or no changes found.")
            sys.exit(1)
    else:
        if not json_mode:
            print(f"[TARGET] Target: {args.path}\n")
            print("Scanning for source files...")
        source_files = get_source_files(args.path)
    
    if not source_files:
        if not json_mode:
            print("\n[WARN]  No source files found to process.")
            print("[TIP] Tip: Make sure you're in the right directory or specify a path.")
        return

    if not json_mode:
        print(f"[OK] Found {len(source_files)} file(s) to process.\n")
    
    # Show provider info
    if not json_mode:
        provider = getattr(args, 'provider', None) or os.getenv('ZENCO_PROVIDER', 'groq')
        model = getattr(args, 'model', None)
        if args.strategy != 'mock':
            print(f"[AI] Using: {provider.upper()}" + (f" ({model})" if model else ""))
            if not args.in_place:
                print(f"  Mode: Dry-run (preview only - use --in-place to save changes)")
            else:
                print(f"  Mode: In-place (files will be modified)")
            print()
    
    try:
        generator = GeneratorFactory.create_generator(
            args.strategy,
            args.style,
            getattr(args, 'provider', None),
            getattr(args, 'model', None),
        )
    except ValueError as e:
        if not json_mode:
            print(f"[ERROR] Error: {e}")
            print(f"[TIP] Tip: Run 'zenco init' to configure your provider.")
        sys.exit(1)

    if not json_mode:
        print(f"{'-'*70}\n")
    
    # Detect JSON mode
    json_mode = getattr(args, 'json', False)
    
    if json_mode:
        # Import JSONOutput for JSON mode
        from autodoc_ai.json_output import JSONOutput
        json_output = JSONOutput()
        
        # Process files and collect results
        for i, filepath in enumerate(source_files, 1):
            try:
                result = process_file_with_treesitter(
                    filepath=filepath,
                    generator=generator,
                    in_place=args.in_place,
                    overwrite_existing=args.overwrite_existing,
                    add_type_hints=hints_enabled,
                    fix_magic_numbers=magic_enabled,
                    docstrings_enabled=docstrings_enabled,
                    dead_code=dead_code_enabled,
                    dead_code_strict=dead_code_strict_enabled,
                    json_mode=True
                )
                
                # Add result to JSON output
                json_output.add_file_result(
                    filepath=result["filepath"],
                    language=result["language"],
                    success=result["success"],
                    original_content=result["original_content"],
                    modified_content=result["modified_content"],
                    changes=result["changes"],
                    stats=result["stats"],
                    error=result.get("error")
                )
            except Exception as e:
                # Handle unexpected errors
                json_output.add_error(
                    error_type="ProcessingError",
                    message=str(e),
                    file=filepath
                )
        
        # Output JSON results
        json_output.output(mode="refactor", in_place=args.in_place)
    else:
        # Normal text output mode
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
                json_mode=False
            )
            print(f"{'-'*70}\n")
        
        # Summary (only in text mode)
        print(f"{'='*70}")
        print(f"  [OK] Processing Complete!")
        print(f"{'='*70}")
        print(f"\nSummary:")
        print(f"  * Files processed: {len(source_files)}")
        print(f"  * Mode: {'Modified files' if args.in_place else 'Preview only'}")
        if not args.in_place:
            print(f"\nTo apply changes, add the --in-place flag")
        print(f"\n{'='*70}\n")


def main():
    """Main CLI entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        prog="zenco",
        description="""
Zenco AI v1.2.0

Zenco AI automatically generates docstrings, adds type hints, and 
improves code quality using Large Language Models (LLMs).

Supports: Python, JavaScript, Java, Go, C++
        """,
        epilog="""
Examples:
  # First-time setup
  zenco init

  # Add docstrings to a file (preview)
  zenco run myfile.py --docstrings

  # Add type hints and save changes
  zenco run . --add-type-hints --in-place

  # Full quality pass on changed files
  zenco run . --diff --add-type-hints --overwrite-existing --in-place

For more help: https://github.com/paudelnirajan/zenco
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
  * Generate missing docstrings
  * Add type hints to functions
  * Improve existing documentation
  * Refactor poorly named variables/functions

By default, runs in preview mode. Use --in-place to save changes.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes for a single file
  zenco run src/main.py

  # Add type hints to entire project
  zenco run . --add-type-hints --in-place

  # Process only Git-changed files
  zenco run . --diff --in-place

  # Use a specific provider
  zenco run . --provider gemini --in-place
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
        choices=["mock", "llm"],
        default=config.get('strategy', 'mock'),
        help="Use 'llm' for real LLM (auto-detects provider), 'mock' for testing without API calls"
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
        help="Modify files directly (default: preview only)"
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
        help="LLM provider to use (default: reads from .env ZENCO_PROVIDER)"
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

    parser_run.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format (for programmatic use)"
    )

    parser_run.set_defaults(func=run_autodoc)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()