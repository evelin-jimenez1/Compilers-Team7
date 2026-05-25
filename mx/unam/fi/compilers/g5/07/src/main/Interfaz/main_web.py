import sys
import os
from pyscript import document

# En PyScript, la carpeta 'Interfaz' es el directorio raíz actual ('.')
# Forzamos los paths virtuales directamente sin usar __file__
sys.path.append(".")

from Lexer.lexer import Lexer
from Parser.grammar import Grammar
from Parser.first_follow import compute_first, compute_follow
from Parser.Parsing_table import LL1Table
from Parser.Parser import Parser
from Semantic.semantic_analyzer import SemanticAnalyzer
from TAC.TAC import TACGenerator
from TAC.Ensamblador import AssemblerGenerator

def web_compiler_bridge(event):
    """
    Controlador de eventos para el botón de la página web.
    Toma el texto del navegador, lo procesa con tus clases y renderiza la salida.
    """
    text_area = document.getElementById("code-input")
    output_screen = document.getElementById("output-screen")
    
    output_screen.innerText = "Iniciando análisis del pipeline en el navegador...\n"
    
    # Transformar el string del textarea en una lista de líneas (como lo requiere tu Lexer)
    raw_code = text_area.value
    codigo_fuente_lineas = raw_code.splitlines()
    
    # Ruta virtual mapeada de manera local dentro del navegador por PyScript
    path_recursos_lexer = "./Lexer"

    try:
        # --- TU PROCESO INTERNO EXACTO (CAJA NEGRA) ---
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
        
        # --- FORMATO DE SALIDA PROFESIONAL ---
        header = "========================================\n"
        header += "   COMPILADOR TEAM 7 - LOG DE PROCESO   \n"
        header += "========================================\n"
        
        if errores:
            reporte = header + "ESTADO: [ERROR SEMÁNTICO]\n"
            reporte += "Se encontraron los siguientes errores:\n"
            for err in errores:
                reporte += f"  - {err}\n"
            output_screen.innerText = reporte
            return
        
        # Generación del Backend si no hay errores semánticos
        tac_gen = TACGenerator()
        instrucciones_tac = tac_gen.generate(ast)
        ensamblador = AssemblerGenerator(instrucciones_tac)
        asm = ensamblador.generate()
        
        reporte = header + "ESTADO: [COMPILACIÓN EXITOSA]\n"
        reporte += "Código generado correctamente.\n\n"
        reporte += "--- ENSAMBLADOR ---\n"
        reporte += "\n".join(asm)
        
        # Pintar el reporte en el cuadro verde de la interfaz web
        output_screen.innerText = reporte

    except SyntaxError as e:
        output_screen.innerText = f"========================================\nESTADO: [ERROR DE SINTAXIS]\nDetalle: {e}"
    except Exception as e:
        output_screen.innerText = f"========================================\nESTADO: [ERROR CRÍTICO]\nDetalle: {str(e)}"

# Conectar el botón del HTML con la ejecución de nuestra función puente de Python
document.getElementById("compile-btn").onclick = web_compiler_bridge