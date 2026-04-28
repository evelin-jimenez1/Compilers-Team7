import tkinter as tk
from tkinter import scrolledtext
from grammar import Grammar

def compute_first(productions, non_terminals):
    """
    Computes the FIRST sets for all non-terminals.
    FIRST(A) is the set of terminals that can begin strings derived from A.
    """
    first = {nt: set() for nt in non_terminals}

    def get_first_of_sequence(sequence):
        res = set()
        for symbol in sequence:
            if symbol == 'epsilon':
                res.add('epsilon')
                break
            if symbol not in non_terminals:
                res.add(symbol)
                break
            
            symbol_first = first[symbol]
            res.update(symbol_first - {'epsilon'})
            if 'epsilon' not in symbol_first:
                break
        else:
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
    Computes the FOLLOW sets for all non-terminals.
    FOLLOW(A) is the set of terminals that can appear immediately to the right of A.
    """
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
                            if 'epsilon' in first_of_rest:
                                follow[symbol].update(follow[head])
                        else:
                            follow[symbol].update(follow[head])
                        
                        if len(follow[symbol]) > before_len:
                            changed = True
    return follow

def display_table_window(title, data_dict, set_name):
    """
    Creates a Tkinter window to display the calculated sets in a formatted table.
    """
    window = tk.Toplevel() # Use Toplevel so it doesn't kill the main process
    window.title(title)
    window.geometry("500x600")

    label = tk.Label(window, text=title, font=("Arial", 12, "bold"))
    label.pack(pady=10)

    text_area = scrolledtext.ScrolledText(window, width=60, height=30, font=("Courier New", 10))
    text_area.pack(padx=20, pady=10)

    # Header
    output = f"{'NON-TERMINAL':<20} | {set_name}\n"
    output += "-" * 55 + "\n"

    # Sorted rows
    for nt in sorted(data_dict.keys()):
        elements = ", ".join(sorted(list(data_dict[nt])))
        output += f"{nt:<20} | {{ {elements} }}\n"

    text_area.insert(tk.INSERT, output)
    text_area.configure(state='disabled')

if __name__ == "__main__":
    # 1. Initialize Grammar
    g = Grammar()
    
    # 2. Compute Sets
    first_table = compute_first(g.productions, g.non_terminals)
    follow_table = compute_follow(g.productions, g.non_terminals, first_table, g.start_symbol)

    # 3. GUI Display
    root = tk.Tk()
    root.withdraw() # Hide the tiny main root window

    display_table_window("FIRST Sets", first_table, "FIRST(A)")
    display_table_window("FOLLOW Sets", follow_table, "FOLLOW(A)")

    print("Windows opened. Close them to terminate the script.")
    root.mainloop()