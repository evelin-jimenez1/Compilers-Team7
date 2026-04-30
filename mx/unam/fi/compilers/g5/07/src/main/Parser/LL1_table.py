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

Date:
    April 28, 2026

Program description:
This module automates the construction of the LL(1) Parsing Table M[A, a]. 
It serves as the decision matrix for the predictive parser, mapping 
Non-Terminal symbols and Lookahead Terminals to their corresponding 
production rules.

Responsibilities:
- Compute the FIRST set of the right-hand side (RHS) of each production.
- Apply LL(1) construction rules to fill the M[A, a] matrix.
- Resolve epsilon (λ) transitions using pre-computed FOLLOW sets.
- Detect and report non-determinism (parsing conflicts) to verify LL(1) status.
- Provide a spreadsheet-like GUI for visual verification of the table.

Key Logic:
- Rule 1 (FIRST): For each terminal 'a' in FIRST(α), add A -> α to M[A, a].
- Rule 2 (FOLLOW): If 'epsilon' is in FIRST(α), for each terminal 'b' in 
  FOLLOW(A), add A -> α to M[A, b].

Usage:
The class 'LL1Table' requires a Grammar object and pre-calculated FIRST/FOLLOW 
dictionaries. Executing the script generates the table for the C-Pure grammar 
and prints a validation status to the console.
"""

import tkinter as tk
from tkinter import ttk
from grammar import Grammar
from first_follow import compute_first, compute_follow

class LL1Table:
    """
    The LL1Table class constructs and stores the predictive parsing matrix.

    Attributes
    ----------
    grammar : Grammar
        The CFG object containing productions and symbols.
    first : dict
        Calculated FIRST sets for all non-terminals.
    follow : dict
        Calculated FOLLOW sets for all non-terminals.
    table : dict
        A nested dictionary representing the matrix M[Non-Terminal][Terminal].
    conflicts : list
        A record of entries where multiple productions were assigned to the 
        same cell.
    """

    def __init__(self, grammar, first_sets, follow_sets):
        """
        Initialize the generator and trigger the table construction process.
        """
        self.grammar = grammar
        self.first = first_sets
        self.follow = follow_sets
        self.table = {}
        self.conflicts = []  # List to store detected grammar conflicts
        self._build_table()

    def _get_first_of_sequence(self, sequence):
        """ 
        Internal helper to compute FIRST for a sequence of symbols in a production body.
        """
        res = set()
        for symbol in sequence:
            if symbol == 'epsilon':
                res.add('epsilon')
                break
            if symbol not in self.grammar.non_terminals:
                res.add(symbol)
                break
            res.update(self.first[symbol] - {'epsilon'})
            if 'epsilon' not in self.first[symbol]:
                break
        else:
            res.add('epsilon')
        return res

    def _insert(self, nt, terminal, production):
        """
        Inserts a production into the table cell M[nt, terminal].
        If a production already exists, it records an LL(1) conflict.
        """
        if terminal in self.table[nt]:
            conflict_msg = (
                f"Conflict detected at M[{nt}, {terminal}]\n"
                f"   Existing: {self.table[nt][terminal]}\n"
                f"   New:      {production}"
            )
            print(conflict_msg)
            self.conflicts.append(conflict_msg)
        else:
            self.table[nt][terminal] = production

    def _build_table(self):
        """
        Core algorithm for filling the LL(1) table using FIRST and FOLLOW sets.
        """
        for nt in self.grammar.non_terminals:
            self.table[nt] = {}

            for prod in self.grammar.get_productions_for(nt):
                first_alpha = self._get_first_of_sequence(prod)
                full_prod_str = f"{nt} -> {' '.join(prod)}"

                # Rule 1: Fill table based on terminals in FIRST(production_body)
                for terminal in first_alpha:
                    if terminal != 'epsilon':
                        self._insert(nt, terminal, full_prod_str)

                # Rule 2: If production body is nullable, fill table using FOLLOW(head)
                if 'epsilon' in first_alpha:
                    for terminal in self.follow[nt]:
                        self._insert(nt, terminal, full_prod_str)

    def display_gui(self):
        """
        Renders the parsing table in a Toplevel window using a Treeview (Grid).
        Each row represents a Non-Terminal and each column a Terminal.
        """
        window = tk.Toplevel()
        window.title("LL(1) Parsing Table")
        window.geometry("1100x600")

        # Prepare terminals for columns, including the end-of-file marker '$'
        terminals = sorted(list(self.grammar.terminals))
        if '$' not in terminals:
            terminals.append('$')
        if 'epsilon' in terminals:
            terminals.remove('epsilon')

        columns = ["NT"] + terminals

        # Container for scrollable treeview
        container = tk.Frame(window)
        container.pack(expand=True, fill='both')

        tree = ttk.Treeview(container, columns=columns, show='headings')
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)

        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Table Headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')

        # Insert data rows
        for nt in sorted(self.table.keys()):
            row = [nt]
            for t in terminals:
                row.append(self.table[nt].get(t, ""))
            tree.insert("", tk.END, values=row)

        # Console summary
        if self.conflicts:
            print("\n⚠️ GRAMMAR IS NOT LL(1): Conflicts found in table construction.\n")
        else:
            print("\n✅ Grammar is LL(1): Table successfully constructed.\n")

# -----------------------------------
# MAIN TEST
# -----------------------------------
if __name__ == "__main__":
    # Computation flow
    g = Grammar()
    first_res = compute_first(g.productions, g.non_terminals)
    follow_res = compute_follow(g.productions, g.non_terminals, first_res, g.start_symbol)

    # Table Generation
    table_gen = LL1Table(g, first_res, follow_res)

    root = tk.Tk()
    root.withdraw() # Hide root, show Toplevel
    table_gen.display_gui()
    root.mainloop()