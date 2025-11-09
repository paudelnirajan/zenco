# Zenco

[![PyPI version](https://badge.fury.io/py/zenco.svg)](https://badge.fury.io/py/zenco)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Zenco** is an AI-powered code analysis and enhancement tool that supports multiple programming languages. It automatically generates docstrings, adds type hints, detects magic numbers, removes dead code, and provides intelligent refactoring suggestions using Large Language Models (LLMs).

This project was built on a foundation of solid Object-Oriented Programming principles and design patterns, including the Visitor, Strategy, Factory, and Adapter patterns.

---

## Core Features

### Multi-Language Support
*   **Python, JavaScript, Java, Go, C++** - Full support across major programming languages
*   **Tree-sitter powered** - Fast, accurate parsing for all supported languages

### AI-Powered Code Enhancement
*   **Docstring Generation:** Context-aware docstrings for functions and classes
*   **Type Hint Addition:** Intelligent type annotations for Python functions
*   **Magic Number Detection:** Identifies and replaces numeric literals with named constants
*   **Dead Code Removal:** Detects and removes unused imports, variables, and functions
*   **Strict Mode:** Advanced cleanup including unused local variables and private methods

### Developer Experience
*   **Multiple LLM Providers:** Support for Groq, OpenAI, Anthropic, and Google Gemini
*   **Colorful Terminal Output:** Rich, beautiful command-line interface
*   **Umbrella Commands:** `--refactor` and `--refactor-strict` for comprehensive code improvement
*   **Git Integration:** Process only changed files with `--diff`
*   **Safe Preview Mode:** See changes before applying with dry-run by default

## Installation

Install Zenco directly from PyPI:

```bash
pip install zenco
```

## Quick Start

1. **Initialize your project:**
```bash
zenco init
```
This interactive wizard helps you configure your preferred AI provider (Groq, OpenAI, Anthropic, or Gemini).

2. **Preview changes on a file:**
```bash
zenco run myfile.py --refactor
```

3. **Apply comprehensive improvements:**
```bash
zenco run . --refactor-strict --in-place
```

## Configuration

Zenco uses a `.env` file for secrets and a `pyproject.toml` file for project-wide settings.

### 1. API Credentials (`.env`)

The `zenco init` command will create this for you. Example:

```env
GROQ_API_KEY="gsk_YourActualGroqApiKeyHere"
GROQ_MODEL_NAME="llama3-8b-8192"
AUTODOC_PROVIDER="groq"
```

## Usage Examples

### Basic Commands
```bash
# Get help
zenco --help
zenco run --help

# Preview changes (dry run)
zenco run myfile.py --docstrings
zenco run . --refactor

# Apply changes
zenco run myfile.py --docstrings --in-place
zenco run . --refactor-strict --in-place
```

### Feature-Specific Usage
```bash
# Add type hints to Python files
zenco run . --add-type-hints --in-place

# Fix magic numbers across languages
zenco run . --fix-magic-numbers --in-place

# Remove dead code (safe mode)
zenco run . --dead-code --in-place

# Remove dead code (strict mode - includes locals)
zenco run . --dead-code --dead-code-strict --in-place

# Process only Git-changed files
zenco run . --diff --refactor --in-place
```

### Umbrella Commands
```bash
# Safe refactor: docstrings + type hints + magic numbers + dead code
zenco run . --refactor --in-place

# Strict refactor: includes unused local variables and private methods
zenco run . --refactor-strict --in-place
```

## How It Works

Zenco uses a "Tree-sitter + AI" architecture for fast, accurate multi-language support:

1.  **Tree-sitter Parsing:** Fast, incremental parsing for Python, JavaScript, Java, Go, and C++
2.  **Pattern Detection:** Identifies missing docstrings, magic numbers, unused code, and type annotation opportunities
3.  **AI Enhancement:** Sends relevant code context to your chosen LLM for intelligent suggestions
4.  **Safe Transformation:** Applies changes using precise byte-level edits with the CodeTransformer
5.  **Multi-Provider Support:** Works with Groq, OpenAI, Anthropic, and Google Gemini APIs

## License

This project is licensed under the MIT License.