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
identifiers, their types, initialization state, and scope levels using
a stack-based scoping mechanism.
"""

class Symbol:
    """Represents a single entry in the symbol table."""
    def __init__(self, name, symbol_type, line, is_function=False):
        self.name = name
        self.type = symbol_type
        self.line = line
        self.is_func = is_function
        self.initialized = False
        self.params = []

    def __repr__(self):
        cat = "FUNC" if self.is_func else "VAR"
        return f"[{cat}] {self.name} ({self.type}) - Init: {self.initialized}"


class SymbolTable:
    """Manages scopes using a stack of dictionaries (global + local scopes)."""
    def __init__(self):
        self.scopes = [{}]
        self.errors = []

    def enter_scope(self):
        """Enter a new local scope."""
        self.scopes.append({})

    def exit_scope(self):
        """Exit current scope."""
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, symbol_type, line, is_func=False):
        """Declare a new symbol in current scope, detecting redeclarations."""
        current_scope = self.scopes[-1]

        if name in current_scope:
            self.errors.append(f"[Line {line}] Semantic Error: '{name}' already defined in this scope.")
            return False

        if symbol_type == "void" and not is_func:
            self.errors.append(f"[Line {line}] Semantic Error: Variable '{name}' cannot be of type void.")
            return False

        new_symbol = Symbol(name, symbol_type, line, is_func)
        current_scope[name] = new_symbol
        return True

    def lookup(self, name):
        """Lookup symbol across all scopes, from current back to global."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def mark_as_initialized(self, name):
        """Mark variable as initialized."""
        symbol = self.lookup(name)
        if symbol:
            symbol.initialized = True

    def get_all_symbols(self):
        """Return a flattened view of all symbols (useful for debugging)."""
        flat_table = {}
        for scope in self.scopes:
            flat_table.update(scope)
        return flat_table