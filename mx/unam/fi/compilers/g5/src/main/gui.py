import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from lexer import Lexer


def format_results(tokens, total_tokens):
    if tokens["Unknown"]:
        result = "Error: There are unrecognized tokens in the input.\n"
        result += f"Unknown tokens: {sorted(tokens['Unknown'])}"
        return result

    output = []
    for category, values in tokens.items():
        if category != "Unknown":
            output.append(f"{category}: {sorted(values)}")
    output.append(f"Total Tokens: {total_tokens}")
    return "\n".join(output)


def run_gui():
    root = tk.Tk()
    root.title("C Lexer")
    root.geometry("900x650")

    resource_dir = Path(__file__).parent / "resources"

    # ---------- Functions ----------
    def analyze_text():
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
        file_path = filedialog.askopenfilename(
            title="Open C file",
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
        input_text.delete("1.0", tk.END)
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.config(state=tk.DISABLED)

    # ---------- UI ----------
    title_label = tk.Label(root, text="Lexical Analyzer for C", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)

    input_label = tk.Label(root, text="Input Code:", font=("Arial", 12, "bold"))
    input_label.pack(anchor="w", padx=10)

    input_text = tk.Text(root, height=15, width=100, font=("Courier New", 11))
    input_text.pack(padx=10, pady=5, fill="both")

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    analyze_button = tk.Button(button_frame, text="Analyze String", command=analyze_text, width=15)
    analyze_button.grid(row=0, column=0, padx=5)

    open_button = tk.Button(button_frame, text="Open File", command=open_file, width=15)
    open_button.grid(row=0, column=1, padx=5)

    clear_button = tk.Button(button_frame, text="Clear", command=clear_all, width=15)
    clear_button.grid(row=0, column=2, padx=5)

    output_label = tk.Label(root, text="Output:", font=("Arial", 12, "bold"))
    output_label.pack(anchor="w", padx=10)

    output_text = tk.Text(root, height=15, width=100, font=("Courier New", 11), state=tk.DISABLED)
    output_text.pack(padx=10, pady=5, fill="both", expand=True)

    root.mainloop()