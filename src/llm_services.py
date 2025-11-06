import abc
from cmd import PROMPT
import os
from groq import Groq

# ---- Interface (Contract) ----

class ILLMService(abc.ABC):
    """
    An interface for a service that can make requests to an LLM.
    This defines our internal, application-specific contract, supporting both generation and evaluation tasks.
    """
    @abc.abstractmethod
    def create_completion(self, prompt: str) -> str:
        """
        Generates a text completion based on the input prompt.
        """
        pass

    @abc.abstractmethod
    def evaluate_docstring(self, code: str, docstring: str) -> bool:
        """
        Asks the LLM to evaluate if a docstring is high quality for the given code.
        Returns True if the docstring is deemed good, False otherwise.
        """
        pass

    @abc.abstractmethod
    def suggest_name(self, code_context: str, old_name: str) -> str | None:
        """
        Asks the LLM to suggets a better name for a variable.
        """
        pass

    @abc.abstractmethod
    def suggest_function_name(self, code_context: str, old_name: str) -> str | None:
        """Suggests a better name for a function or method."""
        pass

    @abc.abstractmethod
    def evaluate_name(self, code_context: str, name: str) -> bool:
        """Asks the LLM to evaluate if a name is high quality. Returns True if good."""
        pass

# --- Implementation (Adapter) ---

class GroqAdapter(ILLMService):
    """
    An adapter for the Groq API. It "adapts" the `groq` library to fit the simple `ILLMService` interface our applciation uses.
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        if not api_key:
            raise ValueError("Groq API key is required.")
        self.client = Groq(api_key=api_key)
        self.model = model

    def create_completion(self, prompt: str) -> str:
        """
        Handles the specific logic for calling the Groq Chat Completions endpoint.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return ""

    def evaluate_docstring(self, code: str, docstring: str) -> bool:
        """
        Implements the LLM-powered evaluation logic using a specific prompt.
        """
        prompt = f"""
        Analyze the following Python code and its docstring.
        Is the docstring a high-quality, descriptive, and helpful documentation for the code?
        A good docstring explains what the code does, its arguments (if any), what it returns. A bad docstring is either too generic or completely irrevalent.

        Code:
        ```python
        {code}
        ```

        Docstring:
        ```
        {docstring}
        ```

        Answer with a single word: YES or NO.
        """
        try:
            response = self.create_completion(prompt)
            return "yes" in response.lower().strip()
            
        except Exception as e:
            print(f"Error during docstring evaluation: {e}")
            return True

    
    def suggest_name(self, code_context: str, old_name: str) -> str | None:
        prompt = f"""
        Analyze the following Python code. The variable `{old_name}` has a poor name. Suggest a better, more descriptive variable name based on the usage in the code.

        Code:

        {code_context}

        A good name should be descriptive, follow standard Python naming convention (snake_case), and not be a reserved keyword.

        Return only the new variable name, and nothing else.
        """
        try: 
            response = self.create_completion(prompt=prompt).strip()
            # basic validation
            if response and response.isidentifier():
                return response
            return None
        except Exception as e:
            print(f"Error suggesting name: {e}")
            return None

    def suggest_function_name(self, code_context: str, old_name: str) -> str | None:
        prompt = f"""
        Analyze the following Python function/method. The name `{old_name}` is poor.
        Suggest a better, more descriptive name that follows Python's snake_case convention.

        Code:
        
        {code_context}
                Return only the new function name, and nothing else.
        """
        try:
            response = self.create_completion(prompt).strip()
            if response and response.isidentifier():
                return response
            return None
        except Exception as e:
            print(f"Error suggesting function name: {e}")
            return None

    def evaluate_name(self, code_context: str, name: str) -> bool:
        prompt = f"""
        Analyze the following Python code and the name `{name}`.
        Is the name a high-quality, descriptive, and contextually appropriate name for the variable, function, or class?
        A good name is clear, concise, and follows standard Python conventions (e.g., snake_case for variables/functions).
        A bad name is too short (like 'x' or 'd'), generic (like 'data' or 'temp'), or doesn't match what the code is doing.

        Code:
        
        {code_context}
                Answer with a single word: YES or NO.
        """
        try:
            response = self.create_completion(prompt)
            return "yes" in response.lower().strip()
        except Exception as e:
            print(f"Error during name evaluation: {e}")
            return True 