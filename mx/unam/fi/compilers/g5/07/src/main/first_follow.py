"""
FIRST and FOLLOW Set Generator
------------------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Hernández Héctor Emilio

Date: April 28, 2026

Description:
This module implements the mathematical algorithms to compute FIRST and FOLLOW sets
for a given context-free grammar. These sets are fundamental for constructing 
the LL(1) parsing table and ensuring non-ambiguous syntax analysis.

Logic:
- FIRST(A): The set of terminals that can begin strings derived from A.
- FOLLOW(A): The set of terminals that can appear immediately to the right of A 
             in some sentential form.
"""

import tkinter as tk
from tkinter import scrolledtext
from grammar import Grammar

def compute_first(productions, non_terminals):
    """
    Computes FIRST sets using an iterative fixed-point algorithm.
    It propagates terminals and epsilon through the production chains 
    until no further changes occur.
    """
    first = {nt: set() for nt in non_terminals}

    def get_first_of_sequence(sequence):
        """ Helper to compute FIRST for a sequence of symbols (rhs of a rule) """
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
            
            # If epsilon is not in the symbol's FIRST, we stop propagation
            if 'epsilon' not in symbol_first:
                break
        else:
            # If the entire loop finishes, it means the entire sequence can derive epsilon
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
    Computes FOLLOW sets using the following rules:
    1. Place $ in FOLLOW(StartSymbol).
    2. If A -> αBβ, then everything in FIRST(β) except epsilon is in FOLLOW(B).
    3. If A -> αB or A -> αBβ where FIRST(β) contains epsilon, 
       then everything in FOLLOW(A) is in FOLLOW(B).
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
                        
                        # Look at the rest of the production after the non-terminal
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
                            
                            # Rule 3: If rest can be empty, propagate FOLLOW(head)
                            if 'epsilon' in first_of_rest:
                                follow[symbol].update(follow[head])
                        else:
                            # Rule 3: Nothing follows B, so FOLLOW(B) contains FOLLOW(head)
                            follow[symbol].update(follow[head])
                        
                        if len(follow[symbol]) > before_len:
                            changed = True
    return follow

def display_table_window(title, data_dict, set_name):
    """
    Renders a formatted table within a Tkinter Toplevel window 
    to visualize the calculated sets.
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

    # Table Formatting
    output = f"{'NON-TERMINAL':<25} | {set_name}\n"
    output += "=" * 60 + "\n"

    for nt in sorted(data_dict.keys()):
        elements = ", ".join(sorted(list(data_dict[nt])))
        output += f"{nt:<25} | {{ {elements} }}\n\n"

    text_area.insert(tk.INSERT, output)
    text_area.configure(state='disabled') # Prevent user editing

if __name__ == "__main__":
    # Standard testing routine
    g = Grammar()
    
    # Mathematical computation
    first_results = compute_first(g.productions, g.non_terminals)
    follow_results = compute_follow(g.productions, g.non_terminals, first_results, g.start_symbol)

    # UI Execution
    root = tk.Tk()
    root.withdraw() # Main window is not needed, only the Toplevels

    display_table_window("Calculated FIRST Sets", first_results, "FIRST(α)")
    display_table_window("Calculated FOLLOW Sets", follow_results, "FOLLOW(α)")

    print("Status: Computation complete. GUI windows active.")
    root.mainloop()