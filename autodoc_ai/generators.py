import abc
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tree_sitter import Node
from .llm_services import ILLMService, GroqAdapter

class IDocstringGenerator(abc.ABC):
    """An interface for AI strategies using Tree-sitter."""
    @abc.abstractmethod
    def generate(self, node: Node) -> str:
        """Generates a docstring for a given Tree-sitter node."""
        pass

    @abc.abstractmethod
    def evaluate(self, node: Node, docstring: str) -> bool:
        """Evaluates if a docstring is high quality."""
        pass

    @abc.abstractmethod
    def suggest_name(self, node: Node, old_name: str) -> str | None:
        """Suggests a better name for any given node."""
        pass


class MockGenerator(IDocstringGenerator):
    """A mock generator for testing."""
    def generate(self, node: Node) -> str:
        return "This is a mock docstring."

    def evaluate(self, node: Node, docstring: str) -> bool:
        return len(docstring) > 20

    def suggest_name(self, node: Node, old_name: str) -> str | None:
        return f"mock_name_for_{old_name}"


class LLMGenerator(IDocstringGenerator):
    """A generator that uses an LLM service."""
    def __init__(self, llm_service: ILLMService, style: str = "google"):
        self.llm_service = llm_service
        self.style = style

    def generate(self, node: Node) -> str:
        code_snippet = node.text.decode('utf8')
        prompt = f"""
        Generate a professional, {self.style}-style docstring for the following code.
        Only return the raw content of the docstring, without the triple quotes.
        Code:
        {code_snippet}
        """
        raw_docstring = self.llm_service.create_completion(prompt)
        return raw_docstring.strip()

    def evaluate(self, node: Node, docstring: str) -> bool:
        code_snippet = node.text.decode('utf8')
        return self.llm_service.evaluate_docstring(code_snippet, docstring)

    def suggest_name(self, node: Node, old_name: str) -> str | None:
        code_context = node.text.decode('utf8')

        if node.type in ['function_definition', 'function_declaration']:
            return self.llm_service.suggest_function_name(code_context, old_name)
        elif node.type in ['class_definition', 'class_declaration']:
            return self.llm_service.suggest_class_name(code_context, old_name)
        else:
            return self.llm_service.suggest_name(code_context, old_name)


class GeneratorFactory:
    """A factory to create the appropriate docstring generator."""
    @staticmethod
    def create_generator(strategy: str, style: str = "google") -> IDocstringGenerator:
        if strategy == "mock":
            return MockGenerator()
        
        if strategy == "groq":
            dotenv_path = Path(os.getcwd()) / '.env'
            load_dotenv(dotenv_path=dotenv_path)
            api_key = os.getenv("GROQ_API_KEY")
            
            if not api_key:
                print("\nError: Groq API key not found.", file=sys.stderr)
                sys.exit(1)

            model_name = os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192")
            groq_adapter = GroqAdapter(api_key=api_key, model=model_name)
            return LLMGenerator(llm_service=groq_adapter, style=style)
            
        raise ValueError(f"Unknown generator strategy: {strategy}")