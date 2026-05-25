"""
Semantic Analyzer with Syntax-Directed Translation (SDT)
------------------------------------------------------
Authors: Team 7
Date: May 2026

Description:
This module performs Syntax-Directed Translation over the real grammar 
nodes produced by the LL(1) Parser, validating declarations, scopes, 
and initialization status using the Symbol Table.
"""

import sys
import os

# Permite encontrar el módulo de la Tabla de Símbolos si están en carpetas separadas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from SymbolTable import SymbolTable

class SemanticAnalyzer:
    def __init__(self):
        self.table = SymbolTable()
        self.errors = []

    def analyze(self, node):
        """Punto de entrada para iniciar el recorrido de traducción dirigida por sintaxis (SDT)."""
        self.errors = []  # Limpiar errores de ejecuciones previas
        self.visit(node)
        # Combinamos los errores acumulados del analizador y de la tabla de símbolos
        return self.errors + self.table.errors

    def visit(self, node):
        """Despachador dinámico (Patrón Visitor) según el tipo de nodo de la gramática."""
        if node is None:
            return
        
        method_name = f'visit_{node.node_type}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    # --- REGLAS SEMÁNTICAS MAPEADAS A TU GRAMÁTICA REAL ---

    def visit_STMT(self, node):
        """Regla Semántica para Enunciados (Declaraciones y Asignaciones)."""
        if not node.children:
            return self.generic_visit(node)

        first_child = node.children[0]

        # Caso A: Declaración de Variable -> STMT : [TYPE, id, OPT_ASSIGN, ;]
        if first_child.node_type == 'TYPE':
            type_node = first_child
            id_node = node.children[1]
            opt_assign_node = node.children[2]

            # Extraemos el tipo de dato real (int, float, char, etc.) desde el hijo de TYPE
            var_type = type_node.children[0].node_type if type_node.children else "void"
            var_name = id_node.value

            # Acción Semántica: Registrar en la Tabla de Símbolos
            success = self.table.declare(var_name, var_type, line=0)

            # Si se declara con éxito y tiene inicialización inmediata (OPT_ASSIGN -> = E)
            if success and opt_assign_node.children and opt_assign_node.children[0].node_type == '=':
                self.table.mark_as_initialized(var_name)

        # Caso B: Asignación o llamada -> STMT : [id, STMT_ID_REST]
        elif first_child.node_type == 'id':
            var_name = first_child.value
            stmt_id_rest = node.children[1]

            # Acción Semántica: Verificar existencia previa (Uso antes de declaración)
            symbol = self.table.lookup(var_name)
            if not symbol:
                self.errors.append(f"Error Semántico: La variable '{var_name}' no ha sido declarada.")
            else:
                # Si el resto del ID es una asignación directa (STMT_ID_REST -> = E ;)
                if stmt_id_rest.children and stmt_id_rest.children[0].node_type == '=':
                    self.table.mark_as_initialized(var_name)

        # Continuar el recorrido por el resto de los subárboles de la instrucción
        self.generic_visit(node)

    def visit_PRIMARY(self, node):
        """Regla Semántica para expresiones primarias (Detección de lectura de variables)."""
        if node.children and node.children[0].node_type == 'id':
            var_name = node.children[0].value

            # Acción Semántica: Verificar que la variable que se va a leer exista y esté inicializada
            symbol = self.table.lookup(var_name)
            if not symbol:
                self.errors.append(f"Error Semántico: Variable '{var_name}' utilizada en expresión no está declarada.")
            elif not symbol.initialized:
                self.errors.append(f"Error Semántico: Variable '{var_name}' detectada en expresión antes de ser inicializada.")

        self.generic_visit(node)

    def generic_visit(self, node):
        """Recorrido recursivo estándar por todos los hijos del nodo actual."""
        for child in node.children:
            # Nos aseguramos de visitar solo nodos válidos del AST
            if hasattr(child, 'children'):
                self.visit(child)