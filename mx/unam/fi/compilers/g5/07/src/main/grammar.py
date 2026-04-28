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

Date: April 28, 2026

Description:
This module defines the context-free grammar (CFG) for the C language.
The grammar is structured in Backus-Naur Form (BNF) and has been factorized
to eliminate left recursion, making it compatible with LL(1) parsing.

Usage:
Run this script directly to visualize the grammar in a GUI window.
"""

import tkinter as tk
from tkinter import scrolledtext

class Grammar:
    """
    Encapsulates the formal definition of the C language.
    
    Attributes:
        terminals (set): The set of atomic symbols (tokens) recognized by the Lexer.
        non_terminals (set): Variables used in productions to represent syntactic structures.
        start_symbol (str): The entry point of the grammar.
        productions (dict): A mapping of non-terminal symbols to their derivation rules.
    """

    def __init__(self):
        # 1. Terminals (Tokens)
        # These represent the base alphabet of the language.
        self.terminals = {
            'id', 'constant', 'literal', 'int', 'float', 'double', 'char', 'void',
            'if', 'else', 'return', '=', ';', ',', '(', ')', '{', '}',
            '+', '-', '*', '/', '%', '==', '!=', '>', '>=', '<', '<=', '&&', '||', '!'
        }

        # 2. Non-Terminals
        # Syntactic variables used to construct the language hierarchy.
        self.non_terminals = {
            'PROGRAM', 'GLOBAL_LIST', 'GLOBAL', 'TYPE', 'GLOBAL_REST',
            'STMT_LIST', 'STMT', 'STMT_ID_REST', 'IF_STMT', 'ELSE_PART',
            'OPT_E', 'OPT_ASSIGN_LOCAL', 'ARG_LIST_OPT', 'ARG_LIST', 'ARG_LIST_PRIME',
            'E', 'LOGIC_OR', 'LOGIC_OR_PRIME', 'LOGIC_AND', 'LOGIC_AND_PRIME',
            'EQUALITY', 'EQUALITY_PRIME', 'COMPARISON', 'COMPARISON_PRIME',
            'TERM', 'TERM_PRIME', 'FACTOR', 'FACTOR_PRIME', 'UNARY', 
            'PRIMARY', 'PRIMARY_ID_REST'
        }

        self.start_symbol = 'PROGRAM'

        # 3. Production Rules
        # Represented as a Dictionary: Non-Terminal -> List of Lists (OR options)
        # Note: 'epsilon' represents the empty string for LL(1) compliance.
        self.productions = {
            'PROGRAM': [['GLOBAL_LIST']],
            'GLOBAL_LIST': [['GLOBAL', 'GLOBAL_LIST'], ['epsilon']],
            'GLOBAL': [['TYPE', 'id', 'GLOBAL_REST']],
            'TYPE': [['int'], ['float'], ['double'], ['char'], ['void']],
            'GLOBAL_REST': [['(', ')', '{', 'STMT_LIST', '}'], ['OPT_ASSIGN', ';']],
            'STMT_LIST': [['STMT', 'STMT_LIST'], ['epsilon']],
            'STMT': [['IF_STMT'], ['return', 'OPT_E', ';'], ['TYPE', 'id', 'OPT_ASSIGN_LOCAL', ';'], ['id', 'STMT_ID_REST']],
            'STMT_ID_REST': [['=', 'E', ';'], ['(', 'ARG_LIST_OPT', ')', ';']],
            'IF_STMT': [['if', '(', 'E', ')', '{', 'STMT_LIST', '}', 'ELSE_PART']],
            'ELSE_PART': [['else', '{', 'STMT_LIST', '}'], ['epsilon']],
            'ARG_LIST_OPT': [['ARG_LIST'], ['epsilon']],
            'ARG_LIST': [['E', 'ARG_LIST_PRIME']],
            'ARG_LIST_PRIME': [[',', 'E', 'ARG_LIST_PRIME'], ['epsilon']],
            'E': [['LOGIC_OR']],
            'LOGIC_OR': [['LOGIC_AND', 'LOGIC_OR_PRIME']],
            'LOGIC_OR_PRIME': [['||', 'LOGIC_AND', 'LOGIC_OR_PRIME'], ['epsilon']],
            'LOGIC_AND': [['EQUALITY', 'LOGIC_AND_PRIME']],
            'LOGIC_AND_PRIME': [['&&', 'EQUALITY', 'LOGIC_AND_PRIME'], ['epsilon']],
            'EQUALITY': [['COMPARISON', 'EQUALITY_PRIME']],
            'EQUALITY_PRIME': [['==', 'COMPARISON', 'EQUALITY_PRIME'], ['!=', 'COMPARISON', 'EQUALITY_PRIME'], ['epsilon']],
            'COMPARISON': [['TERM', 'COMPARISON_PRIME']],
            'COMPARISON_PRIME': [['op_rel', 'TERM', 'COMPARISON_PRIME'], ['epsilon']],
            'TERM': [['FACTOR', 'TERM_PRIME']],
            'TERM_PRIME': [['+', 'FACTOR', 'TERM_PRIME'], ['-', 'FACTOR', 'TERM_PRIME'], ['epsilon']],
            'FACTOR': [['UNARY', 'FACTOR_PRIME']],
            'FACTOR_PRIME': [['*', 'UNARY', 'FACTOR_PRIME'], ['/', 'UNARY', 'FACTOR_PRIME'], ['%', 'UNARY', 'FACTOR_PRIME'], ['epsilon']],
            'UNARY': [['!', 'UNARY'], ['-', 'UNARY'], ['PRIMARY']],
            'PRIMARY': [['id', 'PRIMARY_ID_REST'], ['constant'], ['literal'], ['(', 'E', ')']],
            'PRIMARY_ID_REST': [['(', 'ARG_LIST_OPT', ')'], ['epsilon']]
        }
    def get_productions_for(self, non_terminal):
        """ Returns the list of productions for a given non-terminal """
        return self.productions.get(non_terminal, [])
    
    def display_in_window(self):
        """ 
        Initializes a Tkinter graphical interface to render the grammar rules.
        Format used: <NON_TERMINAL> ::= rule1 | rule2 ... | ruleN
        """
        root = tk.Tk()
        root.title("C-Pure Grammar Specification - Team 7")
        root.geometry("600x700")
        root.configure(bg="#f0f0f0")

        # Header Label
        label = tk.Label(root, text="Formal Grammar (BNF Notation)", 
                         font=("Helvetica", 14, "bold"), bg="#f0f0f0", fg="#333")
        label.pack(pady=10)

        # Scrolled Text Widget for grammar rules
        text_area = scrolledtext.ScrolledText(root, width=70, height=35, 
                                              font=("Courier New", 10), 
                                              bg="white", fg="black")
        text_area.pack(padx=20, pady=10)

        # Formatting rules for display
        grammar_text = f"Start Symbol: {self.start_symbol}\n"
        grammar_text += "="*45 + "\n\n"

        for nt, prods in self.productions.items():
            # Join production lists with a pipe '|' for standard BNF visualization
            formatted_prods = " | ".join([" ".join(p) for p in prods])
            grammar_text += f"<{nt}> ::= {formatted_prods}\n\n"

        # Insertion and state management
        text_area.insert(tk.INSERT, grammar_text)
        text_area.configure(state='disabled') # Read-only mode

        root.mainloop()

# Entry point for stand-alone visualization
if __name__ == "__main__":
    g = Grammar()
    g.display_in_window()