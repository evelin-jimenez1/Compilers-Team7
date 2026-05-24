""""
C Grammar Specification
-----------------------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date:
    April 28, 2026

Program description:
The Grammar class defines the formal structure of a subset of the C language. 
It specifically implements a Context-Free Grammar (CFG) designed to be 
compatible with LL(1) predictive parsing.

Responsibilities:
- Define the set of terminal symbols (tokens) recognized by the language.
- Define the set of non-terminal symbols representing syntactic structures.
- Specify the production rules in Backus-Naur Form (BNF).
- Eliminate left recursion and apply left factoring to support top-down parsing.
- Provide a graphical interface (GUI) to visualize the production rules.
- Serve as the foundational data source for the Syntax-Directed Translation (SDT).

Grammar Features:
- Recursive descent and LL(1) parsing table compatible.
- Handle global declarations (functions and variables with parameter support).
- Expression hierarchy: logic, equality, comparison, and arithmetic operations.
- Control structures: support for 'if-else' blocks (including flat else-if chains).
- Iteration statements: while, do-while, and for loops with basic increment/decrement.
"""

import tkinter as tk
from tkinter import scrolledtext

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
        # 'ELSE_CHOICE' resolves the predictive cascade of flat else-if statements without conflicts.
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
            'PROGRAM': [
                ['GLOBAL', 'PROGRAM'],
                ['epsilon']
            ],
            'GLOBAL': [
                ['TYPE', 'id', 'GLOBAL_REST']
            ],
            'TYPE': [
                ['int'], ['float'], ['double'], ['char'], ['void']
            ],
            'GLOBAL_REST': [
                ['(', 'PARAMS', ')', '{', 'STMT_LIST', '}'],
                ['OPT_ASSIGN', ';']
            ],
            
            # --- Function Parameters (Right Recursion for LL(1)) ---
            'PARAMS': [
                ['TYPE', 'id', 'PARAMS_REST'],
                ['epsilon']
            ],
            'PARAMS_REST': [
                [',', 'TYPE', 'id', 'PARAMS_REST'],
                ['epsilon']
            ],
            'OPT_ASSIGN': [
                ['=', 'E'],
                ['epsilon']
            ],
            
            # --- Statements and Blocks ---
            'STMT_LIST': [
                ['STMT', 'STMT_LIST'],
                ['epsilon']
            ],
            'STMT': [
                ['IF_STMT'],
                ['WHILE_STMT'],
                ['DO_WHILE_STMT'],
                ['FOR_STMT'],
                ['return', 'OPT_E', ';'],
                ['TYPE', 'id', 'OPT_ASSIGN', ';'],
                ['id', 'STMT_ID_REST']
            ],
            'OPT_E': [
                ['E'],
                ['epsilon']
            ],
            
            # --- Identifier Resolution (Assignments, Calls, Postfix Operations) ---
            'STMT_ID_REST': [
                ['=', 'E', ';'],
                ['(', 'ARGS', ')', ';'],
                ['++', ';'],
                ['--', ';']
            ],
            'ARGS': [
                ['E', 'ARGS_REST'],
                ['epsilon']
            ],
            'ARGS_REST': [
                [',', 'E', 'ARGS_REST'],
                ['epsilon']
            ],
            
            # --- Control Flow Structures (With Flat Else-If Factorization) ---
            'IF_STMT': [
                ['if', '(', 'E', ')', '{', 'STMT_LIST', '}', 'ELSE_PART']
            ],
            'ELSE_PART': [
                ['else', 'ELSE_CHOICE'],
                ['epsilon']
            ],
            'ELSE_CHOICE': [
                ['{', 'STMT_LIST', '}'],
                ['IF_STMT'] # LL(1) Factorization trick: safe direct recursion to handle nested chains flats
            ],

            # --- Iteration Loops Statements ---
            'WHILE_STMT': [
                ['while', '(', 'E', ')', '{', 'STMT_LIST', '}']
            ],
            'DO_WHILE_STMT': [
                ['do', '{', 'STMT_LIST', '}', 'while', '(', 'E', ')', ';']
            ],
            'FOR_STMT': [
                ['for', '(', 'FOR_INIT', 'E', ';', 'FOR_UPD', ')', '{', 'STMT_LIST', '}']
            ],
            'FOR_INIT': [
                ['TYPE', 'id', '=', 'E', ';'],
                ['id', '=', 'E', ';'],
                [';']
            ],
            'FOR_UPD': [
                ['id', 'FOR_UPD_REST'],
                ['epsilon']
            ],
            'FOR_UPD_REST': [
                ['++'],
                ['--'],
                ['=', 'E']
            ],
            
            # --- Expressions Operator Precedence Cascades ---
            'E': [
                ['LOGIC_OR']
            ],
            'LOGIC_OR': [
                ['LOGIC_AND', 'LOGIC_OR_PRIME']
            ],
            'LOGIC_OR_PRIME': [
                ['||', 'LOGIC_AND', 'LOGIC_OR_PRIME'],
                ['epsilon']
            ],
            'LOGIC_AND': [
                ['EQUALITY', 'LOGIC_AND_PRIME']
            ],
            'LOGIC_AND_PRIME': [
                ['&&', 'EQUALITY', 'LOGIC_AND_PRIME'],
                ['epsilon']
            ],
            'EQUALITY': [
                ['COMPARISON', 'EQUALITY_PRIME']
            ],
            'EQUALITY_PRIME': [
                ['==', 'COMPARISON', 'EQUALITY_PRIME'],
                ['!=', 'COMPARISON', 'EQUALITY_PRIME'],
                ['epsilon']
            ],
            'COMPARISON': [
                ['TERM', 'COMPARISON_PRIME']
            ],
            'COMPARISON_PRIME': [
                ['>', 'TERM', 'COMPARISON_PRIME'],
                ['<', 'TERM', 'COMPARISON_PRIME'],
                ['>=', 'TERM', 'COMPARISON_PRIME'],
                ['<=', 'TERM', 'COMPARISON_PRIME'],
                ['epsilon']
            ],
            'TERM': [
                ['FACTOR', 'TERM_PRIME']
            ],
            'TERM_PRIME': [
                ['+', 'FACTOR', 'TERM_PRIME'],
                ['-', 'FACTOR', 'TERM_PRIME'],
                ['epsilon']
            ],
            'FACTOR': [
                ['UNARY', 'FACTOR_PRIME']
            ],
            'FACTOR_PRIME': [
                ['*', 'UNARY', 'FACTOR_PRIME'],
                ['/', 'UNARY', 'FACTOR_PRIME'],
                ['%', 'UNARY', 'FACTOR_PRIME'],
                ['epsilon']
            ],
            'UNARY': [
                ['!', 'UNARY'],
                ['-', 'UNARY'],
                ['PRIMARY']
            ],
            'PRIMARY': [
                ['id'],
                ['constant'],
                ['literal'],
                ['(', 'E', ')']
            ]
        }

    def get_productions_for(self, non_terminal: str):
        """
        Returns the list of production rules associated with a specific non-terminal symbol.
        """
        return self.productions.get(non_terminal, [])

    def display_in_window(self):
        """
        Launches a Tkinter-based GUI window to visualize the formal grammar rules in BNF format.
        """
        root = tk.Tk()
        root.title("C-Pure Grammar Specification - Team 7")
        root.geometry("650x750")

        label = tk.Label(root, text="Formal Context-Free Grammar (BNF)",
                         font=("Arial", 14, "bold"))
        label.pack(pady=10)

        text_area = scrolledtext.ScrolledText(
            root,
            width=80,
            height=40,
            font=("Courier New", 10)
        )
        text_area.pack(padx=10, pady=10)

        grammar_text = f"Start Symbol: {self.start_symbol}\n"
        grammar_text += "=" * 50 + "\n\n"

        for nt, prods in self.productions.items():
            formatted = " | ".join([" ".join(p) for p in prods])
            grammar_text += f"<{nt}> ::= {formatted}\n\n"

        text_area.insert(tk.INSERT, grammar_text)
        text_area.configure(state='disabled')

        root.mainloop()

if __name__ == '__main__':
    # Standalone execution for visual testing and structural validation
    g = Grammar()
    g.display_in_window()