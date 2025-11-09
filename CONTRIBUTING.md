# Contributing to Zenco

🎉 **Thank you for your interest in contributing to Zenco!** 

We welcome contributions of all types, from bug fixes to new features. This guide will help you get started.

---

## 🚀 Quick Start

### For Quick Contributions:
1. **Fork** this repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Make** your changes
4. **Test** thoroughly: `pytest tests/ -v`
5. **Commit** and push to your fork
6. **Create** a Pull Request

---

## 🛠️ Development Setup

### Prerequisites:
- Python 3.9+
- Git
- GitHub account

### Local Setup:
```bash
# Clone your fork
git clone https://github.com/paudelnirajan/zenco.git
cd zenco

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black isort flake8 mypy

# Run tests to verify setup
pytest tests/ -v
```

---

## 📋 How to Contribute

### 🐛 Reporting Bugs

1. **Check existing issues** first
2. **Use the bug report template**:
   - Python version and OS
   - Zenco version
   - Steps to reproduce
   - Expected vs actual behavior
   - Sample code if applicable

### ✨ Requesting Features

1. **Check existing feature requests**
2. **Use the feature request template**:
   - Problem description
   - Proposed solution
   - Alternative approaches
   - Use case examples

### 🔧 Code Contributions

#### Areas Where We Need Help:

- **🌐 New Language Support**: Rust, TypeScript, PHP, etc.
- **🔄 Refactoring Features**: Variable/function renaming
- **📝 Documentation**: Examples, tutorials, API docs
- **🧪 Testing**: More comprehensive test coverage
- **🎨 UI/UX**: Better terminal output, progress indicators

#### Development Workflow:

1. **Choose an issue** or create your own
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make changes** following our coding standards
4. **Test your changes**:
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Check code formatting
   black --check autodoc_ai/
   isort --check-only autodoc_ai/
   
   # Run linting
   flake8 autodoc_ai/
   ```
5. **Update documentation** if needed
6. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add TypeScript support"
   git commit -m "fix: resolve magic number detection in Go"
   ```
7. **Push and create PR** with detailed description

---

## 📏 Coding Standards

### Python Code Style:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **Type hints** where appropriate
- **Docstrings** using Google style

### Example Function:
```python
def process_code(file_path: str, options: dict) -> str:
    """Process a source code file with given options.
    
    Args:
        file_path: Path to the source file.
        options: Dictionary of processing options.
        
    Returns:
        Processed code as string.
        
    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    # Implementation here
    pass
```

### Git Commit Messages:
Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for refactoring
- `chore:` for maintenance

---

## 🧪 Testing Guidelines

### Running Tests:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=autodoc_ai --cov-report=html

# Run specific test file
pytest tests/test_basic.py -v
```

### Writing Tests:
- **Test files** go in [tests/](cci:7://file:///Users/nirajanpaudel17/Documents/Projects/AutoDoc/tests:0:0-0:0) directory
- **Test functions** should be descriptive: `test_parser_creates_ast()`
- **Use fixtures** for setup/teardown
- **Mock external dependencies** (LLM APIs)

### Example Test:
```python
def test_python_parser_creation():
    """Test that Python parser can be created successfully."""
    parser = get_language_parser('python')
    assert parser is not None
    
    code = b"def hello(): return 'world'"
    tree = parser.parse(code)
    assert tree.root_node is not None
```

---

## 🌳 Multi-Language Support

### Adding New Languages:

1. **Install tree-sitter grammar**:
   ```bash
   pip install tree-sitter-rust
   ```

2. **Add to `parser.py`**:
   ```python
   from tree_sitter_rust import language as rust_language
   
   LANGUAGES['rust'] = Language(rust_language())
   ```

3. **Add queries** for the new language
4. **Update `cli.py`** processing logic
5. **Add tests** for the new language
6. **Update documentation**

### Language-Specific Features:

- **Python**: Type hints, docstrings, AST analysis
- **JavaScript**: JSDoc, ES6+ syntax, TypeScript support
- **Java**: Javadoc, import cleanup, annotation processing
- **Go**: godoc, interface generation, go fmt integration
- **C++**: Doxygen, header processing, clang-format integration

---

## 📚 Documentation

### Types of Documentation:

- **Code documentation**: Docstrings, comments
- **User documentation**: README, examples, tutorials
- **API documentation**: Function signatures, usage examples
- **Development documentation**: Architecture, design decisions

### Documentation Standards:
- **Google style** docstrings for Python
- **JSDoc** for JavaScript
- **Javadoc** for Java
- **godoc** for Go
- **Doxygen** for C++

---

## 🔄 Pull Request Process

### Before Submitting:
1. **Ensure all tests pass**: `pytest tests/ -v`
2. **Check code formatting**: `black --check autodoc_ai/`
3. **Update documentation** if needed
4. **Rebase** on latest main: `git rebase origin/main`

### PR Template:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process:
1. **Automated checks** run (tests, linting)
2. **Code review** by maintainers
3. **Feedback and revisions** as needed
4. **Approval and merge** to main

---

## 🏗️ Project Architecture

### Core Components:

- **`cli.py`**: Command-line interface and main logic
- **`parser.py`**: Tree-sitter language parsers
- **`generators.py`**: LLM service adapters
- **[transformers.py](cci:7://file:///Users/nirajanpaudel17/Documents/Projects/AutoDoc/autodoc_ai/transformers.py:0:0-0:0)**: Code transformation utilities
- **`utils.py`**: Helper functions and file operations
- **`formatters.py`**: Code formatting logic

### Design Patterns:
- **Strategy Pattern**: LLM provider selection
- **Factory Pattern**: Generator creation
- **Visitor Pattern**: AST traversal
- **Adapter Pattern**: LLM API integration

---

## 🤝 Community Guidelines

### Code of Conduct:
- **Be respectful** and inclusive 
- **Focus on constructive feedback**
- **Assume good intentions**

### Getting Help:
- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Documentation**: Check existing docs first

---

## 🎉 Recognition

### Contributors:
All contributors are recognized in:
- **README.md**: Contributors section
- **Release notes**: For each release
- **GitHub contributors**: Automatic recognition

### Ways to Contribute:
- **Code**: New features, bug fixes
- **Documentation**: Improving docs, examples
- **Testing**: Writing tests, reporting bugs
- **Design**: UI/UX improvements
- **Community**: Answering questions, reviewing PRs

---

## 📞 Getting Started

### First Contribution Ideas:
1. **Fix a typo** in documentation
2. **Add a test case** for existing functionality
3. **Improve error messages**
4. **Add an example** to the examples folder
5. **Report a bug** with detailed reproduction steps

### Questions?
- **Check existing issues** first
- **Create a new issue** for questions
- **Join discussions** for ideas and feedback

---

## 📜 License

By contributing to Zenco, you agree that your contributions will be licensed under the **MIT License**.

---

**🚀 Ready to contribute? Pick an issue and start coding!**

Thank you for helping make Zenco better! 🙏
