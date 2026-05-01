"""
AST Visualizer Module
--------------------
Converts an AST (from parser_sdt.py) into a Graphviz graph
and exports it as an image.

Usage:
    from ast_visualizer import render_ast

    render_ast(ast, "output/ast.png")
"""

from graphviz import Digraph
import os


class ASTVisualizer:

    # Initialize Graphviz structure and node counter
    def __init__(self):
        self.dot = Digraph(comment="Abstract Syntax Tree")
        self.counter = 0

    # Generate unique node identifier
    def _next_id(self):
        node_id = str(self.counter)
        self.counter += 1
        return node_id

    # Format node label with type, value and inferred type
    def _format_label(self, node):
        label = node.node_type

        if node.value is not None:
            label += f"\n{node.value}"

        if node.inferred_type is not None:
            label += f"\n<{node.inferred_type}>"

        return label

    # Recursively add nodes and edges to the graph
    def _add_node(self, node, parent_id=None):
        node_id = self._next_id()

        label = self._format_label(node)

        # Node coloring based on type
        color = "white"
        style = "filled"

        if node.node_type in ["CONST", "LITERAL"]:
            color = "#90ee90"  # green
        elif node.node_type in ["ID"]:
            color = "#add8e6"  # light blue
        elif "VAR" in node.node_type:
            color = "#ffd580"  # orange
        elif node.node_type in ["BIN_OP", "UNARY"]:
            color = "#ff9999"  # light red
        elif node.node_type == "FUNCTION":
            color = "#d9b3ff"  # purple

        # Create node in Graphviz
        self.dot.node(node_id, label, style=style, fillcolor=color)

        # Connect to parent if exists
        if parent_id is not None:
            self.dot.edge(parent_id, node_id)

        # Recursively process children
        for child in node.children:
            if child:
                self._add_node(child, node_id)

    # Build graph from AST root
    def build(self, ast):
        self._add_node(ast)
        return self.dot

    # Render AST to image file
    def render(self, ast, filename="ast_output", format="png", view=False):
        self.build(ast)

        output_path = self.dot.render(
            filename=filename,
            format=format,
            cleanup=True,
            view=view
        )

        return output_path


# Simple helper function for direct usage
def render_ast(ast, filename="ast_output", file_format="png"):
    visualizer = ASTVisualizer()
    return visualizer.render(ast, filename, file_format)