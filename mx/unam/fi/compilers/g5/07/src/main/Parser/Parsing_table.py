"""
LL(1) Predictive Parsing Table Generator - Headless Edition
----------------------------------------------------------
Authors: Team 7
Date: April 28, 2026

Description:
This module automates the construction of the LL(1) Parsing Table M[A, a]. 
"""

from grammar import Grammar
from first_follow import compute_first, compute_follow, get_first_of_sequence

class LL1Table:
    def __init__(self, grammar, first_sets, follow_sets):
        self.grammar = grammar
        self.first = first_sets
        self.follow = follow_sets
        self.table = {nt: {} for nt in self.grammar.non_terminals}
        self.conflicts = []  
        self._build_table()

    def _insert(self, nt, terminal, production):
        """ Inserts a rule in M[NT, terminal] and records conflicts. """
        if terminal not in self.table[nt]:
            self.table[nt][terminal] = []
        
        if production not in self.table[nt][terminal]:
            if len(self.table[nt][terminal]) > 0:
                conflict_msg = f"Conflict at M[{nt}, {terminal}]: {self.table[nt][terminal]} vs {production}"
                self.conflicts.append(conflict_msg)
            self.table[nt][terminal].append(production)

    def _build_table(self):
        """ Core matrix compiler algorithm using FIRST and FOLLOW sets. """
        for nt in self.grammar.non_terminals:
            for prod in self.grammar.get_productions_for(nt):
                # Usamos la función optimizada de first_follow.py
                first_alpha = get_first_of_sequence(prod, self.first, self.grammar.non_terminals)
                full_prod_str = f"{nt} -> {' '.join(prod)}"

                for terminal in first_alpha:
                    if terminal != 'epsilon':
                        self._insert(nt, terminal, full_prod_str)

                if 'epsilon' in first_alpha:
                    for terminal in self.follow[nt]:
                        self._insert(nt, terminal, full_prod_str)

    def print_table(self):
        """ Prints the parsing table to the console. """
        print("\n[System] Parsing table matrix successfully generated:")
        for nt in sorted(self.table.keys()):
            print(f"{nt}: {self.table[nt]}")
        if self.conflicts:
            print("\nGrammar analysis: Conflicts detected.")
        else:
            print("\nGrammar verification successful: Deterministic LL(1) table compiled.")

if __name__ == "__main__":
    g = Grammar()
    first_res = compute_first(g.productions, g.non_terminals)
    follow_res = compute_follow(g.productions, g.non_terminals, first_res, g.start_symbol)
    table_gen = LL1Table(g, first_res, follow_res)
    table_gen.print_table()