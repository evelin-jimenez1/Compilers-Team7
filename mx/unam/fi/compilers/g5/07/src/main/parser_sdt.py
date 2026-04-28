"""
Recursive Descent Parser + Syntax-Directed Translation (SDT)
------------------------------------------------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date: April 28, 2026

Description:
This module performs Syntax Analysis (Parsing) and Semantic Analysis (SDT) 
simultaneously. It constructs an Abstract Syntax Tree (AST) while verifying 
type compatibility and scope rules using a Symbol Table.

Grammar Compliance: LL(1) Top-Down
Intermediate Representation: AST
"""

from SymbolTable import SymbolTable
from ASTNode import ASTNode

class Parser:
    """
    Predictive Parser for the C-Pure Language.
    
    Attributes:
        tokens (list): Stream of tokens from the Lexer.
        current (int): Index of the lookahead token.
        symbol_table (SymbolTable): Manages scopes and identifier metadata.
        derivation (list): Tracks applied grammar rules for documentation.
        sdt_errors (list): Collects semantic violations found during parsing.
    """
    
    TYPE_KEYWORDS = {"int", "float", "double", "char", "void"}

    def __init__(self, tokens_list):
        # Initial check for Lexical errors
        unknown_tokens = [t for t in tokens_list if t["type"] == "Unknown"]
        if unknown_tokens:
            first_err = unknown_tokens[0]
            raise Exception(f"[Line {first_err['line']}] Lexical Error: Unknown token '{first_err['value']}'")

        self.tokens = tokens_list
        self.current = 0
        self.derivation = []
        
        # Semantic Components
        self.symbol_table = SymbolTable()
        self.current_function_type = None
        self.sdt_errors = []

    # ------------------------------------------------------------
    # Token Navigation & Predictive Control
    # ------------------------------------------------------------

    def peek(self):
        """ Returns the current lookahead token without consuming it. """
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return {"type": "EOF", "value": "$", "line": -1, "column": -1}

    def advance(self):
        """ Consumes and returns the current token. """
        if not self.is_at_end():
            self.current += 1
        return self.tokens[self.current - 1]

    def is_at_end(self):
        return self.peek()["type"] == "EOF"

    def match(self, *values):
        """ Checks if the lookahead matches any of the given values. Consumes if True. """
        if self.peek()["value"] in values:
            self.advance()
            return True
        return False

    def match_type(self, type_name):
        """ Checks if the lookahead matches a specific token category. """
        if self.peek()["type"] == type_name:
            self.advance()
            return True
        return False

    def consume(self, expected_value, message):
        """ Forces a match with a specific value or raises a Syntax Error. """
        if self.peek()["value"] == expected_value:
            return self.advance()
        raise Exception(f"[Line {self.peek()['line']}] Syntax Error: {message} (found '{self.peek()['value']}')")

    def consume_type(self, expected_type, message):
        """ Forces a match with a token category or raises a Syntax Error. """
        if self.peek()["type"] == expected_type:
            return self.advance()
        raise Exception(f"[Line {self.peek()['line']}] Syntax Error: {message}")

    # ------------------------------------------------------------
    # Grammar Rules (BNF Implementation)
    # ------------------------------------------------------------

    def parse_program(self):
        """ <PROGRAM> ::= <GLOBAL_LIST> """
        self.log("<PROGRAM> ::= <GLOBAL_LIST>")
        nodes = []
        while not self.is_at_end():
            nodes.append(self.parse_global_decl())
        return ASTNode("PROGRAM", nodes)

    def parse_global_decl(self):
        """ <GLOBAL> ::= <TYPE> id <GLOBAL_REST> """
        self.log("<GLOBAL> ::= <TYPE> id <GLOBAL_REST>")
        
        type_token = self.peek()
        if type_token["value"] not in self.TYPE_KEYWORDS:
            raise Exception(f"[Line {type_token['line']}] Syntax Error: Expected data type")
        
        data_type = self.advance()["value"]
        id_token = self.consume_type("Identifiers", "Expected identifier name")
        
        # Predictive decision based on Lookahead '('
        if self.peek()["value"] == "(":
            return self.parse_function_decl(data_type, id_token)
        return self.parse_global_variable(data_type, id_token)

    def parse_function_decl(self, ret_type, id_t):
        """ Handles function declaration and body scoping. """
        self.symbol_table.declare(id_t["value"], ret_type, id_t["line"], is_func=True)
        
        self.consume("(", "Expected '('")
        self.consume(")", "Expected ')'") # Argument lists can be added here
        self.consume("{", "Expected '{'")
        
        # SDT: Switch context to function scope
        self.symbol_table.enter_scope()
        self.current_function_type = ret_type
        
        body = []
        while self.peek()["value"] != "}" and not self.is_at_end():
            body.append(self.parse_statement())
            
        self.consume("}", "Expected '}'")
        self.symbol_table.exit_scope()
        self.current_function_type = None # Reset context
        
        return ASTNode("FUNCTION", body, value=f"{ret_type} {id_t['value']}", inferred_type=ret_type)

    def parse_statement(self):
        """ 
        <STMT> ::= <IF_STMT> | return <E>; | <TYPE> id; | id = <E>; 
        """
        token = self.peek()

        if token["value"] == "if":
            return self.parse_if_stmt()
            
        if token["value"] == "return":
            self.advance()
            expr = self.parse_expression() if self.peek()["value"] != ";" else None
            self.consume(";", "Expected ';'")
            return ASTNode("RETURN", [expr] if expr else [])

        if token["value"] in self.TYPE_KEYWORDS:
            return self.parse_local_decl()

        if token["type"] == "Identifiers":
            id_t = self.advance()
            if self.match("="):
                expr = self.parse_expression()
                self.consume(";", "Expected ';'")
                
                # SDT: Verify variable exists and mark initialized
                sym = self.symbol_table.lookup(id_t["value"])
                if not sym:
                    # Si no existe en la tabla, lanzamos el error semántico
                    self.sdt_errors.append(f"[Line {id_t['line']}] SDT Error: Variable '{id_t['value']}' was not declared before assignment.")
                else:
                    # Si sí existe, la marcamos como inicializada
                    self.symbol_table.mark_as_initialized(id_t["value"])
                    
                return ASTNode("ASSIGN", [expr], value=id_t["value"])
            
            if self.match("("):
                # Simple function call
                self.consume(")", "Expected ')'")
                self.consume(";", "Expected ';'")
                return ASTNode("CALL", value=id_t["value"])

        raise Exception(f"[Line {token['line']}] Syntax Error: Invalid statement start '{token['value']}'")

    def parse_local_decl(self):
            """ <STMT> ::= <TYPE> id <OPT_ASSIGN_LOCAL> ; """
            self.log("<STMT> ::= <TYPE> id <OPT_ASSIGN_LOCAL> ;")
            
            # Consumimos el tipo de dato y el identificador
            data_type = self.advance()["value"]
            id_token = self.consume_type("Identifiers", "Expected variable name")
            var_name = id_token["value"]
            
            # SDT: Declarar en la tabla de símbolos
            self.symbol_table.declare(var_name, data_type, id_token["line"])
            
            children = []
            if self.match("="):
                expr = self.parse_expression()
                children.append(expr)
                # SDT: Marcar como inicializada
                self.symbol_table.mark_as_initialized(var_name)
                
            self.consume(";", "Expected ';' after variable declaration")
            
            return ASTNode("LOCAL_VAR", children, value=f"{data_type} {var_name}", inferred_type=data_type)

    def parse_if_stmt(self):
        """ <IF_STMT> ::= if ( <E> ) { <STMT_LIST> } <ELSE_PART> """
        self.log("<IF_STMT> ::= if ( <E> ) { <STMT_LIST> } <ELSE_PART>")
        
        self.consume("if", "Expected 'if'")
        self.consume("(", "Expected '(' after 'if'")
        condition = self.parse_expression()
        self.consume(")", "Expected ')' after condition")
        
        # Parseamos el bloque THEN
        self.consume("{", "Expected '{' to start 'if' block")
        then_body = []
        while self.peek()["value"] != "}" and not self.is_at_end():
            then_body.append(self.parse_statement())
        self.consume("}", "Expected '}' to close 'if' block")
        
        # Parseamos el bloque ELSE (Opcional)
        else_body = []
        if self.match("else"):
            self.log("<ELSE_PART> ::= else { <STMT_LIST> }")
            self.consume("{", "Expected '{' to start 'else' block")
            while self.peek()["value"] != "}" and not self.is_at_end():
                else_body.append(self.parse_statement())
            self.consume("}", "Expected '}' to close 'else' block")
        else:
            self.log("<ELSE_PART> ::= epsilon")
            
        # Construcción del AST para control de flujo
        then_node = ASTNode("THEN", then_body)
        children = [condition, then_node]
        if else_body:
            children.append(ASTNode("ELSE", else_body))
            
        return ASTNode("IF", children)

    def parse_global_variable(self, data_type, id_token):
        """ <GLOBAL_REST> ::= <OPT_ASSIGN> ; """
        self.log("<GLOBAL_REST> ::= <OPT_ASSIGN> ;")
        
        var_name = id_token["value"]
        self.symbol_table.declare(var_name, data_type, id_token["line"])
        
        children = []
        if self.match("="):
            expr = self.parse_expression()
            children.append(expr)
            self.symbol_table.mark_as_initialized(var_name)
            
        self.consume(";", "Expected ';' after global variable declaration")
        
        return ASTNode("GLOBAL_VAR", children, value=f"{data_type} {var_name}", inferred_type=data_type)
    # ------------------------------------------------------------
    # Expression Hierarchy (LL1 Non-Recursive Loops)
    # ------------------------------------------------------------


    def parse_expression(self):
        return self.parse_logic_or()

    def parse_logic_or(self):
        node = self.parse_logic_and()
        while self.match("||"):
            right = self.parse_logic_and()
            node = ASTNode("BIN_OP", [node, right], value="||", inferred_type="int")
        return node

    def parse_logic_and(self):
        node = self.parse_equality()
        while self.match("&&"):
            right = self.parse_equality()
            node = ASTNode("BIN_OP", [node, right], value="&&", inferred_type="int")
        return node

    def parse_equality(self):
        node = self.parse_comparison()
        while self.peek()["value"] in {"==", "!="}:
            op = self.advance()["value"]
            right = self.parse_comparison()
            node = ASTNode("BIN_OP", [node, right], value=op, inferred_type="int")
        return node

    def parse_comparison(self):
        node = self.parse_term()
        while self.peek()["value"] in {">", ">=", "<", "<="}:
            op = self.advance()["value"]
            right = self.parse_term()
            node = ASTNode("BIN_OP", [node, right], value=op, inferred_type="int")
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek()["value"] in {"+", "-"}:
            op = self.advance()["value"]
            right = self.parse_factor()
            # SDT: Type inference for arithmetic
            res_t = self._infer_arithmetic_type(node.inferred_type, right.inferred_type)
            node = ASTNode("BIN_OP", [node, right], value=op, inferred_type=res_t)
        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.peek()["value"] in {"*", "/", "%"}:
            op = self.advance()["value"]
            right = self.parse_unary()
            res_t = self._infer_arithmetic_type(node.inferred_type, right.inferred_type)
            node = ASTNode("BIN_OP", [node, right], value=op, inferred_type=res_t)
        return node

    def parse_unary(self):
        if self.peek()["value"] in {"!", "-"}:
            op = self.advance()["value"]
            child = self.parse_unary()
            return ASTNode("UNARY", [child], value=op, inferred_type=child.inferred_type)
        return self.parse_primary()

    def parse_primary(self):
        """ <PRIMARY> ::= id | constant | literal | ( E ) """
        token = self.peek()

        if self.match_type("Identifiers"):
            val = self.tokens[self.current - 1]["value"]
            sym = self.symbol_table.lookup(val)
            inf_t = sym.type if sym else "unknown"
            if not sym:
                self.sdt_errors.append(f"[Line {token['line']}] SDT Error: Undeclared ID '{val}'")
            return ASTNode("ID", value=val, inferred_type=inf_t)

        if self.match_type("Constants"):
            val = self.tokens[self.current - 1]["value"]
            inf_t = "double" if "." in val else "int"
            return ASTNode("CONST", value=val, inferred_type=inf_t)

        if self.match_type("Literals"):
            return ASTNode("LITERAL", value=self.tokens[self.current - 1]["value"], inferred_type="string")

        if self.match("("):
            node = self.parse_expression()
            self.consume(")", "Expected ')'")
            return node

        raise Exception(f"[Line {token['line']}] Syntax Error: Expected primary expression")

    # ------------------------------------------------------------
    # Utility & Output Methods
    # ------------------------------------------------------------

    def _infer_arithmetic_type(self, t1, t2):
        """ Semantic Helper: Logic for type promotion (e.g., int + double -> double) """
        if "double" in {t1, t2}: return "double"
        if "float" in {t1, t2}: return "float"
        return "int"

    def log(self, rule):
        self.derivation.append(rule)

    def get_derivation(self, ast=None):
        """ Generates the final project report for the GUI. """
        report = ["Parsing Success!\n", "Derivation:"]
        report.extend(self.derivation)
        report.append("\n" + "-"*30)
        report.append("Abstract Syntax Tree (AST):")
        report.append(str(ast))
        
        # Merge all errors
        all_errors = self.sdt_errors + self.symbol_table.errors
        if all_errors:
            report.append("\nSEMANTIC ERRORS FOUND:")
            report.extend(all_errors)
        else:
            report.append("\nSEMANTIC STATUS: Verified (No Errors)")
            
        return "\n".join(report)