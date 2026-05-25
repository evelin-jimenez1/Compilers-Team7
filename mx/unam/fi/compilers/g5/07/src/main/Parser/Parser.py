"""
LL(1) Predictive Parser - AST Builder & Auto-Fix Edition
--------------------------------------------------------
Authors: Team 7
Date: May 2026

Description:
This module implements the execution driver for the LL(1) syntax analyzer. 
It incorporates a Semantic Stack to dynamically construct the AST and 
includes a fail-safe to correct Lexer misclassifications on the fly.
"""

import sys
import os

# Permite que Parser.py encuentre la carpeta 'AST'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Ast.ASTNode import ASTNode

class Parser:
    def __init__(self, parsing_table, start_symbol):
        self.parsing_table = parsing_table
        self.start_symbol = start_symbol

    def _get_grammar_symbol(self, token):
        """
        Traduce las categorías y valores del Lexer a los símbolos exactos de la Gramática.
        Incluye un parche para forzar el reconocimiento de palabras clave.
        """
        t_type = token['type']
        t_val = token['value']

        # PARCHE DE SEGURIDAD: Lista de palabras reservadas de tu gramática
        palabras_reservadas = ['int', 'float', 'void', 'char', 'double', 'if', 'else', 'while', 'for', 'return', 'do']

        if t_type == 'Keywords' or t_val in palabras_reservadas:
            return t_val  # Fuerza a que 'int' sea 'int' y no 'id'
        elif t_type == 'Identifiers':
            return 'id'
        elif t_type == 'Constants':
            return 'constant'
        elif t_type == 'Literals':
            return 'literal'
        elif t_type in ['Operators', 'Punctuation']:
            return t_val
        return t_type

    def parse(self, token_stream):
        """
        Procesa el flujo de tokens. Si es válido, construye y retorna el AST.
        """
        tokens = list(token_stream) + [{'type': '$', 'value': '$', 'line': -1}]
        stack = ['$', self.start_symbol]
        node_stack = []
        
        token_index = 0
        current_token = tokens[token_index]
        
        while len(stack) > 0:
            top = stack[-1]
            
            # ACCIÓN SEMÁNTICA: CONSTRUCCIÓN DEL AST
            if isinstance(top, tuple) and top[0] == '#BUILD':
                stack.pop()
                _, nt_type, num_children = top
                
                children = []
                for _ in range(num_children):
                    if node_stack:
                        children.insert(0, node_stack.pop())
                
                parent_node = ASTNode(node_type=nt_type, children=children)
                node_stack.append(parent_node)
                continue
            
            lookahead_key = self._get_grammar_symbol(current_token)
            lookahead_value = current_token['value']
            current_line = current_token['line']

            # Case 1: Match
            if top == lookahead_key:
                stack.pop()
                leaf_node = ASTNode(node_type=top, value=lookahead_value)
                node_stack.append(leaf_node)
                
                token_index += 1
                if token_index < len(tokens):
                    current_token = tokens[token_index]
            
            # Case 2: Terminal Mismatch / Error
            elif top not in self.parsing_table:
                raise SyntaxError(f"Line {current_line}: Unexpected token '{lookahead_value}'. Expected '{top}'.")
            
            # Case 3: Expandir
            else:
                raw_cell_content = self.parsing_table[top].get(lookahead_key, [])
                
                if not raw_cell_content:
                    raise SyntaxError(f"Line {current_line}: Syntax error near '{lookahead_value}'. No rule for <{top}>.")
                
                full_rule_str = raw_cell_content[0]
                body_part_str = full_rule_str.split("->")[1].strip()
                production_body = body_part_str.split()

                stack.pop() 
                
                if production_body == ['epsilon']:
                    stack.append(('#BUILD', top, 0))
                else:
                    stack.append(('#BUILD', top, len(production_body)))
                    for symbol in reversed(production_body):
                        stack.append(symbol)

        if node_stack:
            return node_stack[0]
        return None