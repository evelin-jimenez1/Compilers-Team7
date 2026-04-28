"""
Abstract Syntax Tree (AST) Node Definition
------------------------------------------
Description:
This module defines the structure for the nodes of the AST.
The AST is the intermediate representation that the Semantic 
Analyzer traverses to verify the logic of the code.
"""

class ASTNode:
    """
    Represents a node in the Abstract Syntax Tree.
    
    Attributes:
        type (str): The category of the node (e.g., 'ASSIGN', 'BIN_OP', 'IF').
        children (list): Other ASTNodes that belong to this node.
        value (str): The actual value or operator (e.g., 'x', '+', 'int main').
        inferred_type (str): The data type determined during semantic analysis.
    """
    def __init__(self, node_type, children=None, value=None, inferred_type=None):
        self.node_type = node_type
        self.children = children if children else []
        self.value = value
        self.inferred_type = inferred_type

    def __repr__(self, level=0):
        """ Returns a visual hierarchical string representation of the tree. """
        type_info = f" <{self.inferred_type}>" if self.inferred_type else ""
        value_info = f" : {self.value}" if self.value is not None else ""
        
        # Visual structure with branches
        indent = "  " * level
        result = f"{indent}|-- [{self.node_type}]{value_info}{type_info}\n"
        
        for child in self.children:
            if child:
                result += child.__repr__(level + 1)
        return result