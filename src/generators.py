import abc
import ast
import os
from dotenv import load_dotenv
from src.llm_services import ILLMService, GroqAdapter

class IDocStringGenerator(abc.ABC):
    """
    An interface for different docstring generation and evaluation  strategies.
    """
    @abc.abstractmethod
    def generate(self, node: ast.AST) -> str:
        """
        Generates a docstring for the given AST node.

        :param node: The AST node e.g., FunctionDef, ClassDef) to document.
        :return: The generated docstring as a string
        """
        pass

    @abc.abstractmethod
    def evaluate(self, node: ast.AST, docstring: str) -> bool:
        """
        Evaluates if a docstring is of high quality for a given AST node.

        :param node: The AST node (e.g., FunctionDef, ClassDef).
        :param docstring: The existing docstring to evaluate.
        :return: True if the docstring is deemed good, False otherwise.
        """
        pass

    @abc.abstractmethod
    def suggest_variable_name(self, node: ast.FunctionDef, old_name: str) -> str | None:
        """Suggests a better name for a variable within the context of a function."""
        pass

    @abc.abstractmethod
    def suggest_function_name(self, node: ast.FunctionDef, old_name: str) -> str | None:
        """Suggests a better name for a function or method."""
        pass

    @abc.abstractmethod
    def evaluate_name(self, node: ast.AST, name: str) -> bool:
        """Evaluates if a name is of high quality for a given AST node."""
        pass


class MockGenerator(IDocStringGenerator):
    """
    A mock generator that returns a placeholder docstring.
    This is used for testing the AST modification pipeline without making the real API calls.
    """
    def generate(self, node: ast.AST) -> str:
        return "This is a mock docstring."
    
    def evaluate(self, node: ast.AST, docstring: str) -> bool:
        return True

    def suggest_variable_name(self, node: ast.FunctionDef, old_name: str) -> str | None:
        return f"mock_name_for_{old_name}"

    def suggest_function_name(self, node: ast.FunctionDef, old_name: str) -> str | None:
        return f"mock_function_name_for_{old_name}"

    def evaluate_name(self, node: ast.AST, name: str) -> bool:
        return len(name) > 3


class LLMGenerator(IDocStringGenerator):
    """
    A generator that uses an LLM service (via ILLMService adapter) to create and evaluate docstrings.
    """
    def __init__(self, llm_service: ILLMService, style: str = "google"):
        self.llm_service = llm_service
        self.style = style

    def generate(self, node: ast.AST) -> str:
        code_snippet = ast.unparse(node)
        prompt = f"""
        Generate a professional, **{self.style}-style docstring** for the following Python code.
        Only return the docstring itself, without any introductory text like "Here is the docstring:".
        The docstring should be enclosed in triple quotes.
        ```python
        {code_snippet}
        ```
        """

        raw_docstring = self.llm_service.create_completion(prompt)

        if raw_docstring.startswith('"""') and raw_docstring.endswith('"""'):
            return raw_docstring[3:-3].strip()
        
        return raw_docstring.strip()

    def evaluate(self, node: ast.AST, docstring: str) -> bool:
        """
        Delegates the evaluation task to the injected ILLMService (e.g., GroqAdapter).
        """
        code_snippet = ast.unparse(node)
        return self.llm_service.evaluate_docstring(code_snippet, docstring)

    def suggest_variable_name(self, node: ast.FunctionDef, old_name: str) -> str | None:
        code_context = ast.unparse(node)
        return self.llm_service.suggest_name(code_context, old_name)

    def suggest_function_name(self, node: ast.FunctionDef, old_name: str) -> str | None:
        code_context = ast.unparse(node)
        return self.llm_service.suggest_function_name(code_context, old_name)

    def evaluate_name(self, node: ast.AST, name: str) -> bool:
        code_context = ast.unparse(node)
        return self.llm_service.evaluate_name(code_context, name)


class GeneratorFactory:
    """
    A factory to create the appropriate docstring generator based on a strategy name.
    """
    @staticmethod
    def create_generator(strategy: str, style: str = "google") -> IDocStringGenerator:
        if strategy == "mock":
            return MockGenerator()
        
        if strategy == "groq":
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in .env file.")

            model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
            
            groq_adapter = GroqAdapter(api_key=api_key, model=model_name)
            return LLMGenerator(llm_service=groq_adapter, style=style)
        raise ValueError(f"Unknown generator strategy: {strategy}")