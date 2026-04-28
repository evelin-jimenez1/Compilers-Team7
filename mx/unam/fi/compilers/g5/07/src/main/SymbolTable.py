"""
Symbol Table Manager
--------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date: April 28, 2026

Description:
This module manages the Symbol Table for the C-Pure compiler. It tracks 
identifiers (variables and functions), their data types, initialization 
status, and scope levels. 

Functionality:
- Scope Stack: Supports nested scopes for local and global variables.
- Type Tracking: Stores data types (int, float, char, etc.) for semantic validation.
- Initialization Check: Tracks whether a variable has been assigned a value.
- Error Detection: Identifies redeclarations or usage of undeclared variables.
"""

class Symbol:
    """ Represents a single entry in the Symbol Table. """
    def __init__(self, name, symbol_type, line, is_function=False):
        self.name = name
        self.type = symbol_type
        self.line = line
        self.is_function = is_function
        self.initialized = False
        self.params = []  # Used if it's a function

    def __repr__(self):
        cat = "FUNC" if self.is_function else "VAR"
        return f"[{cat}] {self.name} ({self.type}) - Init: {self.initialized}"

class SymbolTable:
    """
    Manages a stack of scopes to handle variable visibility and lifetimes.
    """
    def __init__(self):
        # A list of dictionaries, where each dict represents a scope level.
        # Index 0 is always the Global Scope.
        self.scopes = [{}]
        self.errors = []

    def enter_scope(self):
        """ Pushes a new local scope onto the stack. """
        self.scopes.append({})

    def exit_scope(self):
        """ Pops the current local scope. """
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, symbol_type, line, is_func=False):
        """
        Adds a new symbol to the current (topmost) scope.
        Returns False if the symbol was already declared in this scope.
        """
        current_scope = self.scopes[-1]
        
        if name in current_scope:
            self.errors.append(f"[Line {line}] Semantic Error: '{name}' is already defined in this scope.")
            return False
        
        if symbol_type == "void" and not is_func:
            self.errors.append(f"[Line {line}] Semantic Error: Variable '{name}' cannot be of type 'void'.")
            return False

        new_symbol = Symbol(name, symbol_type, line, is_func)
        current_scope[name] = new_symbol
        return True

    def lookup(self, name):
        """
        Searches for a symbol starting from the current scope up to the global scope.
        Returns the Symbol object if found, None otherwise.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def mark_as_initialized(self, name):
        """ Marks a variable as having an assigned value. """
        symbol = self.lookup(name)
        if symbol:
            symbol.initialized = True

    def get_all_symbols(self):
        """ Returns a flattened view of all symbols currently reachable. """
        flat_table = {}
        for scope in self.scopes:
            flat_table.update(scope)
        return flat_table

    def print_table(self):
        """ Utility to print the current state of the table to the console. """
        print("\n--- Current Symbol Table State ---")
        for i, scope in enumerate(self.scopes):
            scope_name = "Global" if i == 0 else f"Local Level {i}"
            print(f"{scope_name}: {scope}")

# --- Test Script ---
if __name__ == "__main__":
    st = SymbolTable()
    
    print("Test 1: Global Declaration")
    st.declare("global_x", "int", 1)
    
    print("Test 2: Entering Local Scope")
    st.enter_scope()
    st.declare("local_y", "float", 5)
    
    print("Lookup 'global_x' from local scope:", st.lookup("global_x"))
    print("Lookup 'local_y' from local scope:", st.lookup("local_y"))
    
    print("\nTest 3: Exiting Local Scope")
    st.exit_scope()
    print("Lookup 'local_y' (should be None):", st.lookup("local_y"))
    
    st.print_table()