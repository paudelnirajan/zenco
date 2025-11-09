import abc
from textwrap import indent

class IDocstringFormatter(abc.ABC):
    """An interface for language-specific docstring formatters."""
    @abc.abstractmethod
    def format(self, docstring: str, indentation: str) -> str:
        pass

class PythonFormatter(IDocstringFormatter):
    """Formats docstrings for Python."""
    def format(self, docstring: str, indentation: str) -> str:
        indented_content = indent(docstring.strip(), indentation)
        return f'{indentation}"""\n{indented_content}\n{indentation}"""\n'

class CStyleDocFormatter(IDocstringFormatter): 
    """Formats docstrings for C-style languages (Java, JS, C++, etc.)."""
    def format(self, docstring: str, indentation: str) -> str:
        lines = docstring.strip().split('\n')
        doc_lines = [f"{indentation} * {line}" for line in lines]
        content = '\n'.join(doc_lines)
        return f"{indentation}/**\n{content}\n{indentation} */\n"

class GoFormatter(IDocstringFormatter):
    """Formats docstrings for Go."""
    def format(self, docstring: str, indentation: str) -> str:
        lines = docstring.strip().split('\n')
        go_lines = [f"{indentation}// {line}" for line in lines]
        return '\n'.join(go_lines) + '\n'

class FormatterFactory:
    """A factory to create the appropriate docstring formatter."""
    @staticmethod
    def create_formatter(language: str) -> IDocstringFormatter:
        if language == "python":
            return PythonFormatter()

        if language in ['javascript', 'java', 'c', 'cpp', 'go']:
            return CStyleDocFormatter()
        
        return PythonFormatter()
