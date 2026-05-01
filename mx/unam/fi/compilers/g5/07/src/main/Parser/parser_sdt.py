from Ast.ASTNode import ASTNode
from Semantic.SymbolTable import SymbolTable


class Parser:

    TYPE_KEYWORDS = {"int", "float", "double", "char", "void", "string"}

    def __init__(self, tokens_list):

        unknown_tokens = [t for t in tokens_list if t["type"] == "Unknown"]
        if unknown_tokens:
            first_err = unknown_tokens[0]
            raise Exception(f"[Line {first_err['line']}] Lexical Error: Unknown token '{first_err['value']}'")

        self.tokens = tokens_list
        self.current = 0

        self.symbol_table = SymbolTable()
        self.current_function_type = None

        self.sdt_errors = []
        self.derivation = []

    # -------------------------
    # UTIL
    # -------------------------

    def log(self, msg):
        self.derivation.append(msg)

    def error(self, msg):
        self.sdt_errors.append(f"[Line {self.peek()['line']}] {msg}")

    def peek(self):
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return {"type": "EOF", "value": "$", "line": -1}

    def advance(self):
        if self.current < len(self.tokens):
            self.current += 1
        return self.tokens[self.current - 1]

    def match(self, val):
        if self.peek()["value"] == val:
            self.advance()
            return True
        return False

    def match_type(self, t):
        if self.peek()["type"] == t:
            return self.advance()
        return None

    def consume(self, val, msg):
        if self.peek()["value"] == val:
            return self.advance()
        raise Exception(f"[Line {self.peek()['line']}] {msg}")

    def consume_type(self, t, msg):
        if self.peek()["type"] == t:
            return self.advance()
        raise Exception(f"[Line {self.peek()['line']}] {msg}")

    def is_at_end(self):
        return self.peek()["type"] == "EOF"

    # -------------------------
    # PROGRAM
    # -------------------------

    def parse_program(self):
        self.log("Program -> Declaration*")

        nodes = []
        while not self.is_at_end():
            nodes.append(self.parse_global())

        return ASTNode("PROGRAM", nodes)

    # -------------------------
    # GLOBAL
    # -------------------------

    def parse_global(self):
        token = self.peek()

        if token["value"] == "class":
            return self.parse_class()

        type_token = token["value"]
        self.advance()
        id_token = self.consume_type("Identifiers", "Expected identifier")

        if self.peek()["value"] == "(":
            return self.parse_function(type_token, id_token)

        return self.parse_global_var(type_token, id_token)

    # -------------------------
    # CLASS
    # -------------------------

    def parse_class(self):
        self.consume("class", "Expected class")
        id_token = self.consume_type("Identifiers", "Expected identifier")

        self.log("ClassDeclaration -> 'class' Identifier '{' Declaration* '}'")
        self.log(f"Identifier -> {id_token['value']}")

        self.consume("{", "Expected '{'")

        body = []
        while self.peek()["value"] != "}":
            body.append(self.parse_global())

        self.consume("}", "Expected '}'")

        return ASTNode("CLASS", body, value=id_token["value"])

    # -------------------------
    # GLOBAL VAR
    # -------------------------

    def parse_global_var(self, t, id_token):

        self.log("VariableDeclaration -> Datatype Identifier ['=' Expression] ';'")
        self.log(f"Datatype -> {t}")
        self.log(f"Identifier -> {id_token['value']}")

        if not self.symbol_table.declare(id_token["value"], t, id_token["line"]):
            self.error(f"Duplicate variable '{id_token['value']}'")

        children = []

        if self.match("="):
            expr = self.parse_expression()
            children.append(expr)

            self.symbol_table.mark_as_initialized(id_token["value"])

        self.consume(";", "Expected ';'")

        return ASTNode("GLOBAL_VAR", children, value=id_token["value"], inferred_type=t)

    # -------------------------
    # FUNCTION
    # -------------------------

    def parse_function(self, t, id_token):

        self.log("FunctionDeclaration -> 'function' Datatype Identifier '(' ')' '{' Statement* '}'")
        self.log(f"Datatype -> {t}")
        self.log(f"Identifier -> {id_token['value']}")

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

    # -------------------------
    # STATEMENTS
    # -------------------------

    def parse_statement(self):

        token = self.peek()

        if token["value"] == "writeln":
            return self.parse_print()

        if token["value"] in self.TYPE_KEYWORDS:
            return self.parse_local_decl()

        if token["type"] == "Identifiers":
            id_t = self.advance()

            if self.match("="):
                expr = self.parse_expression()

                self.symbol_table.mark_as_initialized(id_t["value"])

                self.consume(";", "Expected ';'")
                return ASTNode("ASSIGN", [expr], value=id_t["value"])

            if self.match("("):
                self.consume(")", "Expected ')'")
                self.consume(";", "Expected ';'")
                return ASTNode("CALL", value=id_t["value"])

        raise Exception(f"[Line {token['line']}] Invalid statement")

    # -------------------------
    # PRINT
    # -------------------------

    def parse_print(self):

        self.log("PrintStatement -> 'writeln' '(' Expression ')' ';'")

        self.consume("writeln", "Expected writeln")
        self.consume("(", "Expected '('")

        expr = self.parse_expression()

        self.consume(")", "Expected ')'")
        self.consume(";", "Expected ';'")

        return ASTNode("PRINT", [expr])

    # -------------------------
    # LOCAL VAR
    # -------------------------

    def parse_local_decl(self):

        t = self.advance()["value"]
        id_token = self.consume_type("Identifiers", "Expected identifier")

        self.log("VariableDeclaration -> Datatype Identifier ['=' Expression] ';'")
        self.log(f"Datatype -> {t}")
        self.log(f"Identifier -> {id_token['value']}")

        if self.match("="):
            expr = self.parse_expression()
            self.symbol_table.mark_as_initialized(id_token["value"])
        else:
            expr = None

        self.consume(";", "Expected ';'")

        return ASTNode("LOCAL_VAR", [expr] if expr else [], value=id_token["value"], inferred_type=t)

    # -------------------------
    # EXPRESSIONS
    # -------------------------

    def parse_expression(self):
        self.log("Expression -> Assignment")
        return self.parse_logic_or()

    def parse_logic_or(self):
        node = self.parse_logic_and()
        return node

    def parse_logic_and(self):
        node = self.parse_equality()
        return node

    def parse_equality(self):
        node = self.parse_comparison()
        return node

    def parse_comparison(self):
        node = self.parse_term()
        return node

    def parse_term(self):
        node = self.parse_factor()
        return node

    def parse_factor(self):
        node = self.parse_unary()
        return node

    def parse_unary(self):
        return self.parse_primary()

    # -------------------------
    # PRIMARY
    # -------------------------

    def parse_primary(self):

        if t := self.match_type("Identifiers"):
            return ASTNode("ID", value=t["value"])

        if t := self.match_type("Constants"):
            self.log(f"Literal -> {t['value']}")
            return ASTNode("CONST", value=t["value"])

        if t := self.match_type("Literals"):
            self.log(f"Literal -> {t['value']}")
            return ASTNode("LITERAL", value=t["value"])

        if self.match("("):
            node = self.parse_expression()
            self.consume(")", "Expected ')'")
            return node

        raise Exception(f"[Line {self.peek()['line']}] Expected expression")

    # -------------------------
    # OUTPUT
    # -------------------------

    def get_derivation(self, ast=None):
        report = []

        report.append("Derivation Steps:\n")
        report.extend(self.derivation)

        report.append("\n------------------------------")
        report.append("Abstract Syntax Tree (AST):")

        report.append(str(ast) if ast else "(No AST)")

        all_errors = self.sdt_errors + self.symbol_table.errors

        if all_errors:
            report.append("\nSEMANTIC ERRORS:")
            report.extend(all_errors)
        else:
            report.append("\nSEMANTIC STATUS: Verified")

        return "\n".join(report)