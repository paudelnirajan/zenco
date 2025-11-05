from os.path import isfile
import os
import pathspec

def get_python_files(path: str) -> list[str]:
    """
    Finds all Python files in a given path, respecting .gitignore.

    :param path: The path to a file or directory.
    :return: A list of absolute paths to Python files.
    """
    if os.path.isfile(path=path):
        if path.endswith(".py"):
            return [os.path.abspath(path)]
        return []

    if not os.path.isdir(path):
        print(f"Error: Path '{path}' is not a valid file or directory.")
        return []

    gitignore_path = os.path.join(path, ".gitignore")
    spec = None
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            patterns = f.read().splitlines()
            patterns.extend(['.git/', 'venv/', '__pycache__/'])
            spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)

    python_files = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                if spec and spec.match_file(full_path):
                    continue
                python_files.append(full_path)
    return python_files