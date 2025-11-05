# AutoDoc: AI-Powered Code Documentation Generator

## Project Overview

**AutoDoc** is a command-line utility designed to help developers maintain high-quality documentation in their Python projects. It automatically analyzes existing source code, identifies undocumented functions and classes, and uses a Large Language Model (LLM) to generate or validate necessary docstrings.

This tool ensures code completeness, reduces documentation debt, and allows developers to focus on writing code, not comments.

## Features

  * **Intelligent Docstring Insertion:** Scans Python files, finds missing docstrings for functions and classes, and injects high-quality, generated documentation directly into the Abstract Syntax Tree (AST).
  * **Docstring Evaluation:** Uses a well-crafted LLM prompt to evaluate existing docstrings. If a docstring is found to be low-quality (e.g., a "TODO" placeholder or too generic), the tool can flag it or automatically replace it with a superior generated version.
  * **Pluggable AI Backend:** The architecture is designed to easily swap between different LLM providers (e.g., Groq, OpenAI) or even run in a placeholder **Mock** mode for rapid local testing.
  * **Non-Destructive AST Modification:** Safely modifies the code structure at the tree level, ensuring the resulting code is syntactically correct and properly formatted.

## Technology Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Language** | **Python 3.9+** | Core development language. |
| **AST Parsing** | **`ast`** (Built-in) | Used for reading source code into an Abstract Syntax Tree. |
| **Code Rewrite** | **`ast.unparse`** / `astor` (Optional) | Converts the modified AST back into source code. |
| **AI Backend** | **Groq SDK** | Primary LLM provider for fast, real-time generation and evaluation. |
| **Dependency Management**| **`dotenv`** | Manages API keys and configuration settings. |

## Getting Started

### Prerequisites

1.  Python 3.9 or higher.
2.  A Groq API key (or equivalent for a different LLM service).

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/paudelnirajan/autodoc
    cd autodoc
    ```
2.  Set up a virtual environment and install dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  Create a file named `.env` in the project root and add your API key:
    ```
    # .env
    GROQ_API_KEY="sk-..."
    GROQ_MODEL_NAME="llama-3.3-70b-versatile" # Optional, defaults to this model
    ```

### Usage

Run the tool from the command line, specifying the file you wish to document and the strategy to use:

```bash
# Preview changes (dry run) using the LLM strategy
python3 main.py --file=path/to/my_script.py --strategy=groq

# Apply changes to the file using the LLM strategy
python3 main.py --file=path/to/my_script.py --strategy=groq --write

# Run in mock mode to test the AST modification without API calls
python3 main.py --file=path/to/my_script.py --strategy=mock --write
```
