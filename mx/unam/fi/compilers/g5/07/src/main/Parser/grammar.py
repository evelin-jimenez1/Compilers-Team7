"""
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
- Recursive descent compatible.
- Handle global declarations (functions and variables).
- Expression hierarchy: logic, equality, comparison, and arithmetic operations.
- Control structures: support for 'if-else' blocks.
- Function calls and assignment handling via 'STMT_ID_REST'.

Usage:
The module can be imported to retrieve production rules or executed as a 
standalone script to open a Tkinter window displaying the full grammar.
"""

import tkinter as tk
from tkinter import scrolledtext

class Grammar:
    """
    The Grammar class stores and organizes the CFG for the C-Pure compiler.

    Attributes
    ----------
    terminals : set
        Tokens that form the leaves of the parse tree.
    non_terminals : set
        Syntactic categories that can be expanded into other symbols.
    productions : dict
        A mapping of non-terminals to lists of possible production sequences.
    start_symbol : str
        The entry point of the grammar (PROGRAM).
    """

    def __init__(self):
        """
        Initialize the grammar components, defining the vocabulary and 
        the hierarchical rules for the language.
        """
        

        # TERMINALS

        # List of atomic symbols recognized by the Lexer.
        self.terminals = {
            'id', 'constant', 'literal',
            'int', 'float', 'double', 'char', 'void',
            'if', 'else', 'return',
            '=', ';', '(', ')', '{', '}',
            '+', '-', '*', '/', '%',
            '==', '!=', '>', '>=', '<', '<=',
            '&&', '||', '!'
        }


        # NON-TERMINALS

        # Variables used to derive strings in the language.
        self.non_terminals = {
            'PROGRAM', 'GLOBAL', 'TYPE', 'GLOBAL_REST',
            'OPT_ASSIGN', 'OPT_E',
            'STMT_LIST', 'STMT', 'STMT_ID_REST',
            'IF_STMT', 'ELSE_PART',
            'E', 'LOGIC_OR', 'LOGIC_OR_PRIME',
            'LOGIC_AND', 'LOGIC_AND_PRIME',
            'EQUALITY', 'EQUALITY_PRIME',
            'COMPARISON', 'COMPARISON_PRIME',
            'TERM', 'TERM_PRIME',
            'FACTOR', 'FACTOR_PRIME',
            'UNARY', 'PRIMARY'
        }

        self.start_symbol = 'PROGRAM'

        # PRODUCTIONS

        # Dictionary representing the rules. 'epsilon' denotes an empty string derivation.
        self.productions = {
            # Entry point: A program is a sequence of global declarations.
            'PROGRAM': [['GLOBAL', 'PROGRAM'], ['epsilon']],

            'GLOBAL': [['TYPE', 'id', 'GLOBAL_REST']],

            'TYPE': [['int'], ['float'], ['double'], ['char'], ['void']],

            # Left factoring applied to distinguish between functions and variable declarations.
            'GLOBAL_REST': [
                ['(', ')', '{', 'STMT_LIST', '}'],
                ['OPT_ASSIGN', ';']
            ],

            'OPT_ASSIGN': [['=', 'E'], ['epsilon']],

            # Statements and flow control
            'STMT_LIST': [['STMT', 'STMT_LIST'], ['epsilon']],

            'STMT': [
                ['IF_STMT'],
                ['return', 'OPT_E', ';'],
                ['TYPE', 'id', 'OPT_ASSIGN', ';'],
                ['id', 'STMT_ID_REST']
            ],

            'OPT_E': [['E'], ['epsilon']],

            'STMT_ID_REST': [
                ['=', 'E', ';'],
                ['(', ')', ';']
            ],

            'IF_STMT': [['if', '(', 'E', ')', '{', 'STMT_LIST', '}', 'ELSE_PART']],

            'ELSE_PART': [['else', '{', 'STMT_LIST', '}'], ['epsilon']],

            # Expression hierarchy (Factorized to eliminate left recursion)
            'E': [['LOGIC_OR']],

            'LOGIC_OR': [['LOGIC_AND', 'LOGIC_OR_PRIME']],
            'LOGIC_OR_PRIME': [['||', 'LOGIC_AND', 'LOGIC_OR_PRIME'], ['epsilon']],

            'LOGIC_AND': [['EQUALITY', 'LOGIC_AND_PRIME']],
            'LOGIC_AND_PRIME': [['&&', 'EQUALITY', 'LOGIC_AND_PRIME'], ['epsilon']],

            'EQUALITY': [['COMPARISON', 'EQUALITY_PRIME']],
            'EQUALITY_PRIME': [
                ['==', 'COMPARISON', 'EQUALITY_PRIME'],
                ['!=', 'COMPARISON', 'EQUALITY_PRIME'],
                ['epsilon']
            ],

            'COMPARISON': [['TERM', 'COMPARISON_PRIME']],
            'COMPARISON_PRIME': [
                ['>', 'TERM', 'COMPARISON_PRIME'],
                ['<', 'TERM', 'COMPARISON_PRIME'],
                ['>=', 'TERM', 'COMPARISON_PRIME'],
                ['<=', 'TERM', 'COMPARISON_PRIME'],
                ['epsilon']
            ],

            'TERM': [['FACTOR', 'TERM_PRIME']],
            'TERM_PRIME': [
                ['+', 'FACTOR', 'TERM_PRIME'],
                ['-', 'FACTOR', 'TERM_PRIME'],
                ['epsilon']
            ],

            'FACTOR': [['UNARY', 'FACTOR_PRIME']],
            'FACTOR_PRIME': [
                ['*', 'UNARY', 'FACTOR_PRIME'],
                ['/', 'UNARY', 'FACTOR_PRIME'],
                ['%', 'UNARY', 'FACTOR_PRIME'],
                ['epsilon']
            ],

            'UNARY': [['!', 'UNARY'], ['-', 'UNARY'], ['PRIMARY']],

            'PRIMARY': [
                ['id'],
                ['constant'],
                ['literal'],
                ['(', 'E', ')']
            ]
        }

    def get_productions_for(self, non_terminal):
        """
        Retrieve the list of productions for a given non-terminal.

        Parameters
        ----------
        non_terminal : str
            The name of the non-terminal to look up.

        Returns
        -------
        list
            The production rules associated with the symbol.
        """
        return self.productions.get(non_terminal, [])

    def display_in_window(self):
        """
        Launch a Tkinter-based GUI to display the grammar in a readable BNF format.
        Useful for debugging and verification of rule factorization.
        """
        root = tk.Tk()
        root.title("C-Pure Grammar (Final)")
        root.geometry("650x750")

        label = tk.Label(root, text="Formal Grammar (BNF)",
                         font=("Arial", 14, "bold"))
        label.pack(pady=10)

        text_area = scrolledtext.ScrolledText(
            root,
            width=80,
            height=40,
            font=("Courier New", 10)
        )
        text_area.pack(padx=10, pady=10)

        # Build the string representation of the grammar
        grammar_text = f"Start Symbol: {self.start_symbol}\n"
        grammar_text += "=" * 50 + "\n\n"

        for nt, prods in self.productions.items():
            formatted = " | ".join([" ".join(p) for p in prods])
            grammar_text += f"<{nt}> ::= {formatted}\n\n"

        text_area.insert(tk.INSERT, grammar_text)
        text_area.configure(state='disabled')

        root.mainloop()

if __name__ == "__main__":
    # Execution entry point for visualization.
    g = Grammar()
    g.display_in_window()