import streamlit as st
import sys
import os

# Importante: Añadir la carpeta padre al path antes de importar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main2 import run_compiler

st.title("Compilador Team 7")

codigo = st.text_area("Código C:", height=200)

if st.button("Compilar"):
    # Llamada directa a la función que ahora devuelve un string
    resultado = run_compiler(codigo.splitlines(), "../Lexer")
    st.code(resultado)