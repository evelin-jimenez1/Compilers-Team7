"""
Purpose:
    Generation and configuration of the graphical user interface for the
    C-Pure Compiler. Supports manual input, lexical analysis, syntactic
    analysis, SDT validation, and AST visualization.
"""

import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from PIL import Image, ImageTk

from lexer import Lexer
from parser_sdt import Parser 
from ast_visualizer import render_ast


# ------------------------------------------------------------
# Style configuration
# ------------------------------------------------------------

BG_COLOR = "#121212"
CARD_COLOR = "#1e1e1e"
TEXT_BG = "#0f0f0f"
TEXT_FG = "#f5f5f5"
ACCENT = "#2d7ff9"
BORDER = "#333333"
LEXEME_COLOR = "#a64d59"


lexer_results = []
parser_derivation = ""
ast_image_reference = None


def run_gui():
    global lexer_results, parser_derivation, ast_image_reference

    root = tk.Tk()
    root.title("C-Pure Compiler - Team 7")
    root.geometry("1100x900")
    root.configure(bg=BG_COLOR)

    resource_dir = Path(__file__).parent / "resources"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    text_font = ("Courier New", 11)

    # --------------------------------------------------------
    # Output display logic
    # --------------------------------------------------------

    def show_output():
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)

        mode = view_mode.get()

        if mode == 0:
            for token in lexer_results:
                output_text.insert(tk.END, f"[{token['value']}]", "lexeme")
                output_text.insert(
                    tk.END,
                    f" - {token['type']} at line: {token['line']}, "
                    f"Col: {token['column']}\n"
                )

            output_text.tag_config("lexeme", foreground=LEXEME_COLOR)

        elif mode == 1:
            output_text.insert(tk.END, parser_derivation)

        elif mode == 2:
            output_text.insert(
                tk.END,
                "AST visualization generated below.\n"
                "If the image is empty, run the compiler first.\n"
            )

        output_text.config(state=tk.DISABLED)

    # --------------------------------------------------------
    # AST image display logic
    # --------------------------------------------------------

    def show_ast_image(image_path):
        global ast_image_reference

        try:
            image = Image.open(image_path)

            max_width = 900
            max_height = 350

            image.thumbnail((max_width, max_height))

            ast_image_reference = ImageTk.PhotoImage(image)

            ast_label.config(image=ast_image_reference)
            ast_label.image = ast_image_reference

        except Exception as error:
            ast_label.config(image="")
            messagebox.showerror(
                "AST Visualization Error",
                f"Could not display AST image:\n{error}"
            )

    # --------------------------------------------------------
    # Compiler execution logic
    # --------------------------------------------------------

    def analyze_text():
        global lexer_results, parser_derivation

        text = input_text.get("1.0", tk.END).strip()

        if not text:
            messagebox.showwarning("Warning", "Please enter some code first.")
            return

        try:
            lexer = Lexer(text.split("\n"), str(resource_dir))
            lexer_results = lexer.tokenize()

            unknown_tokens = [
                token for token in lexer_results
                if token["type"] == "Unknown"
            ]

            if unknown_tokens:
                errors = "\n".join(
                    f"Unknown token '{token['value']}' at line "
                    f"{token['line']}, column {token['column']}"
                    for token in unknown_tokens
                )

                parser_derivation = (
                    "Lexical analysis failed.\n\n"
                    "Unknown tokens found:\n"
                    f"{errors}\n\n"
                    "Parsing and SDT validation were not executed."
                )

                ast_label.config(image="")
                show_output()
                messagebox.showerror("Lexical Error", errors)
                return

            parser = Parser(lexer_results)
            ast = parser.parse_program()
            parser_derivation = parser.get_derivation(ast)

            ast_path = output_dir / "ast_output"
            image_path = render_ast(ast, str(ast_path), "png")

            show_ast_image(image_path)
            show_output()

            if parser.sdt_errors:
                messagebox.showwarning(
                    "SDT Error",
                    "Parsing completed, but semantic errors were found."
                )
            else:
                messagebox.showinfo(
                    "Success",
                    "Parsing Success!\nSDT Verified!\nAST Generated!"
                )

        except Exception as error:
            ast_label.config(image="")
            messagebox.showerror("Syntax Error", str(error))

    # --------------------------------------------------------
    # UI Elements
    # --------------------------------------------------------

    wrapper = tk.Frame(root, bg=BG_COLOR)
    wrapper.pack(fill="both", expand=True, padx=20, pady=20)

    input_card = tk.Frame(
        wrapper,
        bg=CARD_COLOR,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    input_card.pack(fill="both", expand=True, pady=(0, 10))

    tk.Label(
        input_card,
        text="Source Code Input",
        font=("Arial", 12, "bold"),
        bg=CARD_COLOR,
        fg=TEXT_FG
    ).pack(anchor="w", padx=15, pady=10)

    input_text = tk.Text(
        input_card,
        height=10,
        font=text_font,
        bg=TEXT_BG,
        fg=TEXT_FG,
        insertbackground=TEXT_FG,
        relief="flat"
    )
    input_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    button_frame = tk.Frame(wrapper, bg=BG_COLOR)
    button_frame.pack(fill="x", pady=10)

    tk.Button(
        button_frame,
        text="RUN COMPILER",
        command=analyze_text,
        bg=ACCENT,
        fg="white",
        font=("Arial", 10, "bold"),
        relief="flat",
        padx=25,
        pady=10
    ).pack(side="left")

    selector_frame = tk.Frame(wrapper, bg=BG_COLOR)
    selector_frame.pack(fill="x", pady=(10, 0))

    view_mode = tk.IntVar(value=0)

    tk.Radiobutton(
        selector_frame,
        text="Lexical Analysis (Tokens)",
        variable=view_mode,
        value=0,
        command=show_output,
        bg=BG_COLOR,
        fg=TEXT_FG,
        selectcolor=CARD_COLOR,
        activebackground=BG_COLOR,
        activeforeground=TEXT_FG,
        font=("Arial", 10)
    ).pack(side="left", padx=5)

    tk.Radiobutton(
        selector_frame,
        text="Syntactic Analysis (Derivation)",
        variable=view_mode,
        value=1,
        command=show_output,
        bg=BG_COLOR,
        fg=TEXT_FG,
        selectcolor=CARD_COLOR,
        activebackground=BG_COLOR,
        activeforeground=TEXT_FG,
        font=("Arial", 10)
    ).pack(side="left", padx=5)

    tk.Radiobutton(
        selector_frame,
        text="AST Graph",
        variable=view_mode,
        value=2,
        command=show_output,
        bg=BG_COLOR,
        fg=TEXT_FG,
        selectcolor=CARD_COLOR,
        activebackground=BG_COLOR,
        activeforeground=TEXT_FG,
        font=("Arial", 10)
    ).pack(side="left", padx=5)

    output_card = tk.Frame(
        wrapper,
        bg=CARD_COLOR,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    output_card.pack(fill="both", expand=True, pady=(5, 10))

    output_text = tk.Text(
        output_card,
        height=12,
        font=text_font,
        bg=TEXT_BG,
        fg=TEXT_FG,
        relief="flat",
        state=tk.DISABLED
    )
    output_text.pack(fill="both", expand=True, padx=15, pady=15)

    ast_card = tk.Frame(
        wrapper,
        bg=CARD_COLOR,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    ast_card.pack(fill="both", expand=True, pady=(5, 0))

    tk.Label(
        ast_card,
        text="AST Visualization",
        font=("Arial", 12, "bold"),
        bg=CARD_COLOR,
        fg=TEXT_FG
    ).pack(anchor="w", padx=15, pady=10)

    ast_label = tk.Label(
        ast_card,
        bg=TEXT_BG,
        fg=TEXT_FG
    )
    ast_label.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    root.mainloop()


if __name__ == "__main__":
    run_gui()