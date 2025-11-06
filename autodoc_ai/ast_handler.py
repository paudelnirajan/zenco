import ast
from .generators import IDocstringGenerator
from .transformers import VariableRenamer

class CodeQualityVisitor(ast.NodeVisitor):
    """
    Finds quality issues and can perform AI-powered refactoring.
    """
    IGNORED_NAMES = {'i', 'j', 'k', 'x', 'y', 'z', 'id', 'self', 'cls'}

    def __init__(self, generator: IDocstringGenerator = None, overwrite_existing: bool = False, refactor: bool = False):
        self.generator = generator
        self.overwrite_existing = overwrite_existing
        self.refactor = refactor
        self.tree_modified = False

    def _process_node_for_docstring(self, node: ast.FunctionDef | ast.ClassDef):
        # This method is unchanged
        existing_docstring = ast.get_docstring(node)
        if not existing_docstring: self._inject_docstring(node); return
        if self.overwrite_existing and self.generator and hasattr(self.generator, 'evaluate'):
            if not self.generator.evaluate(node, existing_docstring):
                print(f"L{node.lineno}:[Docstring] Found poor quality docstring for '{node.name}'. Regenerating.")
                if node.body and isinstance(node.body[0], ast.Expr): node.body.pop(0)
                self._inject_docstring(node)

    def _inject_docstring(self, node: ast.FunctionDef | ast.ClassDef):
        if self.generator:
            print(f"L{node.lineno}:[Docstring] Generating docstring for '{node.name}'.")
            docstring_text = self.generator.generate(node)
            docstring_node = ast.Expr(value=ast.Constant(value=docstring_text))
            node.body.insert(0, docstring_node); self.tree_modified = True
        else:
            print(f"L{node.lineno}:[Docstring] '{node.name}' is missing a docstring.")

    def _check_name(self, context_node: ast.AST, name: str):
        """
        Helper to evaluate a name and suggest/refactor it if it's poor.
        This consolidates logic for variables, functions, and classes.
        """
        if name in self.IGNORED_NAMES or name.startswith("__"):
            return

        is_good_name = self.generator.evaluate_name(context_node, name)
        if not is_good_name:
            print(f"L{context_node.lineno}:[AI Linter] Name '{name}' is potentially poor. Asking for suggestion...")
            
            suggestion = None
            if isinstance(context_node, ast.ClassDef) and name == context_node.name:
                suggestion = self.generator.suggest_class_name(context_node, name)
                if suggestion and suggestion != name:
                    print(f"L{context_node.lineno}:[AI Suggestion] Consider renaming class '{name}' to '{suggestion}'.\n")
            
            elif isinstance(context_node, ast.FunctionDef):
                if name == context_node.name:
                    suggestion = self.generator.suggest_function_name(context_node, name)
                    if suggestion and suggestion != name:
                        print(f"L{context_node.lineno}:[AI Suggestion] Consider renaming function '{name}' to '{suggestion}'.\n")
                else:
                    suggestion = self.generator.suggest_variable_name(context_node, name)
                    if suggestion and suggestion != name:
                        print(f"Renaming variable '{name}' to '{suggestion}' in function '{context_node.name}'.\n")
                        renamer = VariableRenamer(old_name=name, new_name=suggestion)
                        renamer.visit(context_node)
                        self.tree_modified = True

    def visit_ClassDef(self, node: ast.ClassDef):
        self._process_node_for_docstring(node)
        
        if self.refactor and self.generator:
            self._check_name(node, node.name)
        
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_node_for_docstring(node)

        if self.refactor and self.generator:
            self._check_name(node, node.name)
            
            names_to_check = {arg.arg for arg in node.args.args}
            for sub_node in ast.walk(node):
                if isinstance(sub_node, ast.Name) and isinstance(sub_node.ctx, ast.Store):
                    names_to_check.add(sub_node.id)

            for var_name in names_to_check:
                self._check_name(node, var_name)
        else: 
            pass

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)) and node.value not in {0, 1, -1}:
            print(f"L{node.lineno}:[Magic Number] Found a magic number: {node.value}.")
        self.generic_visit(node)