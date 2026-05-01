"""
Abstract Syntax Tree (AST) Node Definition
------------------------------------------
Description:
This module defines the structure for the nodes of the AST.
The AST is the intermediate representation used by the Semantic
Analyzer to verify program correctness.
"""


class ASTNode:

    # Represents a node in the Abstract Syntax Tree
    # Stores type, children, value and inferred semantic type
    def __init__(self, node_type, children=None, value=None, inferred_type=None):

        self.node_type = node_type

        # Child nodes in the AST hierarchy
        self.children = children if children else []

        # Literal value or identifier name
        self.value = value

        # Type inferred during semantic analysis
        self.inferred_type = inferred_type

    # Returns a visual tree representation of the AST
    def __repr__(self, level=0):

        # Format type annotation if exists
        type_info = f" <{self.inferred_type}>" if self.inferred_type else ""

        # Format value if exists
        value_info = f" : {self.value}" if self.value is not None else ""

        # Indentation for tree structure visualization
        indent = "  " * level

        # Node representation
        result = f"{indent}|-- [{self.node_type}]{value_info}{type_info}\n"

        # Recursively print children
        for child in self.children:
            if child:
                result += child.__repr__(level + 1)

        return result