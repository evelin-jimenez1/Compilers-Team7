"""
LL(1) Predictive Parsing Table Generator
----------------------------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date: April 28, 2026

Description:
This module automates the construction of the LL(1) Parsing Table M[A, a]. 
It maps Non-Terminal symbols and Lookahead Terminals to their corresponding 
Full Production Rules (Head -> Body).

Functionality:
- Computes the FIRST set for every production's right-hand side.
- Applies LL(1) rules to fill the decision matrix.
- Handles epsilon transitions using FOLLOW sets to resolve empty derivations.
- Provides a GUI visualization using a Spreadsheet-like grid (Treeview).
"""

import tkinter as tk
from tkinter import ttk
from grammar import Grammar
from first_follow import compute_first, compute_follow

class LL1Table:
    """
    Predictive Parsing Table M[A, a] Manager.
    
    Attributes:
        grammar (Grammar): The formal grammar specification.
        first (dict): Precomputed FIRST sets for all non-terminals.
        follow (dict): Precomputed FOLLOW sets for all non-terminals.
        table (dict): The generated parsing matrix.
    """
    
    def __init__(self, grammar, first_sets, follow_sets):
        self.grammar = grammar
        self.first = first_sets
        self.follow = follow_sets
        self.table = {} 
        self._build_table()

    def _get_first_of_sequence(self, sequence):
        """
        Calculates the FIRST set for a string of grammar symbols.
        Used to determine which terminal activates a specific production.
        """
        res = set()
        for symbol in sequence:
            if symbol == 'epsilon':
                res.add('epsilon')
                break
            if symbol not in self.grammar.non_terminals:
                res.add(symbol)
                break
            
            # Add FIRST(symbol) except epsilon
            res.update(self.first[symbol] - {'epsilon'})
            
            # Stop if the current non-terminal cannot derive epsilon
            if 'epsilon' not in self.first[symbol]:
                break
        else:
            # If all symbols in the sequence can derive epsilon
            res.add('epsilon')
        return res

    def _build_table(self):
        """
        Core Algorithm for LL(1) Table Construction.
        For each production A -> Alpha:
          1. Add 'A -> Alpha' to M[A, a] for every 'a' in FIRST(Alpha).
          2. If epsilon is in FIRST(Alpha), add 'A -> Alpha' to M[A, b] 
             for every 'b' in FOLLOW(A).
        """
        for nt in self.grammar.non_terminals:
            self.table[nt] = {}
            productions = self.grammar.get_productions_for(nt)
            
            for prod in productions:
                # Compute FIRST of the right-hand side (Alpha)
                first_alpha = self._get_first_of_sequence(prod)
                
                # Format the full production string for academic visualization
                # Format: NT -> symbol1 symbol2 ...
                full_prod_str = f"{nt} -> {' '.join(prod)}"
                
                # Rule 1: Fill terminals in FIRST
                for terminal in first_alpha:
                    if terminal != 'epsilon':
                        # Note: If a conflict exists, this grammar is not LL(1)
                        self.table[nt][terminal] = full_prod_str
                
                # Rule 2: Handle epsilon derivations using FOLLOW
                if 'epsilon' in first_alpha:
                    for terminal in self.follow[nt]:
                        self.table[nt][terminal] = full_prod_str

    def display_gui(self):
        """
        Initializes a graphical window to display the Parsing Table in a 
        scrollable grid format.
        """
        window = tk.Toplevel()
        window.title("C-Pure LL(1) Parsing Table - Full View")
        window.geometry("1100x600")
        window.configure(bg="#f4f4f9")

        # Define columns: Sorted list of all terminals + End marker ($)
        terminals = sorted(list(self.grammar.terminals))
        if '$' not in terminals: 
            terminals.append('$')
        if 'epsilon' in terminals: 
            terminals.remove('epsilon') # Epsilon is never a lookahead token
        
        columns = ["NT"] + terminals

        # Main frame for the grid and scrollbars
        container = tk.Frame(window, bg="#f4f4f9")
        container.pack(expand=True, fill='both', padx=15, pady=15)

        # Treeview widget for the grid
        tree = ttk.Treeview(container, columns=columns, show='headings', height=25)
        
        # Scrollbars integration
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Layout using Grid
        tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Configure Header style and column width
        for col in columns:
            tree.heading(col, text=col)
            # Standard productions are long, requiring wider cells
            width = 190 if col != "NT" else 160
            tree.column(col, width=width, anchor='center')

        # Populate rows with Non-Terminals and their corresponding production strings
        for nt in sorted(self.table.keys()):
            row_values = [nt]
            for t in terminals:
                # Retrieve the full production string from the internal table
                row_values.append(self.table[nt].get(t, ""))
            tree.insert("", tk.END, values=row_values)

# --- Entry point for verification ---
if __name__ == "__main__":
    # 1. Initialize data
    g = Grammar()
    first_res = compute_first(g.productions, g.non_terminals)
    follow_res = compute_follow(g.productions, g.non_terminals, first_res, g.start_symbol)
    
    # 2. Build the decision matrix
    generator = LL1Table(g, first_res, follow_res)
    
    # 3. GUI Main Loop
    main_root = tk.Tk()
    main_root.withdraw() # Only show the Toplevel parsing table
    generator.display_gui()
    print("Parsing Table generated successfully.")
    main_root.mainloop()