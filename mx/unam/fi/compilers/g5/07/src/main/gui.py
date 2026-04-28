"""
Purpose:
    Generation and configuration of the graphical user interface where the user will be able to input text to the lexical analyzer, as well as the input and output configuration of the program so the user can submit the input and receive the response from the lexical analyzer.

Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date:
    March 15, 2026

Dependencies:
    - tkinter (Standard Python library for creating GUIs)
    - pathlib (Standard Python library for OS-independent path handling)
    - lexer (Custom local module containing the Lexer class)
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from lexer import Lexer

# Implements hexadecimal color codes for the dark mode theme.
BG_COLOR = "#121212"
CARD_COLOR = "#1e1e1e"
TEXT_BG = "#0f0f0f"
TEXT_FG = "#f5f5f5"
ACCENT = "#2d7ff9"
ACCENT_HOVER = "#1f6ae6"
SECONDARY = "#2b2b2b"
BORDER = "#333333"


def format_results(tokens, total_tokens):
    """
    This function is responsible for receiving the data processed by the lexer.py program 
    and formatting it into readable output.
    
    - Acts as an error filter by detecting "UNKNOWN" tokens, halting the process, 
      and returning a warning with the respective unidentified tokens.
    - Organizes the tokens into established categories (keywords, identifiers, operators, 
      constants, and punctuation marks) and sorts them alphabetically.
    - Indicates the final token count.
    """
    if tokens["Unknown"]:
        result = "Error: There are unrecognized tokens in the input.\n"
        result += f"Unknown tokens: {sorted(tokens['Unknown'])}"
        return result

    output = []
    ordered_categories = [
        "Keywords",
        "Identifiers",
        "Constants",
        "Operators",
        "Punctuation",
        "Literals",
    ]

    for category in ordered_categories:
        if category in tokens:
            output.append(f"{category}: {sorted(tokens[category])}")

    output.append(f"Total Tokens: {total_tokens}")
    return "\n\n".join(output)


def run_gui():
    """
    Function responsible for deploying the window and displaying the interface.
    """
    
    # ---------- A. Window Configuration ----------
    # Creates the main window with the title "Lexer", setting its default size 
    # as well as the minimum size it can be scaled down to.
    root = tk.Tk()
    root.title("Lexer")
    root.geometry("980x700")
    root.minsize(900, 650)
    root.configure(bg=BG_COLOR)

    resource_dir = Path(__file__).parent / "resources"

    # ---------- styles ----------
    title_font = ("Arial", 20, "bold")
    label_font = ("Arial", 11, "bold")
    text_font = ("Courier New", 11)
    button_font = ("Arial", 10, "bold")

    # ---------- B. Visual Effect Functions (Hover) ----------
    # Changes the color of the buttons when the mouse hovers over them.
    def on_enter(event, button, hover_color):
        button.config(bg=hover_color)

    def on_leave(event, button, normal_color):
        button.config(bg=normal_color)

    # ---------- C. Button Logic ----------
    def analyze_text():
        """
        Reads the text entered by the user. If the input is empty, it triggers a warning. 
        If text is found, it sends it to the Lexer class and returns the result to print it on the output screen.
        """
        text = input_text.get("1.0", tk.END).strip()

        if not text:
            messagebox.showwarning("Warning", "Please enter some code first.")
            return

        lexemes = text.split("\n")
        lexer = Lexer(lexemes, str(resource_dir))
        tokens = lexer.tokenize()

        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, format_results(tokens, lexer.get_total_tokens()))
        output_text.config(state=tk.DISABLED)

    def open_file():
        """
        Responsible for opening the file explorer to access a document 
        (either .txt or .c), reading its content, and analyzing it.
        """
        file_path = filedialog.askopenfilename(
            title="Open file",
            filetypes=[("C files", "*.c *.h *.txt"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            input_text.delete("1.0", tk.END)
            input_text.insert(tk.END, content)

            lexemes = content.split("\n")
            lexer = Lexer(lexemes, str(resource_dir))
            tokens = lexer.tokenize()

            output_text.config(state=tk.NORMAL)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, format_results(tokens, lexer.get_total_tokens()))
            output_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def clear_all():
        """
        Clears all content in both the input and output areas.
        """
        input_text.delete("1.0", tk.END)
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.config(state=tk.DISABLED)

    # ---------- D. Visual Interface Construction (Widgets) ----------
    # Responsible for generating the graphical interface using tkinter.

    # wrapper: Creates a margin around all elements.
    wrapper = tk.Frame(root, bg=BG_COLOR)
    wrapper.pack(fill="both", expand=True, padx=18, pady=18)

    # title_label: Sets the title of the lexical analyzer.
    title_label = tk.Label(
        wrapper,
        text="Lexer",
        font=title_font,
        bg=BG_COLOR,
        fg=TEXT_FG
    )
    title_label.pack(pady=(0, 14))

    # input_card: Acts as a frame simulating a visual card.
    input_card = tk.Frame(
        wrapper,
        bg=CARD_COLOR,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    input_card.pack(fill="both", expand=True, pady=(0, 12))

    # input_label: The text label displaying 'Input code'.
    input_label = tk.Label(
        input_card,
        text="Input code",
        font=label_font,
        bg=CARD_COLOR,
        fg=TEXT_FG
    )
    input_label.pack(anchor="w", padx=14, pady=(12, 8))

    input_text_frame = tk.Frame(input_card, bg=CARD_COLOR)
    input_text_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    # input_scroll: Scrollbar for the input text area.
    input_scroll = tk.Scrollbar(input_text_frame)
    input_scroll.pack(side="right", fill="y")

    # input_text: Text area where the user can write the input.
    input_text = tk.Text(
        input_text_frame,
        height=14,
        font=text_font,
        bg=TEXT_BG,
        fg=TEXT_FG,
        insertbackground=TEXT_FG,
        selectbackground=ACCENT,
        relief="flat",
        bd=0,
        wrap="none",
        yscrollcommand=input_scroll.set
    )
    input_text.pack(fill="both", expand=True)
    input_scroll.config(command=input_text.yview)

    # button_frame: Container holding the three buttons ("Analyze String", "Open File", "Clear") 
    # along with their respective visual methods.
    button_frame = tk.Frame(wrapper, bg=BG_COLOR)
    button_frame.pack(fill="x", pady=(0, 12))

    analyze_button = tk.Button(
        button_frame,
        text="Analyze String",
        command=analyze_text,
        font=button_font,
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=16,
        pady=10,
        cursor="hand2"
    )
    analyze_button.pack(side="left", padx=(0, 10))

    open_button = tk.Button(
        button_frame,
        text="Open File",
        command=open_file,
        font=button_font,
        bg=SECONDARY,
        fg=TEXT_FG,
        activebackground="#3a3a3a",
        activeforeground=TEXT_FG,
        relief="flat",
        bd=0,
        padx=16,
        pady=10,
        cursor="hand2"
    )
    open_button.pack(side="left", padx=(0, 10))

    clear_button = tk.Button(
        button_frame,
        text="Clear",
        command=clear_all,
        font=button_font,
        bg=SECONDARY,
        fg=TEXT_FG,
        activebackground="#3a3a3a",
        activeforeground=TEXT_FG,
        relief="flat",
        bd=0,
        padx=16,
        pady=10,
        cursor="hand2"
    )
    clear_button.pack(side="left")

    analyze_button.bind("<Enter>", lambda e: on_enter(e, analyze_button, ACCENT_HOVER))
    analyze_button.bind("<Leave>", lambda e: on_leave(e, analyze_button, ACCENT))

    open_button.bind("<Enter>", lambda e: on_enter(e, open_button, "#3a3a3a"))
    open_button.bind("<Leave>", lambda e: on_leave(e, open_button, SECONDARY))

    clear_button.bind("<Enter>", lambda e: on_enter(e, clear_button, "#3a3a3a"))
    clear_button.bind("<Leave>", lambda e: on_leave(e, clear_button, SECONDARY))

    # output_card: Card that displays the program's output.
    output_card = tk.Frame(
        wrapper,
        bg=CARD_COLOR,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    output_card.pack(fill="both", expand=True)

    output_label = tk.Label(
        output_card,
        text="Output",
        font=label_font,
        bg=CARD_COLOR,
        fg=TEXT_FG
    )
    output_label.pack(anchor="w", padx=14, pady=(12, 8))

    output_text_frame = tk.Frame(output_card, bg=CARD_COLOR)
    output_text_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    output_scroll = tk.Scrollbar(output_text_frame)
    output_scroll.pack(side="right", fill="y")

    output_text = tk.Text(
        output_text_frame,
        height=14,
        font=text_font,
        bg=TEXT_BG,
        fg=TEXT_FG,
        insertbackground=TEXT_FG,
        selectbackground=ACCENT,
        relief="flat",
        bd=0,
        wrap="word",
        state=tk.DISABLED,
        yscrollcommand=output_scroll.set
    )
    output_text.pack(fill="both", expand=True)
    output_scroll.config(command=output_text.yview)

    # ---------- E. Main Loop ----------
    # root.mainloop(): Allows the interface to keep running and wait for user interaction.
    root.mainloop()