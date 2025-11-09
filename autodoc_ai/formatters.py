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

class JSDocFormatter(IDocstringFormatter):
    """Formats docstrings for Javascript/TypeScript."""
    def format(self, docstring: str, indentation: str):
        lines = docstring.strip().split('\n')
        jsdoc_lines = [f"{indentation} * {line}" for line in lines]
        jsdoc_content = '\n'.join(jsdoc_lines)
        return f"{indentation}/**\n{jsdoc_content}\n{indentation} */ \n"

class FormatterFactory:
    """A factory to create the appropriate docstring formatter."""
    @staticmethod
    def create_formatter(language: str) -> IDocstringFormatter:
        if language == "python":
            return PythonFormatter()

        if language == "javascript":
            return JSDocFormatter()
        
        return PythonFormatter()
