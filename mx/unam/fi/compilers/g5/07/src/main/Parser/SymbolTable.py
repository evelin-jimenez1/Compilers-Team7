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
identifiers, their types, initialization state, and scope levels.

Functionality:
- Scope stack for nested environments
- Type tracking for semantic validation
- Initialization tracking
- Semantic error detection
"""


class Symbol:

    # Represents a single entry in the symbol table
    def __init__(self, name, symbol_type, line, is_function=False):

        self.name = name
        self.type = symbol_type
        self.line = line

        # Flag to distinguish functions from variables
        self.is_func = is_function

        # Tracks whether variable has been initialized
        self.initialized = False

        # Function parameter list (if applicable)
        self.params = []

    # String representation for debugging
    def __repr__(self):
        cat = "FUNC" if self.is_func else "VAR"
        return f"[{cat}] {self.name} ({self.type}) - Init: {self.initialized}"


class SymbolTable:

    # Manages scopes using a stack (global + local scopes)
    def __init__(self):

        # Each scope is a dictionary of symbols
        self.scopes = [{}]

        # Semantic error list
        self.errors = []

    # Enter a new local scope
    def enter_scope(self):
        self.scopes.append({})

    # Exit current scope
    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    # Declare a new symbol in current scope
    def declare(self, name, symbol_type, line, is_func=False):

        current_scope = self.scopes[-1]

        # Check redeclaration in same scope
        if name in current_scope:
            self.errors.append(
                f"[Line {line}] Semantic Error: '{name}' already defined in this scope."
            )
            return False

        # Prevent void variables
        if symbol_type == "void" and not is_func:
            self.errors.append(
                f"[Line {line}] Semantic Error: Variable '{name}' cannot be of type void."
            )
            return False

        # Create and store symbol
        new_symbol = Symbol(name, symbol_type, line, is_func)
        current_scope[name] = new_symbol
        return True

    # Lookup symbol across all scopes
    def lookup(self, name):

        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        return None

    # Mark variable as initialized
    def mark_as_initialized(self, name):

        symbol = self.lookup(name)
        if symbol:
            symbol.initialized = True

    # Return flattened view of all symbols
    def get_all_symbols(self):

        flat_table = {}
        for scope in self.scopes:
            flat_table.update(scope)

        return flat_table

    # Print current symbol table state
    def print_table(self):

        print("\nSymbol Table State")

        for i, scope in enumerate(self.scopes):
            scope_name = "Global" if i == 0 else f"Local Level {i}"
            print(f"{scope_name}: {scope}")


# Test section
if __name__ == "__main__":

    st = SymbolTable()

    # Global declaration test
    st.declare("global_x", "int", 1)

    # Local scope test
    st.enter_scope()
    st.declare("local_y", "float", 5)

    print("Lookup global_x:", st.lookup("global_x"))
    print("Lookup local_y:", st.lookup("local_y"))

    # Exit scope test
    st.exit_scope()
    print("Lookup local_y after exit:", st.lookup("local_y"))

    st.print_table()