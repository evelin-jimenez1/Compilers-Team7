"""
Semantic Analyzer with Syntax-Directed Translation (SDT)
------------------------------------------------------
Authors: Team 7
Date: May 2026

Description:
This module performs Syntax-Directed Translation over the real grammar 
nodes produced by the LL(1) Parser, validating declarations, scopes, 
and initialization status using the Symbol Table.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from SymbolTable import SymbolTable

class SemanticAnalyzer:
    def __init__(self):
        self.table = SymbolTable()
        self.errors = []

    def analyze(self, node):
        """Entry point to start the SDT traversal."""
        self.errors = []
        self.table = SymbolTable()   # full reset between compilations
        self.visit(node)
        return self.errors + self.table.errors

    def visit(self, node):
        """Dynamic dispatcher (Visitor Pattern)."""
        if node is None:
            return
        method_name = f'visit_{node.node_type}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    # ─────────────────────────────────────────────────────────────────────────
    # GLOBAL: registers functions and global variables
    # GLOBAL → TYPE id GLOBAL_REST
    # ─────────────────────────────────────────────────────────────────────────
    def visit_GLOBAL(self, node):
        if len(node.children) < 3:
            return self.generic_visit(node)

        type_node   = node.children[0]   # TYPE
        id_node     = node.children[1]   # id
        global_rest = node.children[2]   # GLOBAL_REST

        var_type = type_node.children[0].node_type if type_node.children else "void"
        var_name = id_node.value

        # Decide if it's a function or global variable based on GLOBAL_REST
        # GLOBAL_REST → ( PARAMS ) { STMT_LIST }   → function
        # GLOBAL_REST → OPT_ASSIGN ;               → global variable
        is_func = (
            global_rest.children and
            global_rest.children[0].node_type == '('
        )

        self.table.declare(var_name, var_type, line=0, is_func=is_func)

        if is_func:
            # Functions are always considered initialized (they have a body)
            self.table.mark_as_initialized(var_name)
            # Enter function scope to register parameters and body
            self.table.enter_scope()
            self.generic_visit(node)
            self.table.exit_scope()
        else:
            # Global variable: mark as initialized if it has an assignment
            opt_assign = global_rest.children[0] if global_rest.children else None
            if opt_assign and opt_assign.children and opt_assign.children[0].node_type == '=':
                self.table.mark_as_initialized(var_name)
            self.generic_visit(node)

    # ─────────────────────────────────────────────────────────────────────────
    # PARAMS: first function parameter
    # PARAMS → TYPE id PARAMS_REST  |  epsilon
    # ─────────────────────────────────────────────────────────────────────────
    def visit_PARAMS(self, node):
        if not node.children:
            return  # epsilon

        type_node = None
        id_node   = None
        for child in node.children:
            if hasattr(child, 'node_type'):
                if child.node_type == 'TYPE':
                    type_node = child
                elif child.node_type == 'id':
                    id_node = child

        if type_node and id_node:
            var_type = type_node.children[0].node_type if type_node.children else "int"
            var_name = id_node.value
            success  = self.table.declare(var_name, var_type, line=0)
            if success:
                self.table.mark_as_initialized(var_name)

        self.generic_visit(node)

    # ─────────────────────────────────────────────────────────────────────────
    # PARAMS_REST: additional comma-separated parameters
    # PARAMS_REST → , TYPE id PARAMS_REST  |  epsilon
    # ─────────────────────────────────────────────────────────────────────────
    def visit_PARAMS_REST(self, node):
        if not node.children:
            return  # epsilon

        type_node = None
        id_node   = None
        for child in node.children:
            if hasattr(child, 'node_type'):
                if child.node_type == 'TYPE':
                    type_node = child
                elif child.node_type == 'id':
                    id_node = child

        if type_node and id_node:
            var_type = type_node.children[0].node_type if type_node.children else "int"
            var_name = id_node.value
            success  = self.table.declare(var_name, var_type, line=0)
            if success:
                self.table.mark_as_initialized(var_name)

        self.generic_visit(node)

    # ─────────────────────────────────────────────────────────────────────────
    # STMT: declarations and assignments inside blocks
    # ─────────────────────────────────────────────────────────────────────────
    def visit_STMT(self, node):
        if not node.children:
            return self.generic_visit(node)

        first_child = node.children[0]

        # Case A: Declaration → TYPE id OPT_ASSIGN ;
        if first_child.node_type == 'TYPE':
            type_node       = first_child
            id_node         = node.children[1]
            opt_assign_node = node.children[2]

            var_type = type_node.children[0].node_type if type_node.children else "void"
            var_name = id_node.value

            success = self.table.declare(var_name, var_type, line=0)

            if success and opt_assign_node.children and opt_assign_node.children[0].node_type == '=':
                self.table.mark_as_initialized(var_name)

        # Case B: Assignment or function call → id STMT_ID_REST
        elif first_child.node_type == 'id':
            var_name     = first_child.value
            stmt_id_rest = node.children[1]

            symbol = self.table.lookup(var_name)
            if not symbol:
                self.errors.append(
                    f"Semantic Error: '{var_name}' has not been declared."
                )
            else:
                if stmt_id_rest.children and stmt_id_rest.children[0].node_type == '=':
                    self.table.mark_as_initialized(var_name)

        self.generic_visit(node)

    # ─────────────────────────────────────────────────────────────────────────
    # PRIMARY: variable usage inside expressions
    # ─────────────────────────────────────────────────────────────────────────
    def visit_PRIMARY(self, node):
        if node.children and node.children[0].node_type == 'id':
            var_name = node.children[0].value

            symbol = self.table.lookup(var_name)
            if not symbol:
                self.errors.append(
                    f"Semantic Error: '{var_name}' is used in an expression but has not been declared."
                )
            elif not symbol.initialized:
                self.errors.append(
                    f"Semantic Error: '{var_name}' is used before being initialized."
                )

        self.generic_visit(node)

    # ─────────────────────────────────────────────────────────────────────────
    # Generic fallback
    # ─────────────────────────────────────────────────────────────────────────
    def generic_visit(self, node):
        for child in node.children:
            if hasattr(child, 'children'):
                self.visit(child)