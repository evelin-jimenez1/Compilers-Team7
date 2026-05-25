"""
Abstract Syntax Tree (AST) Node Definition
------------------------------------------
Description:
This module defines the structure for the nodes of the AST.
The AST is the intermediate representation used by the Semantic
Analyzer to verify program correctness and perform SDT.
"""

class ASTNode:
    """
    Represents a node in the Abstract Syntax Tree.
    This structure is designed to be easily traversed by the Semantic Analyzer.
    """
    def __init__(self, node_type, children=None, value=None, inferred_type=None):
        self.node_type = node_type
        self.children = children if children else []
        self.value = value
        self.inferred_type = inferred_type

    def add_child(self, child):
        """Helper to append children dynamically during parsing."""
        if child is not None:
            self.children.append(child)

    def __repr__(self, level=0):
        """Returns a visual tree representation of the AST."""
        type_info = f" <{self.inferred_type}>" if self.inferred_type else ""
        value_info = f" : {self.value}" if self.value is not None else ""
        indent = "  " * level
        result = f"{indent}|-- [{self.node_type}]{value_info}{type_info}\n"
        
        for child in self.children:
            if isinstance(child, ASTNode):
                result += child.__repr__(level + 1)
            else:
                result += f"{indent}  |-- {child}\n"
        return result