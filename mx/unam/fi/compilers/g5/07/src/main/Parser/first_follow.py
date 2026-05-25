"""
FIRST and FOLLOW Set Generator - Pure Logic Edition
---------------------------------------------------
Authors: Team 7
Date: April 28, 2026

Description:
This module provides the computational logic to generate FIRST and FOLLOW sets.
This version is stripped of all GUI components, ensuring 100% compatibility 
with web environments and server-side execution.
"""
import sys
import os

# Agregamos la carpeta actual al path de Python dinámicamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from grammar import Grammar

def get_first_of_sequence(sequence, first_sets, non_terminals):
    """Helper to compute the FIRST set for any sequence."""
    res = set()
    for symbol in sequence:
        if symbol == 'epsilon':
            res.add('epsilon')
            break
        if symbol not in non_terminals:
            res.add(symbol)
            break
        res.update(first_sets[symbol] - {'epsilon'})
        if 'epsilon' not in first_sets[symbol]:
            break
    else:
        res.add('epsilon')
    return res

def compute_first(productions, non_terminals):
    """Computes FIRST sets using an iterative fixed-point algorithm."""
    first = {nt: set() for nt in non_terminals}

    changed = True
    while changed:
        changed = False
        for nt, prods in productions.items():
            before_len = len(first[nt])
            for p in prods:
                first[nt].update(get_first_of_sequence(p, first, non_terminals))
            if len(first[nt]) > before_len:
                changed = True
    return first

def compute_follow(productions, non_terminals, first_sets, start_symbol):
    """Computes FOLLOW sets based on FIRST sets and production positions."""
    follow = {nt: set() for nt in non_terminals}
    follow[start_symbol].add('$')

    changed = True
    while changed:
        changed = False
        for head, prods in productions.items():
            for p in prods:
                for i, symbol in enumerate(p):
                    if symbol in non_terminals:
                        before_len = len(follow[symbol])
                        rest = p[i+1:]
                        if rest:
                            first_of_rest = get_first_of_sequence(rest, first_sets, non_terminals)
                            follow[symbol].update(first_of_rest - {'epsilon'})
                            if 'epsilon' in first_of_rest:
                                follow[symbol].update(follow[head])
                        else:
                            follow[symbol].update(follow[head])
                        if len(follow[symbol]) > before_len:
                            changed = True
    return follow

if __name__ == "__main__":
    g = Grammar()
    first_res = compute_first(g.productions, g.non_terminals)
    follow_res = compute_follow(g.productions, g.non_terminals, first_res, g.start_symbol)
    
    print("--- FIRST sets calculated ---")
    for nt, s in first_res.items():
        print(f"{nt}: {s}")
    
    print("\n--- FOLLOW sets calculated ---")
    for nt, s in follow_res.items():
        print(f"{nt}: {s}")