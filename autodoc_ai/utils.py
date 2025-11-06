from os.path import isfile
import os
import pathspec
import git

def get_git_changed_files() -> list[str] | None:
    """
    Finds all the changed Python files in the current git repository.
    Compares against the last commit. Includes staged, unstaged, and untracked files.

    :return: A list of absolute paths to changed Python files, or None if not a git repo.
    """
    try:
        repo = git.Repo(search_parent_directories=True)
        repo_root = repo.working_tree_dir

        staged_files = [os.path.join(repo_root, item.a_path) for item in repo.index.diff(None) if item.a_path.endswith('.py')]

        unstaged_files = [os.path.join(repo_root, item.a_path) for item in repo.head.commit.diff(None) if item.a_path.endswith('.py')]

        untracked_files = [os.path.join(repo_root, f) for f in repo.untracked_files if f.endswith('.py')]

        all_changed_files = set(staged_files + unstaged_files + untracked_files)
        return list(all_changed_files)

    except git.InvalidGitRepositoryError:
        print("Error: --diff flag was used, but this is not a git repository.")
        return None

    except Exception as e:
        print(f"An unexpected error occurred with Git: {e}")
        return None

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