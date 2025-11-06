import ast

class VariableRenamer(ast.NodeTransformer):
    """
    An AST transformer that renames all occurrences of a variable within the nodes it visits.
    """
    def __init__(self, old_name: str, new_name: str):
        self.old_name = old_name
        self.new_name = new_name

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """
        Called for every 'Name' node (i.e., a variable).
        If the name matches our target, we rename it.
        """
        if node.id == self.old_name:
            node.id = self.new_name
        return node

    def visit_arg(self, node:ast.arg) -> ast.arg:
        """
        Called for every function argument.
        If the argument name matches our target, we rename it.
        """
        if node.arg == self.old_name:
            node.arg = self.new_name
        return node