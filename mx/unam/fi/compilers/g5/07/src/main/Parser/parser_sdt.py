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

        # --- NUEVOS DESPACHADORES DE BUCLES -----------------------------------------------------
        if token["value"] == "while":
            return self.parse_while()
            
        if token["value"] == "do":
            return self.parse_do_while()
            
        if token["value"] == "for":
            return self.parse_for()
        # -----------------------------------------------------------------------------------------

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


    def parse_local_decl(self):
        """
        Parses a local variable declaration inside a function or loop block.
        Example: int x = 5; or float y;
        """
        # 1. Consumimos el tipo de dato (int, float, etc.)
        t = self.advance()["value"]
        
        # 2. Consumimos el identificador (el nombre de la variable)
        id_token = self.consume_type("Identifiers", "Expected identifier in local declaration")

        # Regla semántica: no permitir variables de tipo void
        if t == "void":
            self.error(f"Variable '{id_token['value']}' cannot be void")

        # SDT: Declaramos la variable en el ámbito LOCAL actual de la SymbolTable
        if not self.symbol_table.declare(id_token["value"], t, id_token["line"]):
            self.error(f"Duplicate variable '{id_token['value']}' in this scope")

        children = []

        # 3. Revisamos si hay una asignación opcional (OPT_ASSIGN)
        if self.match("="):
            expr = self.parse_expression()
            children.append(expr)

            # SDT: Verificación de tipos
            if expr.inferred_type != t:
                self.error("Type mismatch in local assignment")

            self.symbol_table.mark_as_initialized(id_token["value"])

        # 4. Consumimos el punto y coma final
        self.consume(";", "Expected ';' after local declaration")

        # Retornamos el nodo AST
        return ASTNode("LOCAL_VAR", children, value=id_token["value"], inferred_type=t)    
        
        # ========================================================================================================
    # LOOP PARSERS (Syntax + SDT)
    # ========================================================================================================

    def parse_while(self):
        """Parses a while loop, managing its semantic scope."""
        self.advance()  # Consume 'while'
        self.consume("(", "Expected '(' after 'while'")
        
        condition = self.parse_expression()
        
        self.consume(")", "Expected ')' after condition")
        self.consume("{", "Expected '{' to open while block")

        # SDT: Entramos al contexto del bucle
        self.symbol_table.enter_loop()
        
        body = []
        while self.peek()["value"] != "}":
            if self.is_at_end():
                raise Exception("Unexpected EOF parsing while block")
            body.append(self.parse_statement())

        self.consume("}", "Expected '}' to close while block")
        
        # SDT: Salimos del contexto
        self.symbol_table.exit_loop()

        return ASTNode("WHILE", [condition] + body)

    def parse_do_while(self):
        """Parses a do-while loop, managing its semantic scope."""
        self.advance()  # Consume 'do'
        self.consume("{", "Expected '{' after 'do'")

        # SDT: Entramos al contexto del bucle
        self.symbol_table.enter_loop()

        body = []
        while self.peek()["value"] != "}":
            if self.is_at_end():
                raise Exception("Unexpected EOF parsing do-while block")
            body.append(self.parse_statement())

        self.consume("}", "Expected '}' after do block")
        
        # SDT: Salimos del contexto
        self.symbol_table.exit_loop()

        self.consume("while", "Expected 'while'")
        self.consume("(", "Expected '(' after 'while'")
        
        condition = self.parse_expression()
        
        self.consume(")", "Expected ')' after condition")
        self.consume(";", "Expected ';' to complete do-while statement")

        return ASTNode("DO_WHILE", [condition] + body)

    def parse_for(self):
        """
        Parses a for loop. Handles initialization, condition, step, 
        and strict scope management for loop variables.
        """
        self.advance()  # Consume 'for'
        self.consume("(", "Expected '(' after 'for'")

        # SDT CRÍTICO: El ámbito del bucle se abre AQUÍ, ANTES del INIT.
        # Esto asegura que `int i = 0` pertenezca al bucle y muera con él.
        self.symbol_table.enter_loop()

        # 1. INIT
        init_node = self.parse_for_init()
        self.consume(";", "Expected ';' after for initialization")

        # 2. CONDITION (OPT_E)
        cond_node = None
        if self.peek()["value"] != ";":
            cond_node = self.parse_expression()
        self.consume(";", "Expected ';' after for condition")

        # 3. STEP
        step_node = self.parse_for_step()
        self.consume(")", "Expected ')' after for step")

        # 4. BODY
        self.consume("{", "Expected '{' to open for block")
        
        # Bloque interno del for (C estándar permite re-declarar variables en el cuerpo)
        self.symbol_table.enter_scope() 
        body = []
        while self.peek()["value"] != "}":
            if self.is_at_end():
                raise Exception("Unexpected EOF parsing for block")
            body.append(self.parse_statement())
            
        self.consume("}", "Expected '}' to close for block")
        self.symbol_table.exit_scope() 

        # SDT CRÍTICO: Se destruye la variable del INIT (ej. 'i')
        self.symbol_table.exit_loop()

        # Empaquetamos todo en un nodo AST unificado.
        # Filtramos 'None' por si el init, cond o step estaban vacíos (epsilon)
        header_nodes = [n for n in (init_node, cond_node, step_node) if n is not None]
        return ASTNode("FOR", header_nodes + body)

    def parse_for_init(self):
        """Parses the initialization segment of a for loop (Declaration, Assignment, or empty)."""
        token = self.peek()

        # Caso 1: Declaración (ej. int i = 0)
        if token["value"] in self.TYPE_KEYWORDS:
            t = self.advance()["value"]
            id_t = self.consume_type("Identifiers", "Expected identifier in for init")

            if not self.symbol_table.declare(id_t["value"], t, id_t["line"]):
                self.error(f"Duplicate variable '{id_t['value']}'")

            children = []
            if self.match("="):
                expr = self.parse_expression()
                children.append(expr)
                if expr.inferred_type != t:
                    self.error("Type mismatch in loop initialization")
                self.symbol_table.mark_as_initialized(id_t["value"])

            return ASTNode("LOCAL_VAR", children, value=id_t["value"], inferred_type=t)

        # Caso 2: Asignación a variable existente (ej. i = 0)
        if token["type"] == "Identifiers":
            id_t = self.advance()
            self.consume("=", "Expected '=' in for init assignment")
            expr = self.parse_expression()

            sym = self.symbol_table.lookup(id_t["value"])
            if not sym:
                self.error(f"Undeclared variable '{id_t['value']}'")
            else:
                if expr.inferred_type != sym.type:
                    self.error("Type mismatch in loop assignment")
                self.symbol_table.mark_as_initialized(id_t["value"])

            return ASTNode("ASSIGN", [expr], value=id_t["value"])

        # Caso 3: epsilon (vacío)
        return None

    def parse_for_step(self):
        """Parses the step segment of a for loop (Assignment or empty)."""
        token = self.peek()

        if token["type"] == "Identifiers":
            id_t = self.advance()
            self.consume("=", "Expected '=' in for step")
            expr = self.parse_expression()

            sym = self.symbol_table.lookup(id_t["value"])
            if not sym:
                self.error(f"Undeclared variable '{id_t['value']}' in loop step")
            else:
                if expr.inferred_type != sym.type:
                    self.error("Type mismatch in loop step assignment")

            return ASTNode("ASSIGN", [expr], value=id_t["value"])

        return None

    # EXPRESSIONS (SDT SECTION)

    def parse_expression(self):
        """Entry point for expression parsing (precedence-based)."""
        return self.parse_logic_or()
    
    # ==========================================
    # EXPRESSION PARSING (Precedence Cascade)
    # ==========================================

    def parse_logic_or(self):
        node = self.parse_logic_and()
        while self.match("||"):
            op = self.tokens[self.current - 1]
            right = self.parse_logic_and()
            node = ASTNode("LOGIC_OR", [node, right], value=op["value"], inferred_type="int")
        return node

    def parse_logic_and(self):
        node = self.parse_equality()
        while self.match("&&"):
            op = self.tokens[self.current - 1]
            right = self.parse_equality()
            node = ASTNode("LOGIC_AND", [node, right], value=op["value"], inferred_type="int")
        return node

    def parse_equality(self):
        node = self.parse_comparison()
        while self.match("==", "!="):
            op = self.tokens[self.current - 1]
            right = self.parse_comparison()
            node = ASTNode("EQUALITY", [node, right], value=op["value"], inferred_type="int")
        return node

    def parse_comparison(self):
        node = self.parse_term()
        while self.match(">", "<", ">=", "<="):
            op = self.tokens[self.current - 1]
            right = self.parse_term()
            node = ASTNode("COMPARISON", [node, right], value=op["value"], inferred_type="int")
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.match("+", "-"):
            op = self.tokens[self.current - 1]
            right = self.parse_factor()
            # Infiere el tipo basado en el nodo izquierdo
            node = ASTNode("TERM", [node, right], value=op["value"], inferred_type=node.inferred_type)
        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.match("*", "/", "%"):
            op = self.tokens[self.current - 1]
            right = self.parse_unary()
            node = ASTNode("FACTOR", [node, right], value=op["value"], inferred_type=node.inferred_type)
        return node

    def parse_unary(self):
        if self.match("!", "-"):
            op = self.tokens[self.current - 1]
            right = self.parse_unary()
            return ASTNode("UNARY", [right], value=op["value"], inferred_type=right.inferred_type)
        return self.parse_primary()

    def parse_primary(self):
        """Maneja números, identificadores y paréntesis."""
        token = self.peek()
        
        # 1. Identificadores (Variables)
        if self.match_type("Identifiers"):
            # SDT: Buscar en la tabla de símbolos para ver si existe y obtener su tipo
            sym = self.symbol_table.lookup(token["value"])
            if not sym:
                self.error(f"Undeclared variable '{token['value']}' used in expression")
                inf_type = "int" # Tipo por defecto para evitar crashear el compilador
            else:
                inf_type = sym.type
            return ASTNode("ID", [], value=token["value"], inferred_type=inf_type)
            
        # 2. Constantes (Números enteros o flotantes)
        # Nota: Ajusta "Constants" si tu lexer los llama "Numbers" o "Integer"
        elif self.match_type("Constants") or self.match_type("Numbers"): 
            t = "float" if "." in token["value"] else "int"
            return ASTNode("CONSTANT", [], value=token["value"], inferred_type=t)
            
        # 3. Literales (Caracteres o Strings)
        elif self.match_type("Literals") or self.match_type("Strings"):
            return ASTNode("LITERAL", [], value=token["value"], inferred_type="char")
            
        # 4. Paréntesis agrupadores ( E )
        elif self.match("("):
            expr = self.parse_expression()
            self.consume(")", "Expected ')' after expression")
            return expr
            
        # 5. Token inesperado
        else:
            self.error(f"Unexpected token in expression: '{token['value']}'")
            self.advance() # Consumir el token malo para evitar un bucle infinito
            return ASTNode("ERROR", [])

    # Fíjate que esta función está alineada a la misma altura que def parse_primary
    def get_derivation(self, ast=None):
        """
        Devuelve la lista de derivaciones gramaticales aplicadas durante el análisis.
        Acepta 'ast' para ser compatible con la llamada desde gui.py.
        """
        if self.derivation:
            return "\n".join(self.derivation)
        
        return "Análisis Sintáctico y Semántico completado exitosamente.\n(Árbol AST generado con éxito)."
