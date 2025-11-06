import os
import tomli
from typing import Any, Dict

def find_pyproject_toml(start_dir: str) -> str | None:
    """
    Finds the pyproject.toml file by searching upwards from a starting directory.
    """
    current_dir = os.path.abspath(start_dir)
    while True:
        toml_path = os.path.join(current_dir, "pyproject.toml")
        if os.path.exists(toml_path):
            return toml_path

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            return None
        current_dir = parent_dir

def load_config() -> Dict[str, Any]:
    """
    Loads configuration from the [tool.autodoc] section of pyproject.toml.
    Returns a dictionary with default values if the file or section is not found.
    """
    default_config = {
        "strategy": "mock",
        "style": "google",
        "overwrite_existing": False,
    }

    toml_path = find_pyproject_toml(os.getcwd())
    if not toml_path:
        return default_config
    
    try:
        with open(toml_path, 'rb') as f:
            full_config = tomli.load(f)
            autodoc_config = full_config.get("tool", {}).get("autodoc", {})
            return {**default_config, **autodoc_config}
    except (tomli.TOMLDecodeError, IOError) as e:
        print(f"Warning: Could not read or parse pyproject.toml: {e}")
        return default_config