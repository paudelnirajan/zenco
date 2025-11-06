import ast
from src.generators import IDocStringGenerator
from src.transformers import VariableRenamer

class CodeQualityVisitor(ast.NodeVisitor):
    """
    Finds quality issues and can perform AI-powered refactoring.
    """

    ALLOWED_SHORT_NAMES = {'i', 'j', 'k', 'x', 'y', 'z', 'id'}

    def __init__(self, generator: IDocStringGenerator = None, overwrite_existing: bool = False, refactor: bool = False):
        self.generator = generator
        self.overwrite_existing = overwrite_existing
        self.refactor = refactor
        self.tree_modified = False

    def _process_node_for_docstring(self, node: ast.FunctionDef | ast.ClassDef):
        """Processes a function or class node for docstring generation/replacement."""
        existing_docstring = ast.get_docstring(node)

        if not existing_docstring:
            self._inject_docstring(node)
            return

        if self.overwrite_existing and self.generator and hasattr(self.generator, 'evaluate'):
            is_good = self.generator.evaluate(node, existing_docstring)
            if not is_good:
                print(f"L{node.lineno}:[Docstring] Found poor quality docstring for '{node.name}'. Regenerating.")
                
                if node.body and isinstance(node.body[0], ast.Expr):
                    node.body.pop(0)
                
                self._inject_docstring(node)

    def _inject_docstring(self, node: ast.FunctionDef | ast.ClassDef):
        """Helper to generate and insert a docstring into a node."""
        if self.generator:
            print(f"L{node.lineno}:[Docstring] Generating docstring for '{node.name}'.")

            docstring_text = self.generator.generate(node)
            docstring_node = ast.Expr(value=ast.Constant(value=docstring_text))

            node.body.insert(0, docstring_node)
            self.tree_modified = True
        else:
            print(f"L{node.lineno}:[Docstring] '{node.name}' is missing a docstring.")

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_node_for_docstring(node)

        names_to_check = {node.name}
        names_to_check.update(arg.arg for arg in node.args.args)
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Name) and isinstance(sub_node.ctx, ast.Store):
                names_to_check.add(sub_node.id)

        if not (self.refactor and self.generator):
            for name in names_to_check:
                if len(name) < 3 and name not in self.ALLOWED_SHORT_NAMES:
                     print(f"L{node.lineno}:[Naming] Name '{name}' in context of '{node.name}' is very short.")
            return

        for name in names_to_check:
            if name.startswith("__"): continue

            is_good_name = self.generator.evaluate_name(node, name)
            if not is_good_name:
                print(f"L{node.lineno}:[AI Linter] Name '{name}' is potentially poor. Asking for suggestion...")
                
                if name == node.name:
                    suggestion = self.generator.suggest_function_name(node, name)
                    if suggestion and suggestion != name:
                        print(f"L{node.lineno}:[AI Suggestion] Consider renaming function '{name}' to '{suggestion}'.\n")
                else:
                    suggestion = self.generator.suggest_variable_name(node, name)
                    if suggestion and suggestion != name:
                        print(f"Renaming variable '{name}' to '{suggestion}' in function '{node.name}'.")
                        renamer = VariableRenamer(old_name=name, new_name=suggestion)
                        renamer.visit(node)
                        self.tree_modified = True

        self.generic_visit(node) 

    def visit_ClassDef(self, node: ast.ClassDef):
        if not ast.get_docstring(node):
            self._inject_docstring(node)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)) and node.value not in {0, 1, -1}:
            print(f"L{node.lineno}:[Magic Number] Found a magic number: {node.value}.")
        self.generic_visit(node)
        
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store) and len(node.id) < 3 and node.id not in self.ALLOWED_SHORT_NAMES:
            print(f"L{node.lineno}:[Naming] Variable name '{node.id}' is too short.")
        self.generic_visit(node)