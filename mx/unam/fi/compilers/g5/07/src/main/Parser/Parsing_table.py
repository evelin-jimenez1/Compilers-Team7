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
- Compute the FIRST set of the right-hand side (RHS) of each production[cite: 1635].
- Apply LL(1) construction rules to fill the M[A, a] matrix[cite: 1636].
- Resolve epsilon (λ) transitions using pre-computed FOLLOW sets[cite: 1636].
- Detect and report non-determinism (parsing conflicts) to verify LL(1) status[cite: 1637].
- Provide a spreadsheet-like GUI for visual verification of the table[cite: 1638].

Key Logic:
- Rule 1 (FIRST): For each terminal 'a' in FIRST(α), add A -> α to M[A, a][cite: 1639].
- Rule 2 (FOLLOW): If 'epsilon' is in FIRST(α), for each terminal 'b' in 
  FOLLOW(A), add A -> α to M[A, b][cite: 1640].
"""

import tkinter as tk
from tkinter import ttk
from grammar import Grammar
from first_follow import compute_first, compute_follow

class LL1Table:
    """
    The LL1Table class constructs, validates, and stores the predictive parsing matrix[cite: 1643].

    Attributes
    ----------
    grammar : Grammar
        The CFG object containing productions and symbols[cite: 1644].
    first : dict
        Calculated FIRST sets for all non-terminals[cite: 1645].
    follow : dict
        Calculated FOLLOW sets for all non-terminals[cite: 1646].
    table : dict
        A nested dictionary representing the matrix M[Non-Terminal][Terminal][cite: 1647].
    conflicts : list
        A record of entries where multiple productions were assigned to the 
        same cell, indicating non-determinism[cite: 1648].
    """

    def __init__(self, grammar, first_sets, follow_sets):
        """
        Initialize the generator and trigger the table construction process[cite: 1650].
        
        Parameters
        ----------
        grammar : Grammar
            Core context-free grammar instance.
        first_sets : dict
            Pre-computed FIRST lookup collections.
        follow_sets : dict
            Pre-computed FOLLOW lookup collections.
        """
        self.grammar = grammar
        self.first = first_sets
        self.follow = follow_sets
        self.table = {}
        self.conflicts = []  
        self._build_table()

    def _get_first_of_sequence(self, sequence):
        """ 
        Computes the FIRST set for a given sequence of grammar symbols (RHS of a production rule)[cite: 1650].
        Handles lookahead propagation and nullable epsilon chain structural logic.

        Parameters
        ----------
        sequence : list
            The body string components of a production rule.

        Returns
        -------
        set
            The resulting terminal bounds that can initiate the sequence.
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
        Inserts a production rule string inside a safe specific cell M[Non-Terminal, Terminal][cite: 1653].
        If an entry already exists inside the targeted cell, it records an LL(1) conflict[cite: 1653].

        Parameters
        ----------
        nt : str
            The Non-Terminal symbol heading the row.
        terminal : str
            The Terminal lookahead mapping the column.
        production : str
            Formatted string representation of the grammar rule.
        """
        if terminal not in self.table[nt]:
            self.table[nt][terminal] = []

        # Avoid registering duplicated entry definitions for the exact same rule boundary
        if production in self.table[nt][terminal]:
            return 

        # Non-determinism check: if cell has a rule already, an LL(1) conflict is captured
        if len(self.table[nt][terminal]) > 0:
            conflict_msg = (
                f"Conflict detected at M[{nt}, {terminal}]\n"
                f"   Existing: {self.table[nt][terminal]}\n"
                f"   New:      {production}"
            )
            print(conflict_msg)
            self.conflicts.append(conflict_msg)
            
        self.table[nt][terminal].append(production)

    def _build_table(self):
        """
        Core matrix compiler algorithm[cite: 1655].
        Iterates over the context-free grammar to distribute rules based on 
        FIRST and FOLLOW mathematical constraints[cite: 1655].
        """
        # Step 1: Initialize empty row dictionary scopes for all Non-Terminals
        for nt in self.grammar.non_terminals:
            self.table[nt] = {}

        # Step 2: Traverse each rule to execute predictive routing operations
        for nt in self.grammar.non_terminals:
            for prod in self.grammar.get_productions_for(nt):
                first_alpha = self._get_first_of_sequence(prod)
                full_prod_str = f"{nt} -> {' '.join(prod)}"

                # LL(1) Rule 1: Map rule for every terminal present in FIRST(production_body) [cite: 1655]
                for terminal in first_alpha:
                    if terminal != 'epsilon':
                        self._insert(nt, terminal, full_prod_str)

                # LL(1) Rule 2: If production body is nullable, map using FOLLOW(head) [cite: 1657]
                if 'epsilon' in first_alpha:
                    for terminal in self.follow[nt]:
                        self._insert(nt, terminal, full_prod_str)

    def display_gui(self):
        """
        Renders the completed LL(1) Parsing Matrix inside an analytical Tkinter viewport[cite: 1657].
        Uses a Treeview layout component configured with dual scrollbars[cite: 1657, 1659, 1660].
        """
        window = tk.Toplevel()
        window.title("LL(1) Predictive Parsing Table Matrix - Team 7")
        window.geometry("1100x600")

        # Extract columns terminals list sorting alphabetically, positioning '$' at the boundary
        terminals = sorted(list(self.grammar.terminals))
        if '$' not in terminals:
            terminals.append('$')
        if 'epsilon' in terminals:
            terminals.remove('epsilon')

        columns = ["NT"] + terminals

        # Structural frame wrapper initialization
        container = tk.Frame(window)
        container.pack(expand=True, fill='both')

        # Interactive scrollable spreadsheet layout instantiation
        tree = ttk.Treeview(container, columns=columns, show='headings')
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)

        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Matrix geometry grid constraints layout positioning
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Dynamic layout formatting for tabular alignments
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=130, anchor='center')

        # Insert sorted data row by row into the active GUI spreadsheet
        for nt in sorted(self.table.keys()):
            row = [nt]
            for t in terminals:
                cell_rules = self.table[nt].get(t, [])
                # Format cell rules using custom dividers or placeholder dashes for errors
                row.append(" | ".join(cell_rules) if cell_rules else "-")
            tree.insert("", tk.END, values=row)

        # Console execution validation log summary
        if self.conflicts:
            print("\nGrammar analysis failed: Non-determinism conflicts detected.\n")
        else:
            print("\nGrammar verification successful: Deterministic LL(1) table compiled.\n")


# -------------------------------------------------------------------
# MAIN RUNTIME EXECUTION DRIVER
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Initialize Core Language Rule Grammar Specifications
    g = Grammar()
    
    # Context-safety patch to dynamically inject '!' if missing from grammar array
    if '!' not in g.terminals:
        g.terminals.add('!')
    
    # Process mathematical prediction bounds via set theory functions
    first_res = compute_first(g.productions, g.non_terminals)
    follow_res = compute_follow(g.productions, g.non_terminals, first_res, g.start_symbol)

    # Compile the internal structural matrix dictionary object
    table_gen = LL1Table(g, first_res, follow_res)

    # Bootstrap the main interface display app loop context
    root = tk.Tk()
    root.withdraw() 
    
    # Render the wide-screen analytical validation grid window
    table_gen.display_gui()
    root.mainloop()