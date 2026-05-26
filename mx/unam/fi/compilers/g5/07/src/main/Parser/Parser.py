"""
LL(1) Predictive Parser - AST Builder & Auto-Fix Edition
--------------------------------------------------------
Authors: Team 7
Date: May 2026

Description:
This module implements the execution driver for the LL(1) syntax analyzer. 
It incorporates a Semantic Stack to dynamically construct the AST and 
includes a fail-safe to correct Lexer misclassifications on the fly.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Ast.ASTNode import ASTNode


# ─────────────────────────────────────────────────────────────────────────────
# Diagnostic table
# Each entry: (non_terminal, lookahead) → (message, use_last_line)
#   use_last_line = True  → the real error is on the PREVIOUS line
#                           (something was missing there, e.g. a ';')
#   use_last_line = False → the error is on the CURRENT line
# ─────────────────────────────────────────────────────────────────────────────

_DIAGNOSTICS = {

    # ── Missing semicolons ────────────────────────────────────────────────────
    # After "id STMT_ID_REST": we consumed the identifier but the next token
    # is not '=', '(', '++', '--' → the statement on the previous line is
    # missing its semicolon.
    ('STMT_ID_REST', '}')      : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'id')     : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'int')    : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'float')  : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'double') : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'char')   : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'return') : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'if')     : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'while')  : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', 'for')    : ("Missing ';' after statement.",             True),
    ('STMT_ID_REST', '$')      : ("Missing ';' at end of file.",              True),
    ('STMT_ID_REST', ';')      : ("Missing '=', '()', '++', or '--' after identifier.", False),

    # After "TYPE id OPT_ASSIGN": next token is not '=' or ';'
    ('OPT_ASSIGN',  'id')      : ("Missing ';' after variable declaration.",  True),
    ('OPT_ASSIGN',  '}')       : ("Missing ';' after variable declaration.",  True),
    ('OPT_ASSIGN',  'return')  : ("Missing ';' after variable declaration.",  True),
    ('OPT_ASSIGN',  'if')      : ("Missing ';' after variable declaration.",  True),
    ('OPT_ASSIGN',  'while')   : ("Missing ';' after variable declaration.",  True),
    ('OPT_ASSIGN',  'for')     : ("Missing ';' after variable declaration.",  True),
    ('OPT_ASSIGN',  '$')       : ("Missing ';' at end of file.",              True),

    # After "return OPT_E": next token is not ';'
    ('OPT_E',  'id')           : ("Missing ';' after return statement.",      True),
    ('OPT_E',  '}')            : ("Missing ';' after return statement.",      True),
    ('OPT_E',  '$')            : ("Missing ';' at end of file.",              True),

    # STMT can't start with these — usually means the previous stmt lost its ';'
    ('STMT',   '}')            : ("Missing ';' before '}'.",                  True),
    ('STMT',   '$')            : ("Missing ';' at end of file.",              True),

    # ── Missing closing braces ────────────────────────────────────────────────
    # ELSE_PART is optional ('else' or epsilon).  When the parser is here and
    # sees something that is NOT 'else' and also NOT a valid FOLLOW(ELSE_PART),
    # it means the if-body was never closed with '}'.
    ('ELSE_PART', '$')         : ("Missing '}' — unclosed 'if' block.",       True),
    ('ELSE_PART', 'return')    : ("Missing '}' to close 'if' block.",         True),
    ('ELSE_PART', 'id')        : ("Missing '}' to close 'if' block.",         True),
    ('ELSE_PART', 'int')       : ("Missing '}' to close 'if' block.",         True),
    ('ELSE_PART', 'float')     : ("Missing '}' to close 'if' block.",         True),
    ('ELSE_PART', 'double')    : ("Missing '}' to close 'if' block.",         True),
    ('ELSE_PART', 'char')      : ("Missing '}' to close 'if' block.",         True),
    ('ELSE_PART', 'while')     : ("Missing '}' to close 'if' block.",         True),
    ('ELSE_PART', 'for')       : ("Missing '}' to close 'if' block.",         True),
    ('ELSE_PART', 'do')        : ("Missing '}' to close 'if' block.",         True),

    # Unclosed blocks detected at end-of-file or unexpected '}'
    ('STMT_LIST', '$')         : ("Unexpected end of file — missing closing '}'.",                    False),
    ('STMT_LIST', '}')         : ("Unexpected '}' — possibly a missing ';' on the previous line.",    True),

    # ── Missing opening/closing parentheses ───────────────────────────────────
    ('PARAMS',     ')')        : ("Expected a type keyword in parameter list, or ')' to close it.",  False),
    ('PARAMS_REST','id')       : ("Missing ',' between parameters.",                                  False),
    ('ARGS_REST',  'id')       : ("Missing ',' between arguments.",                                   False),
    ('ARGS_REST',  'constant') : ("Missing ',' between arguments.",                                   False),
    ('ARGS_REST',  'literal')  : ("Missing ',' between arguments.",                                   False),

    # ── Expression errors ─────────────────────────────────────────────────────
    ('PRIMARY', ';')           : ("Missing value or expression before ';'.",  False),
    ('PRIMARY', ')')           : ("Missing value or expression before ')'.",  False),
    ('PRIMARY', '}')           : ("Missing value or expression before '}'.",  False),
    ('PRIMARY', '+')           : ("Missing left-hand operand for '+'.",       False),
    ('PRIMARY', '-')           : ("Missing left-hand operand for '-'.",       False),
    ('PRIMARY', '*')           : ("Missing left-hand operand for '*'.",       False),
    ('PRIMARY', '/')           : ("Missing left-hand operand for '/'.",       False),
    ('PRIMARY', '%')           : ("Missing left-hand operand for '%'.",       False),
    ('PRIMARY', '=')           : ("Expected a value on the right side of '='.", False),
    ('PRIMARY', '==')          : ("Missing left-hand operand for '=='.",      False),
    ('PRIMARY', '!=')          : ("Missing left-hand operand for '!='.",      False),
    ('PRIMARY', '>')           : ("Missing left-hand operand for '>'.",       False),
    ('PRIMARY', '<')           : ("Missing left-hand operand for '<'.",       False),
    ('PRIMARY', '>=')          : ("Missing left-hand operand for '>='.",      False),
    ('PRIMARY', '<=')          : ("Missing left-hand operand for '<='.",      False),

    ('UNARY',   ';')           : ("Incomplete expression before ';'.",        False),
    ('UNARY',   ')')           : ("Incomplete expression before ')'.",        False),
    ('UNARY',   '}')           : ("Incomplete expression before '}'.",        False),

    ('E',       ')')           : ("Empty expression inside parentheses.",     False),
    ('E',       ';')           : ("Missing expression.",                      False),
    ('E',       '}')           : ("Missing expression before '}'.",           False),

    # ── Control flow — if ─────────────────────────────────────────────────────
    ('ELSE_CHOICE', 'id')      : ("Expected '{' or 'if' after 'else'.",       False),
    ('ELSE_CHOICE', ';')       : ("Expected '{' or 'if' after 'else', not ';'.", False),
    ('ELSE_CHOICE', '$')       : ("Expected '{' or 'if' after 'else'.",       False),

    # ── Control flow — for ────────────────────────────────────────────────────
    ('FOR_UPD',     ')')       : ("Missing update expression in 'for' (e.g. i++, i--, i=...).", False),
    ('FOR_UPD_REST',')')       : ("Incomplete update expression in 'for' loop.",                 False),

    # ── Type errors ───────────────────────────────────────────────────────────
    ('TYPE',  'id')            : ("Missing type keyword (int, float, double, char, void) before identifier.", False),
    ('TYPE',  ';')             : ("Missing type keyword before ';'.",         False),
    ('TYPE',  '(')             : ("Missing type keyword before '('.",         False),
    ('TYPE',  '{')             : ("Missing type keyword before '{'.",         False),
    ('TYPE',  '=')             : ("Missing type keyword before '='.",         False),
    ('TYPE',  '$')             : ("Unexpected end of file — expected a type keyword.", False),

    # ── Global-level errors ───────────────────────────────────────────────────
    ('GLOBAL_REST', ';')       : ("Missing '(' for a function or ';' for a global variable.", False),
    ('GLOBAL_REST', 'id')      : ("Missing '(' or ';' after identifier.",     False),
    ('GLOBAL_REST', '{')       : ("Missing '(' and parameter list before '{'.", False),
}


# ── Fallback context messages (used when no exact match exists) ───────────────
_CONTEXT_FALLBACK = {
    'IF_STMT'      : "Inside 'if' — check that condition uses '(' ')' and body uses '{{' '}}'.",
    'ELSE_PART'    : "After 'if' block — missing '}' or unexpected token.",
    'WHILE_STMT'   : "Inside 'while' — check that condition uses '(' ')' and body uses '{{' '}}'.",
    'DO_WHILE_STMT': "Inside 'do-while' — check closing 'while ( condition );'.",
    'FOR_STMT'     : "Inside 'for' — check initializer, condition, and update sections.",
    'FOR_INIT'     : "In 'for' initializer — expected a declaration or assignment.",
    'FOR_UPD'      : "In 'for' update — expected 'id++', 'id--', or 'id = ...'.",
    'STMT'         : "Expected a statement: declaration, assignment, if, while, for, or return.",
    'STMT_LIST'    : "In statement block — possibly a missing ';' on the previous line.",
    'STMT_ID_REST' : "After identifier — expected '=', '(', '++', or '--', or missing ';'.",
    'PARAMS'       : "In parameter list — expected a type keyword or ')'.",
    'PARAMS_REST'  : "In parameter list — expected ',' or ')'.",
    'ARGS'         : "In argument list — expected an expression or ')'.",
    'ARGS_REST'    : "In argument list — expected ',' or ')'.",
    'GLOBAL'       : "At top level — expected a type keyword to start a declaration or function.",
    'GLOBAL_REST'  : "After identifier — expected '(' for function or ';' for variable.",
    'OPT_ASSIGN'   : "In variable declaration — expected '=' followed by a value, or ';'.",
    'OPT_E'        : "After 'return' — expected an expression or ';'.",
    'TYPE'         : "Expected a type keyword (int, float, double, char, void).",
    'PRIMARY'      : "Expected a value: variable name, number, or '(' expression ')'.",
    'E'            : "Expected an expression.",
    'UNARY'        : "Incomplete expression.",
    'FACTOR'       : "Expected a term in the expression.",
    'TERM'         : "Expected a factor in the expression.",
    'COMPARISON'   : "Expected a comparison expression.",
    'EQUALITY'     : "Expected an equality expression.",
    'LOGIC_AND'    : "Expected a logical AND expression.",
    'LOGIC_OR'     : "Expected a logical OR expression.",
}

_CONTEXT_PRIORITY = list(_CONTEXT_FALLBACK.keys())  # lookup order


def _diagnose(top, lookahead, stack):
    """
    Returns (message, use_last_line).
    Looks up the exact table first, then scans the stack for context.
    """
    key = (top, lookahead)

    # 1. Exact match
    if key in _DIAGNOSTICS:
        msg, use_last = _DIAGNOSTICS[key]
        return msg, use_last

    # 2. Stack context — walk from top of stack downward
    for frame in reversed(stack):
        if isinstance(frame, str) and frame in _CONTEXT_FALLBACK:
            return (
                f"Unexpected '{lookahead}'. {_CONTEXT_FALLBACK[frame]}",
                False,
            )

    # 3. Generic
    return f"Unexpected token '{lookahead}'.", False


class Parser:
    def __init__(self, parsing_table, start_symbol):
        self.parsing_table = parsing_table
        self.start_symbol  = start_symbol

    def _get_grammar_symbol(self, token):
        """
        Translates Lexer categories/values to the exact Grammar symbols.
        Includes a patch to force recognition of reserved keywords.
        """
        t_type = token['type']
        t_val  = token['value']

        reserved = ['int', 'float', 'void', 'char', 'double',
                    'if', 'else', 'while', 'for', 'return', 'do']

        if t_type == 'Keywords' or t_val in reserved:
            return t_val
        elif t_type == 'Identifiers':
            return 'id'
        elif t_type == 'Constants':
            return 'constant'
        elif t_type == 'Literals':
            return 'literal'
        elif t_type in ['Operators', 'Punctuation']:
            return t_val
        return t_type

    def parse(self, token_stream):
        """
        Processes the token stream. If valid, builds and returns the AST.
        """
        tokens = list(token_stream) + [{'type': '$', 'value': '$', 'line': -1}]
        stack      = ['$', self.start_symbol]
        node_stack = []

        token_index   = 0
        current_token = tokens[token_index]
        last_token    = None  # last successfully matched terminal

        while len(stack) > 0:
            top = stack[-1]

            # ── Semantic action: build AST node ──────────────────────────────
            if isinstance(top, tuple) and top[0] == '#BUILD':
                stack.pop()
                _, nt_type, num_children = top

                children = []
                for _ in range(num_children):
                    if node_stack:
                        children.insert(0, node_stack.pop())

                node_stack.append(ASTNode(node_type=nt_type, children=children))
                continue

            lookahead_key   = self._get_grammar_symbol(current_token)
            lookahead_value = current_token['value']
            current_line    = current_token['line']
            last_line       = last_token['line'] if last_token else current_line

            # ── Case 1: Match terminal ────────────────────────────────────────
            if top == lookahead_key:
                stack.pop()
                node_stack.append(ASTNode(node_type=top, value=lookahead_value))
                last_token = current_token  # track last successfully consumed token

                token_index += 1
                if token_index < len(tokens):
                    current_token = tokens[token_index]

            # ── Case 2: Terminal mismatch ─────────────────────────────────────
            # The stack expected a specific terminal but got something else.
            # This is the most precise error: we know exactly what was missing.
            elif top not in self.parsing_table:
                readable = {
                    ';': "';'", '(': "'('", ')': "')'",
                    '{': "'{'", '}': "'}'", ',': "','", '=': "'='",
                }
                expected = readable.get(top, f"'{top}'")
                # ';' missing → blame the line where the statement ended, not
                # the line where the next token appears.
                report_line = last_line if top == ';' and last_line > 0 else current_line
                raise SyntaxError(
                    f"Line {report_line}: Expected {expected} but got '{lookahead_value}'."
                )

            # ── Case 3: Expand non-terminal ───────────────────────────────────
            else:
                raw_cell = self.parsing_table[top].get(lookahead_key, [])

                if not raw_cell:
                    msg, use_last = _diagnose(top, lookahead_key, stack)
                    report_line  = last_line if use_last and last_line > 0 else current_line
                    raise SyntaxError(f"Line {report_line}: {msg}")

                body = raw_cell[0].split("->")[1].strip().split()
                stack.pop()

                if body == ['epsilon']:
                    stack.append(('#BUILD', top, 0))
                else:
                    stack.append(('#BUILD', top, len(body)))
                    for symbol in reversed(body):
                        stack.append(symbol)

        if node_stack:
            return node_stack[0]
        return None