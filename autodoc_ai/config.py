import os
import sys
from typing import Any, Dict, Optional

# This block makes the code compatible with Python < 3.11 and >= 3.11
try:
    # For Python 3.11+
    import tomllib
except ImportError:
    # For older Python versions, use the tomli library as a fallback
    import tomli as tomllib

def find_pyproject_toml(start_dir: str) -> Optional[str]:
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
    Loads configuration from the [tool.zenco] section of pyproject.toml.
    """
    default_config = {
        "strategy": "mock",
        "style": "google",
        "overwrite_existing": False,
        "refactor": False
    }

    toml_path = find_pyproject_toml(os.getcwd())
    if not toml_path:
        return default_config

    try:
        with open(toml_path, "rb") as f:
            # We use `tomllib` which is now an alias for either library
            full_config = tomllib.load(f)
            zenco_config = full_config.get("tool", {}).get("zenco", {})
            return {**default_config, **zenco_config}
    except (tomllib.TOMLDecodeError, IOError) as e:
        print(f"Warning: Could not read or parse pyproject.toml: {e}")
        return default_config