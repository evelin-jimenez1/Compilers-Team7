"""
FIRST and FOLLOW Set Generator
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
This module provides the computational logic to generate FIRST and FOLLOW sets 
from a Grammar object. These sets are essential for validating if a grammar is 
LL(1) and for the subsequent construction of the Predictive Parsing Table.

Responsibilities:
- Implement the iterative fixed-point algorithm for FIRST sets.
- Implement the dependency-based propagation algorithm for FOLLOW sets.
- Handle 'epsilon' (λ) transitions across production chains.
- Provide a visualization tool to audit the mathematical results via GUI.
- Support the Syntax-Directed Translation (SDT) by defining lookahead symbols.

Mathematical Logic:
- FIRST(α): The set of terminals that can appear at the beginning of strings derived from α.
- FOLLOW(A): The set of terminals that can appear immediately to the right of non-terminal A.

Usage:
The module imports 'Grammar' to access the production rules. When executed, it 
calculates both sets for the current C-Pure grammar and displays them in 
formatted tables.
"""

import tkinter as tk
from tkinter import scrolledtext
from grammar import Grammar

def compute_first(productions, non_terminals):
    """
    Computes FIRST sets using an iterative fixed-point algorithm.
    
    The algorithm continues to iterate through all productions, propagating 
    terminals and the epsilon symbol until the sets stabilize (no more changes).

    Parameters
    ----------
    productions : dict
        Dictionary of production rules from the Grammar class.
    non_terminals : set
        Set of all non-terminal symbols in the grammar.

    Returns
    -------
    dict
        A mapping of each non-terminal to its calculated FIRST set.
    """
    first = {nt: set() for nt in non_terminals}

    def get_first_of_sequence(sequence):
        """ 
        Calculates the FIRST set for a specific string of symbols (RHS of a rule).
        Handles the propagation of epsilon through a sequence of non-terminals.
        """
        res = set()
        for symbol in sequence:
            if symbol == 'epsilon':
                res.add('epsilon')
                break
            if symbol not in non_terminals:
                res.add(symbol)
                break
            
            # If symbol is a non-terminal, add its FIRST set (excluding epsilon)
            symbol_first = first[symbol]
            res.update(symbol_first - {'epsilon'})
            
            # If epsilon is not in the symbol's FIRST, the sequence's FIRST is complete
            if 'epsilon' not in symbol_first:
                break
        else:
            # If the loop finishes, the entire sequence can derive epsilon
            res.add('epsilon')
        return res

    changed = True
    while changed:
        changed = False
        for nt, prods in productions.items():
            before_len = len(first[nt])
            for p in prods:
                first[nt].update(get_first_of_sequence(p))
            if len(first[nt]) > before_len:
                changed = True
    return first

def compute_follow(productions, non_terminals, first_sets, start_symbol):
    """
    Computes FOLLOW sets based on FIRST sets and production positions.
    
    Applies the three fundamental rules of FOLLOW set construction:
    1. Initializing the start symbol with the end-of-file marker ($).
    2. Adding FIRST of the remainder of a production to the preceding non-terminal.
    3. Propagating FOLLOW sets from the head of a production to trailing non-terminals.

    Parameters
    ----------
    productions : dict
        Grammar production rules.
    non_terminals : set
        Grammar non-terminals.
    first_sets : dict
        The pre-computed FIRST sets for all symbols.
    start_symbol : str
        The designated entry point of the grammar.

    Returns
    -------
    dict
        A mapping of each non-terminal to its calculated FOLLOW set.
    """
    follow = {nt: set() for nt in non_terminals}
    # Rule 1: End of string marker for the start symbol
    follow[start_symbol].add('$')

    changed = True
    while changed:
        changed = False
        for head, prods in productions.items():
            for p in prods:
                for i, symbol in enumerate(p):
                    if symbol in non_terminals:
                        before_len = len(follow[symbol])
                        
                        # Look at the sequence following the current non-terminal
                        rest = p[i+1:]
                        if rest:
                            # Rule 2: Add FIRST of the remaining sequence
                            first_of_rest = set()
                            for s in rest:
                                if s == 'epsilon': continue
                                if s not in non_terminals:
                                    first_of_rest.add(s)
                                    break
                                first_of_rest.update(first_sets[s] - {'epsilon'})
                                if 'epsilon' not in first_sets[s]:
                                    break
                            else:
                                first_of_rest.add('epsilon')
                            
                            follow[symbol].update(first_of_rest - {'epsilon'})
                            
                            # Rule 3: If rest is nullable, FOLLOW(symbol) includes FOLLOW(head)
                            if 'epsilon' in first_of_rest:
                                follow[symbol].update(follow[head])
                        else:
                            # Rule 3: Nothing follows the symbol in this production
                            follow[symbol].update(follow[head])
                        
                        if len(follow[symbol]) > before_len:
                            changed = True
    return follow

def display_table_window(title, data_dict, set_name):
    """
    Renders a formatted table within a Tkinter Toplevel window.

    Parameters
    ----------
    title : str
        Window title and header.
    data_dict : dict
        The set data to be displayed.
    set_name : str
        Label for the results column (e.g., 'FIRST(α)').
    """
    window = tk.Toplevel()
    window.title(title)
    window.geometry("550x650")
    window.configure(bg="#f8f9fa")

    header_label = tk.Label(window, text=title, font=("Helvetica", 14, "bold"), 
                            bg="#f8f9fa", fg="#2c3e50")
    header_label.pack(pady=15)

    text_area = scrolledtext.ScrolledText(window, width=65, height=30, 
                                          font=("Consolas", 10), 
                                          bg="white", fg="#333")
    text_area.pack(padx=20, pady=10)

    # Column formatting for clear visual alignment
    output = f"{'NON-TERMINAL':<25} | {set_name}\n"
    output += "=" * 60 + "\n"

    for nt in sorted(data_dict.keys()):
        elements = ", ".join(sorted(list(data_dict[nt])))
        output += f"{nt:<25} | {{ {elements} }}\n\n"

    text_area.insert(tk.INSERT, output)
    text_area.configure(state='disabled') 

if __name__ == "__main__":
    # 1. Initialize Grammar
    g = Grammar()
    
    # 2. Perform Mathematical Computation
    first_results = compute_first(g.productions, g.non_terminals)
    follow_results = compute_follow(g.productions, g.non_terminals, first_results, g.start_symbol)

    # 3. GUI Visualization
    root = tk.Tk()
    root.withdraw() # Hide the empty root window

    display_table_window("Calculated FIRST Sets", first_results, "FIRST(α)")
    display_table_window("Calculated FOLLOW Sets", follow_results, "FOLLOW(α)")

    print("Status: Computation complete. GUI windows active.")
    root.mainloop()