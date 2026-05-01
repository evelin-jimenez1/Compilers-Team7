"""
C-Pure Compiler Parser (LL(1) + SDT)
-----------------------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date:
    April 2026

Program description:
This module implements a Top-Down recursive-descent parser for a
subset of the C programming language. It performs syntactic analysis
using an LL(1)-compatible grammar and integrates Syntax-Directed
Translation (SDT) to construct an Abstract Syntax Tree (AST) while
simultaneously performing semantic validation.

The parser is tightly coupled with a Symbol Table that manages scopes
and supports semantic checks such as type validation, redeclaration
detection, and correct usage of identifiers.

Responsibilities:
- Perform predictive parsing based on LL(1) grammar rules.
- Construct an Abstract Syntax Tree (AST) during parsing.
- Execute Syntax-Directed Translation (SDT) actions inline.
- Manage scoped symbol tables for semantic validation.
- Detect syntactic and semantic errors with line precision.
- Enforce type checking for expressions, assignments, and returns.
- Validate function declarations and call consistency.

Architecture:
Each method in the parser corresponds to a grammar non-terminal.
Parsing decisions are driven by lookahead using peek(), while token
consumption is handled through advance() and consume() methods.

Semantic actions are embedded directly within parsing rules, allowing
syntax and semantic analysis to occur in a single pass. The AST serves
as the intermediate representation between parsing and later compiler
phases.
"""

from Ast.ASTNode import ASTNode
from Semantic.SymbolTable import SymbolTable


class Parser:
    """
    Recursive Descent Parser with SDT support.

    This class implements an LL(1) Top-Down parser where each method
    corresponds to a grammar production. It constructs an AST while
    performing semantic analysis using a scoped Symbol Table.
    """

    TYPE_KEYWORDS = {"int", "float", "double", "char", "void"}

    def __init__(self, tokens_list):
        """
        Initializes the parser with a list of tokens from the lexer.

        Parameters
        ----------
        tokens_list : list
            Token stream containing dictionaries with:
            - type
            - value
            - line
        """

        unknown_tokens = [t for t in tokens_list if t["type"] == "Unknown"]
        if unknown_tokens:
            first_err = unknown_tokens[0]
            raise Exception(
                f"[Line {first_err['line']}] Lexical Error: "
                f"Unknown token '{first_err['value']}'"
            )

        self.tokens = tokens_list
        self.current = 0
        self.derivation = []

        self.symbol_table = SymbolTable()
        self.current_function_type = None
        self.sdt_errors = []

    # UTILITIES (LEXICAL CONTROL)

    def error(self, msg):
        """Registers semantic or SDT error with line information."""
        self.sdt_errors.append(f"[Line {self.peek()['line']}] {msg}")

    def peek(self):
        """Returns current token without consuming it."""
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return {"type": "EOF", "value": "$", "line": -1}

    def advance(self):
        """Consumes and returns current token."""
        if self.current < len(self.tokens):
            self.current += 1
        return self.tokens[self.current - 1]

    def match(self, *values):
        """Matches token value against expected values."""
        if self.peek()["value"] in values:
            self.advance()
            return True
        return False

    def match_type(self, t):
        """Matches token type."""
        if self.peek()["type"] == t:
            return self.advance()
        return None

    def consume(self, val, msg):
        """Consumes expected token value or raises syntax error."""
        if self.peek()["value"] == val:
            return self.advance()
        raise Exception(f"[Line {self.peek()['line']}] {msg}")

    def consume_type(self, t, msg):
        """Consumes expected token type or raises syntax error."""
        if self.peek()["type"] == t:
            return self.advance()
        raise Exception(f"[Line {self.peek()['line']}] {msg}")

    def is_at_end(self):
        """Checks end of input."""
        return self.peek()["type"] == "EOF"

    # PROGRAM ENTRY POINT

    def parse_program(self):
        """Builds the root PROGRAM AST node."""
        nodes = []
        while not self.is_at_end():
            nodes.append(self.parse_global())
        return ASTNode("PROGRAM", nodes)

    def parse_global(self):
        """Parses global variables or functions using LL(1) lookahead."""
        type_token = self.peek()

        if type_token["value"] not in self.TYPE_KEYWORDS:
            raise Exception(f"[Line {type_token['line']}] Expected type")

        data_type = self.advance()["value"]
        id_token = self.consume_type("Identifiers", "Expected identifier")

        if self.peek()["value"] == "(":
            return self.parse_function(data_type, id_token)

        return self.parse_global_var(data_type, id_token)

    # GLOBAL VARIABLE DECLARATION

    def parse_global_var(self, t, id_token):
        """Handles global variable declarations and initialization."""

        if t == "void":
            self.error(f"Variable '{id_token['value']}' cannot be void")

        if not self.symbol_table.declare(id_token["value"], t, id_token["line"]):
            self.error(f"Duplicate variable '{id_token['value']}'")

        children = []

        if self.match("="):
            expr = self.parse_expression()
            children.append(expr)

            if expr.inferred_type != t:
                self.error("Type mismatch in assignment")

            self.symbol_table.mark_as_initialized(id_token["value"])

        self.consume(";", "Expected ';'")

        return ASTNode("GLOBAL_VAR", children, value=id_token["value"], inferred_type=t)

    # FUNCTION DEFINITION

    def parse_function(self, t, id_token):
        """Parses function declarations and creates new scope."""

        if not self.symbol_table.declare(
            id_token["value"], t, id_token["line"], is_func=True
        ):
            self.error(f"Duplicate function '{id_token['value']}'")

        self.consume("(", "Expected '('")
        self.consume(")", "Expected ')'")

        self.consume("{", "Expected '{'")

        self.symbol_table.enter_scope()
        self.current_function_type = t

        body = []
        while self.peek()["value"] != "}":
            body.append(self.parse_statement())

        self.consume("}", "Expected '}'")

        self.symbol_table.exit_scope()
        self.current_function_type = None

        return ASTNode("FUNCTION", body, value=id_token["value"], inferred_type=t)

    # STATEMENTS

    def parse_statement(self):
        """Dispatches statement parsing based on lookahead token."""

        token = self.peek()

        if token["value"] == "if":
            return self.parse_if()

        if token["value"] == "return":
            self.advance()
            expr = None

            if self.peek()["value"] != ";":
                expr = self.parse_expression()

            if self.current_function_type == "void" and expr:
                self.error("Void function cannot return value")

            if expr and expr.inferred_type != self.current_function_type:
                self.error("Return type mismatch")

            self.consume(";", "Expected ';'")
            return ASTNode("RETURN", [expr] if expr else [])

        if token["value"] in self.TYPE_KEYWORDS:
            return self.parse_local_decl()

        if token["type"] == "Identifiers":
            id_t = self.advance()

            if self.match("="):
                expr = self.parse_expression()

                sym = self.symbol_table.lookup(id_t["value"])

                if not sym:
                    self.error(f"Undeclared variable '{id_t['value']}'")
                else:
                    if expr.inferred_type != sym.type:
                        self.error("Type mismatch in assignment")
                    self.symbol_table.mark_as_initialized(id_t["value"])

                self.consume(";", "Expected ';'")
                return ASTNode("ASSIGN", [expr], value=id_t["value"])

        raise Exception(f"[Line {token['line']}] Invalid statement")

    # EXPRESSIONS (SDT SECTION)

    def parse_expression(self):
        """Entry point for expression parsing (precedence-based)."""
        return self.parse_logic_or()