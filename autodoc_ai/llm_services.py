import abc
from cmd import PROMPT
import os
from typing import Optional
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
    def suggest_name(self, code_context: str, old_name: str) -> Optional[str]:
        """
        Asks the LLM to suggets a better name for a variable.
        """
        pass

    @abc.abstractmethod
    def suggest_function_name(self, code_context: str, old_name: str) -> Optional[str]:
        """Suggests a better name for a function or method."""
        pass

    @abc.abstractmethod
    def evaluate_name(self, code_context: str, name: str) -> bool:
        """Asks the LLM to evaluate if a name is high quality. Returns True if good."""
        pass

    @abc.abstractmethod
    def generate_type_hints(self, code_context: str) -> dict:
        """
        Generates type hints for a function.
        Returns a dict with 'parameters' (dict of param_name: type_hint) and 'return_type' (str).
        """
        pass

    @abc.abstractmethod
    def suggest_constant_name(self, code_context: str, magic_number: str) -> Optional[str]:
        """
        Suggests a descriptive constant name for a magic number.
        Returns the suggested constant name in UPPER_SNAKE_CASE or None.
        """
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

    def evaluate_name(self, code_context: str, name: str) -> bool:
        prompt = f"""
        Analyze the Python code and the name `{name}`. Is this name high-quality and descriptive?

        **Be very conservative.** Only answer NO if the name is clearly poor.
        - **GOOD names** are descriptive and conventional (e.g., `user_profile`, `calculate_interest`, `first_number`, `item_count`, `MyCoolClass`). Do NOT flag these. These are YES.
        - **BAD names** are too short (e.g., 'x', 'd'), too generic (e.g., 'data', 'temp'), or misleading. These are NO.

        Code:
        {code_context}        
        Is `{name}` a high-quality name in this context? Answer with a single word: YES or NO.
        """
        try:
            response = self.create_completion(prompt)
            return "yes" in response.lower().strip()
        except Exception as e:
            print(f"Error during name evaluation: {e}")
            return True 

    
    def suggest_name(self, code_context: str, old_name: str) -> Optional[str]:
        prompt = f"""
        Analyze the following Python code. The variable `{old_name}` has been flagged for a potential naming issue.
        Suggest a better, more descriptive variable name based on its usage.

        Code:
        {code_context}        
        A good name is descriptive and follows Python's snake_case convention.
        
        **IMPORTANT: If you believe the original name `{old_name}` is already a good and descriptive name, then simply return the original name itself.**

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

    def suggest_function_name(self, code_context: str, old_name: str) -> Optional[str]:
        prompt = f"""
        Analyze the following Python function/method. The name `{old_name}` has been flagged for a potential naming issue.
        Suggest a better, more descriptive name that follows Python's snake_case convention.

        Code:
        {code_context}        
        
        **IMPORTANT: If you believe the original name `{old_name}` is already a good and descriptive name, then simply return the original name itself.**

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

    def suggest_class_name(self, code_context: str, old_name: str) -> Optional[str]:
        prompt = f"""
        Analyze the following Python class. The name `{old_name}` has been flagged for a potential naming issue.
        Suggest a better, more descriptive name that follows Python's PascalCase convention.

        Code:
        {code_context}        
        
        **IMPORTANT: If you believe the original name `{old_name}` is already a good and descriptive name, then simply return the original name itself.**

        Return only the new class name, and nothing else.
        """
        try:
            response = self.create_completion(prompt).strip()
            if response and response.isidentifier():
                return response
            return None
        except Exception as e:
            print(f"Error suggesting class name: {e}")
            return None

    def generate_type_hints(self, code_context: str) -> dict:
        """
        Generates type hints for a Python function by analyzing its implementation.
        Returns a dict with 'parameters' and 'return_type'.
        """
        prompt = f"""
        Analyze the following Python function and infer appropriate type hints for its parameters and return type.

        Code:
        ```python
        {code_context}
        ```

        Based on the function's implementation, variable usage, and operations:
        1. Infer the type for each parameter
        2. Infer the return type
        3. Use standard Python type hints (str, int, float, bool, list, dict, tuple, None, Any, Optional, etc.)
        4. For complex types, use typing module annotations (List[str], Dict[str, int], Optional[int], etc.)

        Return ONLY a valid JSON object in this exact format (no markdown, no extra text):
        {{
            "parameters": {{"param_name": "type_hint", "another_param": "type_hint"}},
            "return_type": "return_type_hint"
        }}

        If a parameter type cannot be inferred confidently, use "Any".
        If the function returns nothing, use "None".
        """
        try:
            response = self.create_completion(prompt).strip()
            
            # Try to extract JSON from the response
            # Sometimes LLMs wrap JSON in markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            import json
            type_hints = json.loads(response)
            
            # Validate the structure
            if not isinstance(type_hints, dict):
                return {"parameters": {}, "return_type": None}
            
            if "parameters" not in type_hints:
                type_hints["parameters"] = {}
            if "return_type" not in type_hints:
                type_hints["return_type"] = None
                
            return type_hints
            
        except json.JSONDecodeError as e:
            print(f"Error parsing type hints JSON: {e}")
            print(f"Response was: {response}")
        except Exception as e:
            print(f"Error generating type hints: {e}")
            return {"parameters": {}, "return_type": None}

    def suggest_constant_name(self, code_context: str, magic_number: str) -> Optional[str]:
        """
        Suggests a descriptive constant name for a magic number based on its usage context.
        """
        prompt = f"""
        Analyze the following Python code and suggest a descriptive constant name for the magic number `{magic_number}`.

        Code:
        ```python
        {code_context}
        ```

        Based on how the number `{magic_number}` is used in the code:
        1. Suggest a clear, descriptive constant name in UPPER_SNAKE_CASE
        2. The name should explain what the number represents
        3. Follow Python naming conventions

        Examples of good constant names:
        - MAX_RETRIES (for 3 in retry logic)
        - TAX_RATE (for 0.15 in tax calculations)
        - DEFAULT_TIMEOUT_SECONDS (for 30 in timeout logic)
        - DAYS_IN_WEEK (for 7)

        Return ONLY the constant name, nothing else. No explanations, no markdown.
        If the number is too generic to name meaningfully, return "SKIP".
        """
        try:
            response = self.create_completion(prompt).strip()
            
            # Clean up response
            response = response.replace('`', '').replace('"', '').replace("'", '').strip()
            
            # Skip if LLM says it's too generic
            if response.upper() == "SKIP" or not response:
                return None
            
            # Validate it's a valid Python identifier in UPPER_SNAKE_CASE
            if response.isupper() and response.replace('_', '').isalnum():
                return response
            
            return None
        except Exception as e:
            print(f"Error suggesting constant name: {e}")
            return None


class OpenAIAdapter(ILLMService):
    """Adapter for OpenAI Chat Completions API (lazy import)."""
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        try:
            from openai import OpenAI  # type: ignore
        except Exception:
            raise ImportError("openai package not installed. pip install openai")
        self.OpenAI = OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def create_completion(self, prompt: str) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return ""

    def evaluate_docstring(self, code: str, docstring: str) -> bool:
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

    def suggest_name(self, code_context: str, old_name: str) -> Optional[str]:
        prompt = f"""
        Analyze the following Python code. The variable `{old_name}` has been flagged for a potential naming issue.
        Suggest a better, more descriptive variable name based on its usage.

        Code:
        {code_context}        
        A good name is descriptive and follows Python's snake_case convention.
        
        **IMPORTANT: If you believe the original name `{old_name}` is already a good and descriptive name, then simply return the original name itself.**

        Return only the new variable name, and nothing else.
        """
        try:
            response = self.create_completion(prompt=prompt).strip()
            if response and response.isidentifier():
                return response
            return None
        except Exception as e:
            print(f"Error suggesting name: {e}")
            return None

    def suggest_function_name(self, code_context: str, old_name: str) -> Optional[str]:
        prompt = f"""
        Analyze the following Python function/method. The name `{old_name}` has been flagged for a potential naming issue.
        Suggest a better, more descriptive name that follows Python's snake_case convention.

        Code:
        {code_context}        
        
        **IMPORTANT: If you believe the original name `{old_name}` is already a good and descriptive name, then simply return the original name itself.**

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

    def suggest_class_name(self, code_context: str, old_name: str) -> Optional[str]:
        prompt = f"""
        Analyze the following Python class. The name `{old_name}` has been flagged for a potential naming issue.
        Suggest a better, more descriptive name that follows Python's PascalCase convention.

        Code:
        {code_context}        
        
        **IMPORTANT: If you believe the original name `{old_name}` is already a good and descriptive name, then simply return the original name itself.**

        Return only the new class name, and nothing else.
        """
        try:
            response = self.create_completion(prompt).strip()
            if response and response.isidentifier():
                return response
            return None
        except Exception as e:
            print(f"Error suggesting class name: {e}")
            return None

    def evaluate_name(self, code_context: str, name: str) -> bool:
        prompt = f"""
        Analyze the Python code and the name `{name}`. Is this name high-quality and descriptive?

        **Be very conservative.** Only answer NO if the name is clearly poor.
        - **GOOD names** are descriptive and conventional (e.g., `user_profile`, `calculate_interest`, `first_number`, `item_count`, `MyCoolClass`). Do NOT flag these. These are YES.
        - **BAD names** are too short (e.g., 'x', 'd'), too generic (e.g., 'data', 'temp'), or misleading. These are NO.

        Code:
        {code_context}        
        Is `{name}` a high-quality name in this context? Answer with a single word: YES or NO.
        """
        try:
            response = self.create_completion(prompt)
            return "yes" in response.lower().strip()
        except Exception as e:
            print(f"Error during name evaluation: {e}")
            return True

    def generate_type_hints(self, code_context: str) -> dict:
        prompt = f"""
        Analyze the following Python function and infer appropriate type hints for its parameters and return type.

        Code:
        ```python
        {code_context}
        ```

        Based on the function's implementation, variable usage, and operations:
        1. Infer the type for each parameter
        2. Infer the return type
        3. Use standard Python type hints (str, int, float, bool, list, dict, tuple, None, Any, Optional, etc.)
        4. For complex types, use typing module annotations (List[str], Dict[str, int], Optional[int], etc.)

        Return ONLY a valid JSON object in this exact format (no markdown, no extra text):
        {{
            "parameters": {{"param_name": "type_hint", "another_param": "type_hint"}},
            "return_type": "return_type_hint"
        }}

        If a parameter type cannot be inferred confidently, use "Any".
        If the function returns nothing, use "None".
        """
        try:
            response = self.create_completion(prompt).strip()
            # unwrap markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            import json
            data = json.loads(response)
            if not isinstance(data, dict):
                return {"parameters": {}, "return_type": None}
            data.setdefault("parameters", {})
            data.setdefault("return_type", None)
            return data
        except Exception as e:
            print(f"Error generating type hints: {e}")
            return {"parameters": {}, "return_type": None}

    def suggest_constant_name(self, code_context: str, magic_number: str) -> Optional[str]:
        """Reuse GroqAdapter implementation."""
        return GroqAdapter.suggest_constant_name(self, code_context, magic_number)

class AnthropicAdapter(ILLMService):
    """Adapter for Anthropic Messages API (Claude) with lazy import."""
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-latest"):
        if not api_key:
            raise ValueError("Anthropic API key is required.")
        try:
            import anthropic  # lazy import
        except Exception:
            raise ImportError("anthropic package not installed. pip install anthropic")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def create_completion(self, prompt: str) -> str:
        try:
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            # content is a list of blocks; take first text
            return "".join(block.text for block in msg.content if hasattr(block, "text"))
        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            return ""

    # Delegate to OpenAIAdapter's implementation by creating a helper instance
    def evaluate_docstring(self, code: str, docstring: str) -> bool:
        return OpenAIAdapter.evaluate_docstring(self, code, docstring)
    
    def suggest_name(self, code_context: str, old_name: str) -> Optional[str]:
        return OpenAIAdapter.suggest_name(self, code_context, old_name)
    
    def suggest_function_name(self, code_context: str, old_name: str) -> Optional[str]:
        return OpenAIAdapter.suggest_function_name(self, code_context, old_name)
    
    def suggest_class_name(self, code_context: str, old_name: str) -> Optional[str]:
        return OpenAIAdapter.suggest_class_name(self, code_context, old_name)
    
    def evaluate_name(self, code_context: str, name: str) -> bool:
        return OpenAIAdapter.evaluate_name(self, code_context, name)
    
    def generate_type_hints(self, code_context: str) -> dict:
        return OpenAIAdapter.generate_type_hints(self, code_context)
    
    def suggest_constant_name(self, code_context: str, magic_number: str) -> Optional[str]:
        return GroqAdapter.suggest_constant_name(self, code_context, magic_number)


class GeminiAdapter(ILLMService):
    """Adapter for Google Gemini (google-generativeai) with lazy import."""
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        if not api_key:
            raise ValueError("Gemini API key is required.")
        try:
            import google.generativeai as genai  # lazy import
        except Exception:
            raise ImportError("google-generativeai package not installed. pip install google-generativeai")
        genai.configure(api_key=api_key)
        self.genai = genai
        self.model_name = model

    def create_completion(self, prompt: str) -> str:
        try:
            model = self.genai.GenerativeModel(self.model_name)
            resp = model.generate_content(prompt)
            return resp.text or ""
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return ""

    # Delegate to OpenAIAdapter's implementation
    def evaluate_docstring(self, code: str, docstring: str) -> bool:
        return OpenAIAdapter.evaluate_docstring(self, code, docstring)
    
    def suggest_name(self, code_context: str, old_name: str) -> Optional[str]:
        return OpenAIAdapter.suggest_name(self, code_context, old_name)
    
    def suggest_function_name(self, code_context: str, old_name: str) -> Optional[str]:
        return OpenAIAdapter.suggest_function_name(self, code_context, old_name)
    
    def suggest_class_name(self, code_context: str, old_name: str) -> Optional[str]:
        return OpenAIAdapter.suggest_class_name(self, code_context, old_name)
    
    def evaluate_name(self, code_context: str, name: str) -> bool:
        return OpenAIAdapter.evaluate_name(self, code_context, name)
    
    def generate_type_hints(self, code_context: str) -> dict:
        return OpenAIAdapter.generate_type_hints(self, code_context)
    
    def suggest_constant_name(self, code_context: str, magic_number: str) -> Optional[str]:
        return GroqAdapter.suggest_constant_name(self, code_context, magic_number)
