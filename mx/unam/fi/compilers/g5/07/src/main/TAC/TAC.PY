"""
TAC Generator (Código de Tres Direcciones) - Full Grammar Edition
-----------------------------------------------------------------
Authors: Team 7
Date: May 2026

Description:
Este módulo recorre el AST completo. Traduce expresiones aritméticas,
declaraciones, retornos y aplana estructuras de control (IF, WHILE)
usando Etiquetas (Labels) y Saltos Condicionales (Gotos).
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Ast.ASTNode import ASTNode

class TACGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instruction):
        """Agrega una instrucción al código lineal."""
        self.instructions.append(instruction)

    def generate(self, node):
        self.instructions = []
        self.visit(node)
        return self.instructions

    def visit(self, node):
        if not node:
            return

        # 1. Detectar sentencias IF / ELSE
        if node.node_type == 'IF_STMT' or (node.children and node.children[0].node_type == 'if'):
            self._process_if(node)
            return

        # 2. Detectar bucles WHILE
        if node.node_type == 'WHILE_STMT' or (node.children and node.children[0].node_type == 'while'):
            self._process_while(node)
            return

        # 3. Detectar Declaraciones, Asignaciones y Returns
        if node.node_type == 'STMT':
            first = node.children[0] if node.children else None
            
            if first and first.node_type in ['TYPE', 'id']:
                self._process_assignment(node)
                return
                
            if first and first.node_type == 'return':
                self._process_return(node)
                return

        # Recorrido genérico para buscar más instrucciones
        for child in node.children:
            if isinstance(child, ASTNode):
                self.visit(child)

    # --- GENERADORES ESPECÍFICOS ---

    def _process_assignment(self, node):
        tokens = self._flatten_expr(node)
        # Filtramos palabras clave y punto y coma
        tokens = [t for t in tokens if t not in ['int', 'float', 'void', 'char', 'double', ';']]
        
        if '=' in tokens:
            eq_idx = tokens.index('=')
            var_name = tokens[eq_idx - 1]
            expr_tokens = tokens[eq_idx + 1:]
            
            if len(expr_tokens) == 1:
                self.emit(f"{var_name} = {expr_tokens[0]}")
            else:
                expr_str = " ".join(expr_tokens)
                t = self.new_temp()
                self.emit(f"{t} = {expr_str}")
                self.emit(f"{var_name} = {t}")

    def _process_return(self, node):
        tokens = self._flatten_expr(node)
        tokens = [t for t in tokens if t not in ['return', ';']]
        if tokens:
            self.emit(f"return {' '.join(tokens)}")
        else:
            self.emit("return")

    def _process_if(self, node):
        # Extraer la condición entre paréntesis
        cond_tokens = self._extract_between(node, '(', ')')
        cond_str = " ".join(cond_tokens) if cond_tokens else "1"
        
        t_cond = self.new_temp()
        self.emit(f"{t_cond} = {cond_str}")
        
        l_else = self.new_label()
        l_end = self.new_label()
        
        # Salto condicional
        self.emit(f"ifFalse {t_cond} goto {l_else}")
        
        # Buscar los bloques de código { }
        blocks = self._find_blocks(node)
        
        # Visitar cuerpo del IF
        if len(blocks) > 0:
            self.visit(blocks[0])
            
        self.emit(f"goto {l_end}")
        self.emit(f"Label {l_else}:")
        
        # Visitar cuerpo del ELSE (si existe)
        if len(blocks) > 1:
            self.visit(blocks[1])
            
        self.emit(f"Label {l_end}:")

    def _process_while(self, node):
        l_start = self.new_label()
        l_end = self.new_label()
        
        self.emit(f"Label {l_start}:")
        
        cond_tokens = self._extract_between(node, '(', ')')
        cond_str = " ".join(cond_tokens) if cond_tokens else "1"
        
        t_cond = self.new_temp()
        self.emit(f"{t_cond} = {cond_str}")
        self.emit(f"ifFalse {t_cond} goto {l_end}")
        
        blocks = self._find_blocks(node)
        if len(blocks) > 0:
            self.visit(blocks[0])
            
        self.emit(f"goto {l_start}")
        self.emit(f"Label {l_end}:")

    # --- FUNCIONES DE SOPORTE (AST UTILS) ---

    def _flatten_expr(self, node):
        res = []
        if node.value and node.node_type not in ['epsilon']:
            res.append(node.value)
        for child in node.children:
            if isinstance(child, ASTNode):
                res.extend(self._flatten_expr(child))
        return res

    def _extract_between(self, node, start_char, end_char):
        tokens = self._flatten_expr(node)
        try:
            start = tokens.index(start_char)
            # Buscar el último paréntesis de cierre
            end = len(tokens) - 1 - tokens[::-1].index(end_char)
            return tokens[start+1:end]
        except ValueError:
            return []

    def _find_blocks(self, node):
        """Busca nodos tipo BLOCK de manera inteligente."""
        blocks = []
        for child in node.children:
            if isinstance(child, ASTNode):
                if child.node_type == 'BLOCK' or child.node_type == 'STMT_LIST':
                    blocks.append(child)
                elif child.node_type not in ['IF_STMT', 'WHILE_STMT']: 
                    # Buscar más profundo sin entrar a otros ifs anidados
                    blocks.extend(self._find_blocks(child))
        return blocks