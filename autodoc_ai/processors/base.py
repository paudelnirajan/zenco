"""
Base processor class for code enhancement features.
"""

from abc import ABC, abstractmethod
from typing import Optional, Set, Any
from ..transformers import CodeTransformer


class BaseProcessor(ABC):
    """
    Abstract base class for all code processors.
    
    Each processor handles a specific code enhancement feature
    (docstrings, type hints, magic numbers, dead code detection).
    """
    
    def __init__(self, lang: str, tree: Any, source_bytes: bytes, transformer: CodeTransformer):
        """
        Initialize the processor.
        
        Args:
            lang: Programming language (python, javascript, java, go, cpp)
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes
            transformer: Code transformation utility
        """
        self.lang = lang
        self.tree = tree
        self.source_bytes = source_bytes
        self.transformer = transformer
        self.source_text = source_bytes.decode('utf8')
    
    @abstractmethod
    def process(self, **kwargs) -> Optional[Set[Any]]:
        """
        Process the code and apply transformations.
        
        Returns:
            Optional set of processed nodes (e.g., dead functions to skip)
        """
        pass
    
    def find_nodes_by_type(self, node: Any, target_type: str):
        """
        Recursively find all nodes of a specific type.
        
        Args:
            node: Starting node
            target_type: Type of nodes to find
            
        Returns:
            List of matching nodes
        """
        results = []
        if node.type == target_type:
            results.append(node)
        for child in node.children:
            results.extend(self.find_nodes_by_type(child, target_type))
        return results
    
    def get_function_nodes(self):
        """
        Get all function nodes for the current language.
        
        Returns:
            Set of function nodes
        """
        type_map = {
            'python': 'function_definition',
            'javascript': 'function_declaration',
            'java': 'method_declaration',
            'go': 'function_declaration',
            'cpp': 'function_definition',
        }
        
        func_type = type_map.get(self.lang)
        if not func_type:
            return set()
        
        return set(self.find_nodes_by_type(self.tree.root_node, func_type))
    
    def get_function_name(self, func_node: Any) -> Optional[str]:
        """
        Extract function name from a function node.
        
        Args:
            func_node: Function node
            
        Returns:
            Function name or None
        """
        name_node = func_node.child_by_field_name('name')
        
        # For C++, check declarator
        if not name_node and self.lang == 'cpp':
            declarator = func_node.child_by_field_name('declarator')
            if declarator:
                for child in declarator.children:
                    if child.type == 'identifier':
                        name_node = child
                        break
        
        if name_node:
            return name_node.text.decode('utf8')
        return None
