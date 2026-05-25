import sys
import os
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog  # Para abrir el explorador de archivos de Windows

# Asegurar que el directorio raíz de módulos esté en el path para tus paquetes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Importaciones exactas de tus submódulos reales
from Lexer.lexer import Lexer
from Parser.grammar import Grammar
from Parser.first_follow import compute_first, compute_follow
from Parser.Parsing_table import LL1Table
from Parser.Parser import Parser
from Semantic.semantic_analyzer import SemanticAnalyzer
from TAC.TAC import TACGenerator
from TAC.Ensamblador import AssemblerGenerator

class CompilerIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador C-Pure - Team 7 (Entrada por Archivo Fuente)")
        self.root.geometry("1150x650")
        self.root.configure(bg="#1e1e24")

        # Variables de control
        self.file_path = None

        # Fuentes
        self.mono_font = tkfont.Font(family="Consolas", size=11)
        self.ui_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")

        # Configuración de la cuadrícula (Grid)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # ---- LADO IZQUIERDO: SELECCIÓN Y VISTA DEL ARCHIVO ----
        self.label_left = tk.Label(root, text="Archivo de Entrada: [Ninguno seleccionado]", bg="#1e1e24", fg="#ffcc00", font=self.ui_font)
        self.label_left.grid(row=0, column=0, pady=(10, 5), padx=20, sticky="w")

        self.code_view = tk.Text(root, bg="#121214", fg="#a9b7c6", font=self.mono_font, bd=1, relief="solid", state="disabled")
        self.code_view.grid(row=1, column=0, padx=(20, 10), pady=5, sticky="nsew")

        # ---- LADO DERECHO: CONSOLA DE SALIDA ----
        label_right = tk.Label(root, text="Consola de Salida / Linker / Resultados ASM:", bg="#1e1e24", fg="#4caf50", font=self.ui_font)
        label_right.grid(row=0, column=1, pady=(10, 5), padx=20, sticky="w")

        self.output_screen = tk.Text(root, bg="#0c0c0d", fg="#33ff33", font=self.mono_font, bd=1, relief="solid", state="disabled")
        self.output_screen.grid(row=1, column=1, padx=(10, 20), pady=5, sticky="nsew")

        # ---- PANEL DE BOTONES ABAJO ----
        btn_frame = tk.Frame(root, bg="#1e1e24")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

        # Botón 1: Seleccionar Archivo Fuente (.c)
        self.select_btn = tk.Button(btn_frame, text="📁 Seleccionar Archivo Fuente (.c)", bg="#007acc", fg="white", 
                                    font=("Segoe UI", 11, "bold"), activebackground="#0062a3", activeforeground="white",
                                    bd=0, padx=15, pady=10, command=self.open_file_selector)
        self.select_btn.pack(side=tk.LEFT, padx=10)

        # Botón 2: Ejecutar el Compilador
        self.compile_btn = tk.Button(btn_frame, text="⚙️ Compilar y Ejecutar Pipeline", bg="#4caf50", fg="white", 
                                     font=("Segoe UI", 11, "bold"), activebackground="#45a049", activeforeground="white",
                                     bd=0, padx=15, pady=10, command=self.run_pipeline)
        self.compile_btn.pack(side=tk.LEFT, padx=10)

    def open_file_selector(self):
        """Abre un cuadro de diálogo para forzar que la entrada sea estrictamente un archivo"""
        file_selected = filedialog.askopenfilename(
            title="Seleccionar Código Fuente C",
            filetypes=[("Archivos C", "*.c"), ("Todos los archivos", "*.*")]
        )
        if file_selected:
            self.file_path = file_selected
            filename = os.path.basename(file_selected)
            self.label_left.config(text=f"Archivo Cargado: {filename}", fg="#4caf50")
            
            # Mostrar el contenido del archivo en el cuadro izquierdo (Solo lectura)
            with open(file_selected, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.code_view.configure(state="normal")
            self.code_view.delete("1.0", tk.END)
            self.code_view.insert(tk.END, content)
            self.code_view.configure(state="disabled")
            
            self.write_to_output(f"[SISTEMA]: Archivo '{filename}' cargado con éxito.\nListo para iniciar la cadena de analizadores.")

    def write_to_output(self, text):
        """Escribe en la terminal interna derecha"""
        self.output_screen.configure(state="normal")
        self.output_screen.delete("1.0", tk.END)
        self.output_screen.insert(tk.END, text)
        self.output_screen.configure(state="disabled")

    def run_pipeline(self):
        """Orquestador de Caja Negra basado en archivo de entrada"""
        if not self.file_path:
            self.write_to_output("[ERROR]: No puedes compilar. Primero debes seleccionar un archivo fuente (.c).")
            return

        # Volvemos a leer el archivo físico directamente desde el path para garantizar el flujo formal
        with open(self.file_path, 'r', encoding='utf-8') as f:
            raw_code = f.read()
        
        codigo_fuente_lineas = raw_code.splitlines()
        path_recursos_lexer = os.path.join(BASE_DIR, "Lexer")

        try:
            # --- TU PIPELINE TEÓRICO COMPLETO (CAJA NEGRA) ---
            lexer = Lexer(codigo_fuente_lineas, path_recursos_lexer)
            tokens = lexer.tokenize()
            
            g = Grammar()
            firsts = compute_first(g.productions, g.non_terminals)
            follows = compute_follow(g.productions, g.non_terminals, firsts, g.start_symbol)
            
            tabla = LL1Table(g, firsts, follows)
            parser = Parser(tabla.table, g.start_symbol)
            ast = parser.parse(tokens)
            
            semantic = SemanticAnalyzer()
            errores = semantic.analyze(ast)
            
            header = "========================================\n"
            header += "   COMPILADOR TEAM 7 - LOG DE PROCESO   \n"
            header += "========================================\n\n"
            reporte = header
            reporte += f"ENTRADA: {os.path.basename(self.file_path)}\n"

            if errores:
                reporte += "ESTADO: [ERROR SEMÁNTICO]\n"
                reporte += "Se encontraron los siguientes errores en los analizadores:\n"
                for err in errores:
                    reporte += f"  - {err}\n"
                self.write_to_output(reporte)
                return
            
            # Generación de código si los analizadores aprueban el archivo fuente
            tac_gen = TACGenerator()
            instrucciones_tac = tac_gen.generate(ast)
            
            ensamblador = AssemblerGenerator()
            asm = ensamblador.generate(instrucciones_tac)
            
            reporte += "ESTADO: [COMPILACIÓN Y ENLACE EXITOSO]\n"
            reporte += "Los analizadores han procesado las cadenas del archivo sin errores.\n\n"
            reporte += "--- CÓDIGO OBJETO (ENSAMBLADOR FINAL) ---\n"
            
            if isinstance(asm, list):
                reporte += "\n".join(asm)
            else:
                reporte += str(asm)
            
            self.write_to_output(reporte)

        except SyntaxError as e:
            self.write_to_output(f"========================================\nESTADO: [ERROR DE SINTAXIS]\nDetalle: {e}")
        except Exception as e:
            self.write_to_output(f"========================================\nESTADO: [ERROR CRÍTICO]\nDetalle: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CompilerIDE(root)
    root.mainloop()