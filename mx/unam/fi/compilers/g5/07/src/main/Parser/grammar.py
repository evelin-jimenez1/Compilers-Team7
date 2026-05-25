"""
C Grammar Specification
-----------------------------------
Authors: Team 7
Date: April 28, 2026
"""

class Grammar:
    """
    The Grammar class holds the CFG rules for C-Pure.
    """
    def __init__(self):
        # 1. Terminal Symbols Definition (Lexer Tokens)
        self.terminals = {
            'int', 'float', 'double', 'char', 'void', 'if', 'else', 'while', 'do', 'for', 'return',
            'id', 'constant', 'literal',
            '(', ')', '{', '}', ';', ',', '=', '++', '--',
            '||', '&&', '==', '!=', '>', '<', '>=', '<=', '+', '-', '*', '/', '%'
        }

        # 2. Non-Terminal Symbols Definition (Syntactic Structures)
        self.non_terminals = {
            'PROGRAM', 'GLOBAL', 'GLOBAL_REST', 'TYPE', 'PARAMS', 'PARAMS_REST',
            'OPT_ASSIGN', 'STMT_LIST', 'STMT', 'OPT_E', 'STMT_ID_REST', 'ARGS', 'ARGS_REST',
            'IF_STMT', 'ELSE_PART', 'ELSE_CHOICE', 'WHILE_STMT', 'DO_WHILE_STMT', 'FOR_STMT',
            'FOR_INIT', 'FOR_UPD', 'FOR_UPD_REST', 'E', 'LOGIC_OR', 'LOGIC_OR_PRIME',
            'LOGIC_AND', 'LOGIC_AND_PRIME', 'EQUALITY', 'EQUALITY_PRIME', 'COMPARISON',
            'COMPARISON_PRIME', 'TERM', 'TERM_PRIME', 'FACTOR', 'FACTOR_PRIME', 'UNARY', 'PRIMARY'
        }

        self.start_symbol = 'PROGRAM'

        # 3. Grammar Production Rules Dictionary (Backus-Naur Form)
        self.productions = {
            # --- Global Program Structure ---
            'PROGRAM': [['GLOBAL', 'PROGRAM'], ['epsilon']],
            'GLOBAL': [['TYPE', 'id', 'GLOBAL_REST']],
            'TYPE': [['int'], ['float'], ['double'], ['char'], ['void']],
            'GLOBAL_REST': [['(', 'PARAMS', ')', '{', 'STMT_LIST', '}'], ['OPT_ASSIGN', ';']],
            
            # --- Function Parameters ---
            'PARAMS': [['TYPE', 'id', 'PARAMS_REST'], ['epsilon']],
            'PARAMS_REST': [[',', 'TYPE', 'id', 'PARAMS_REST'], ['epsilon']],
            'OPT_ASSIGN': [['=', 'E'], ['epsilon']],
            
            # --- Statements and Blocks ---
            'STMT_LIST': [['STMT', 'STMT_LIST'], ['epsilon']],
            'STMT': [
                ['IF_STMT'],
                ['WHILE_STMT'],
                ['DO_WHILE_STMT'],
                ['FOR_STMT'],
                ['return', 'OPT_E', ';'],
                ['TYPE', 'id', 'OPT_ASSIGN', ';'],
                ['id', 'STMT_ID_REST']
            ],
            'OPT_E': [['E'], ['epsilon']],
            
            # --- Identifier Resolution ---
            'STMT_ID_REST': [
                ['=', 'E', ';'],
                ['(', 'ARGS', ')', ';'],
                ['++', ';'],
                ['--', ';']
            ],
            'ARGS': [['E', 'ARGS_REST'], ['epsilon']],
            'ARGS_REST': [[',', 'E', 'ARGS_REST'], ['epsilon']],
            
            # --- Control Flow Structures ---
            'IF_STMT': [['if', '(', 'E', ')', '{', 'STMT_LIST', '}', 'ELSE_PART']],
            'ELSE_PART': [['else', 'ELSE_CHOICE'], ['epsilon']],
            'ELSE_CHOICE': [['{', 'STMT_LIST', '}'], ['IF_STMT']],

            # --- Iteration Loops Statements ---
            'WHILE_STMT': [['while', '(', 'E', ')', '{', 'STMT_LIST', '}']],
            'DO_WHILE_STMT': [['do', '{', 'STMT_LIST', '}', 'while', '(', 'E', ')', ';']],
            'FOR_STMT': [['for', '(', 'FOR_INIT', 'E', ';', 'FOR_UPD', ')', '{', 'STMT_LIST', '}']],
            'FOR_INIT': [['TYPE', 'id', '=', 'E', ';'], ['id', '=', 'E', ';'], [';']],
            'FOR_UPD': [['id', 'FOR_UPD_REST'], ['epsilon']],
            'FOR_UPD_REST': [['++'], ['--'], ['=', 'E']],
            
            # --- Expressions ---
            'E': [['LOGIC_OR']],
            'LOGIC_OR': [['LOGIC_AND', 'LOGIC_OR_PRIME']],
            'LOGIC_OR_PRIME': [['||', 'LOGIC_AND', 'LOGIC_OR_PRIME'], ['epsilon']],
            'LOGIC_AND': [['EQUALITY', 'LOGIC_AND_PRIME']],
            'LOGIC_AND_PRIME': [['&&', 'EQUALITY', 'LOGIC_AND_PRIME'], ['epsilon']],
            'EQUALITY': [['COMPARISON', 'EQUALITY_PRIME']],
            'EQUALITY_PRIME': [['==', 'COMPARISON', 'EQUALITY_PRIME'], ['!=', 'COMPARISON', 'EQUALITY_PRIME'], ['epsilon']],
            'COMPARISON': [['TERM', 'COMPARISON_PRIME']],
            'COMPARISON_PRIME': [['>', 'TERM', 'COMPARISON_PRIME'], ['<', 'TERM', 'COMPARISON_PRIME'], ['>=', 'TERM', 'COMPARISON_PRIME'], ['<=', 'TERM', 'COMPARISON_PRIME'], ['epsilon']],
            'TERM': [['FACTOR', 'TERM_PRIME']],
            'TERM_PRIME': [['+', 'FACTOR', 'TERM_PRIME'], ['-', 'FACTOR', 'TERM_PRIME'], ['epsilon']],
            'FACTOR': [['UNARY', 'FACTOR_PRIME']],
            'FACTOR_PRIME': [['*', 'UNARY', 'FACTOR_PRIME'], ['/', 'UNARY', 'FACTOR_PRIME'], ['%', 'UNARY', 'FACTOR_PRIME'], ['epsilon']],
            'UNARY': [['!', 'UNARY'], ['-', 'UNARY'], ['PRIMARY']],
            'PRIMARY': [['id'], ['constant'], ['literal'], ['(', 'E', ')']]
        }

    def get_productions_for(self, non_terminal: str):
        return self.productions.get(non_terminal, [])