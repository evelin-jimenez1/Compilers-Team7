from Ast.ASTNode import ASTNode
from Semantic.SymbolTable import SymbolTable


class Parser:

    TYPE_KEYWORDS = {"int", "float", "double", "char", "void"}

    def __init__(self, tokens_list):

        unknown_tokens = [t for t in tokens_list if t["type"] == "Unknown"]
        if unknown_tokens:
            first_err = unknown_tokens[0]
            raise Exception(f"[Line {first_err['line']}] Lexical Error: Unknown token '{first_err['value']}'")

        self.tokens = tokens_list
        self.current = 0
        self.derivation = []

        self.symbol_table = SymbolTable()
        self.current_function_type = None
        self.sdt_errors = []

    # -------------------------
    # UTIL
    # -------------------------

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

    def match(self, *values):
        if self.peek()["value"] in values:
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
        nodes = []
        while not self.is_at_end():
            nodes.append(self.parse_global())
        return ASTNode("PROGRAM", nodes)

    def parse_global(self):
        type_token = self.peek()

        if type_token["value"] not in self.TYPE_KEYWORDS:
            raise Exception(f"[Line {type_token['line']}] Expected type")

        data_type = self.advance()["value"]
        id_token = self.consume_type("Identifiers", "Expected identifier")

        if self.peek()["value"] == "(":
            return self.parse_function(data_type, id_token)
        return self.parse_global_var(data_type, id_token)

    # -------------------------
    # GLOBAL VAR
    # -------------------------

    def parse_global_var(self, t, id_token):

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

    # -------------------------
    # FUNCTION
    # -------------------------

    def parse_function(self, t, id_token):

        if not self.symbol_table.declare(id_token["value"], t, id_token["line"], is_func=True):
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

    # -------------------------
    # STATEMENTS
    # -------------------------

    def parse_statement(self):

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

            if self.match("("):
                self.consume(")", "Expected ')'")

                sym = self.symbol_table.lookup(id_t["value"])
                if not sym or not sym.is_func:
                    self.error(f"'{id_t['value']}' is not a function")

                self.consume(";", "Expected ';'")
                return ASTNode("CALL", value=id_t["value"])

        raise Exception(f"[Line {token['line']}] Invalid statement")

    # -------------------------
    # IF
    # -------------------------

    def parse_if(self):

        self.consume("if", "Expected if")
        self.consume("(", "Expected '('")

        cond = self.parse_expression()

        if cond.inferred_type not in {"int", "float", "double"}:
            self.error("Invalid condition type")

        self.consume(")", "Expected ')'")

        self.consume("{", "Expected '{'")

        self.symbol_table.enter_scope()

        then_body = []
        while self.peek()["value"] != "}":
            then_body.append(self.parse_statement())

        self.consume("}", "Expected '}'")

        self.symbol_table.exit_scope()

        else_body = []

        if self.match("else"):
            self.consume("{", "Expected '{'")

            self.symbol_table.enter_scope()

            while self.peek()["value"] != "}":
                else_body.append(self.parse_statement())

            self.consume("}", "Expected '}'")
            self.symbol_table.exit_scope()

        return ASTNode("IF", [cond, ASTNode("THEN", then_body), ASTNode("ELSE", else_body)])

    # -------------------------
    # LOCAL DECL
    # -------------------------

    def parse_local_decl(self):

        t = self.advance()["value"]
        id_token = self.consume_type("Identifiers", "Expected identifier")

        if t == "void":
            self.error("Local variable cannot be void")

        if not self.symbol_table.declare(id_token["value"], t, id_token["line"]):
            self.error(f"Duplicate variable '{id_token['value']}'")

        children = []

        if self.match("="):
            expr = self.parse_expression()

            if expr.inferred_type != t:
                self.error("Type mismatch in initialization")

            children.append(expr)
            self.symbol_table.mark_as_initialized(id_token["value"])

        self.consume(";", "Expected ';'")

        return ASTNode("LOCAL_VAR", children, value=id_token["value"], inferred_type=t)

    # -------------------------
    # EXPRESSIONS
    # -------------------------

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
        while self.peek()["value"] in {">", "<", ">=", "<="}:
            op = self.advance()["value"]
            right = self.parse_term()
            node = ASTNode("BIN_OP", [node, right], value=op, inferred_type="int")
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek()["value"] in {"+", "-"}:
            op = self.advance()["value"]
            right = self.parse_factor()

            if node.inferred_type == "string" or right.inferred_type == "string":
                self.error("Invalid arithmetic with string")

            t = self._infer(node.inferred_type, right.inferred_type)
            node = ASTNode("BIN_OP", [node, right], value=op, inferred_type=t)

        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.peek()["value"] in {"*", "/", "%"}:
            op = self.advance()["value"]
            right = self.parse_unary()

            t = self._infer(node.inferred_type, right.inferred_type)
            node = ASTNode("BIN_OP", [node, right], value=op, inferred_type=t)

        return node

    def parse_unary(self):
        if self.peek()["value"] in {"!", "-"}:
            op = self.advance()["value"]
            child = self.parse_unary()
            return ASTNode("UNARY", [child], value=op, inferred_type=child.inferred_type)
        return self.parse_primary()

    def parse_primary(self):

        if t := self.match_type("Identifiers"):
            sym = self.symbol_table.lookup(t["value"])

            if not sym:
                self.error(f"Undeclared variable '{t['value']}'")
                return ASTNode("ID", value=t["value"], inferred_type="unknown")

            if not sym.initialized and not sym.is_func:
                self.error(f"Variable '{t['value']}' used before initialization")

            return ASTNode("ID", value=t["value"], inferred_type=sym.type)

        if t := self.match_type("Constants"):
            val = t["value"]
            return ASTNode("CONST", value=val, inferred_type="double" if "." in val else "int")

        if t := self.match_type("Literals"):
            return ASTNode("LITERAL", value=t["value"], inferred_type="string")

        if self.match("("):
            node = self.parse_expression()
            self.consume(")", "Expected ')'")
            return node

        raise Exception(f"[Line {self.peek()['line']}] Expected expression")

    # -------------------------
    # TYPES
    # -------------------------

    def _infer(self, t1, t2):
        if "double" in {t1, t2}:
            return "double"
        if "float" in {t1, t2}:
            return "float"
        return "int"
    def get_derivation(self, ast=None):
        report = []

        report.append("Parsing Success!\n")

        report.append("Derivation:")
        if self.derivation:
            report.extend(self.derivation)
        else:
            report.append("(No derivation tracked)")

        report.append("\n" + "-" * 30)
        report.append("Abstract Syntax Tree (AST):")

        if ast:
            report.append(str(ast))
        else:
            report.append("(No AST generated)")

        # Unir errores semánticos
        all_errors = self.sdt_errors + self.symbol_table.errors

        if all_errors:
            report.append("\nSEMANTIC ERRORS FOUND:")
            report.extend(all_errors)
        else:
            report.append("\nSEMANTIC STATUS: Verified (No Errors)")

        return "\n".join(report)