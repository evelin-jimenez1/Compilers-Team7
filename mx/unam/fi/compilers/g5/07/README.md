# C-Pure Compiler – Parser & SDT  
**UNAM – Faculty of Engineering**  
**Course:** Compilers  
**Team 7**

---

## Overview

This project implements a **Syntax and Semantic Analyzer (Parser & SDT)** for a simplified C-like language, referred to as **C-Pure**.

The system performs:

- Lexical Analysis (Lexer)  
- Syntactic Analysis (Parser)  
- Semantic Analysis (Syntax Directed Translation – SDT)  
- Abstract Syntax Tree (AST) Construction  
- AST Visualization using Graphviz  

The application includes a **Graphical User Interface (GUI)** for interactive execution.

---

##  Theoretical Background

This project is based on core compiler design concepts:

- Context-Free Grammars (CFG)  
- Top-Down Parsing (Recursive Descent Parser)  
- Syntax Directed Translation (SDT)  
- Abstract Syntax Trees (AST)  

The parser implements a **CFG manually**, where each production rule is mapped to a function.

The AST is a simplified version of the parse tree, containing only semantically relevant elements.

---

## ⚙️ System Architecture

```
Input Source Code
↓
Lexer
↓
Tokens
↓
Parser (Top-Down)
↓
AST + SDT Validation
↓
Output + Visualization
```

---

## 📁 Project Structure

```
Compilers-Team7/
│
├── .gitignore
├── README.md
│
└── mx/
    └── unam/
        └── fi/
            └── compilers/
                └── g5/
                    │
                    ├── doc/
                    │   ├── 07-Compilers-Lexer.pdf
                    │   │
                    │   ├── automatas/
                    │   │   ├── Constants_Automata.png
                    │   │   ├── Identifiers_Automata.png
                    │   │   ├── Keywords_automata.png
                    │   │   ├── Literals_Automata.png
                    │   │   ├── Operators_Automata.png
                    │   │   └── Punctuation_Automata.png
                    │   │
                    │   ├── regular_expressions/
                    │   │   ├── Constants_regular.png
                    │   │   ├── Identifiers_regular.png
                    │   │   ├── Keywords_regular.png
                    │   │   ├── Literals_regular.png
                    │   │   ├── Operator_regular.png
                    │   │   └── Punctuation_regular.png
                    │   │
                    │   └── test/
                    │       ├── .gitkeep
                    │       ├── Test1 Token Recognition and Whitespace Handling.png
                    │       ├── Test1 Token Recognition and Whitespace Handling.txt
                    │       ├── Test2 Comment Processing.png
                    │       ├── Test2 Comment Processing.txt
                    │       ├── Test3 Unknown Token Detection.png
                    │       ├── Test3 Unknown Token Detection.txt
                    │       ├── Test4 Lexical Error.png
                    │       └── Test4 Lexical Error.txt
                    │
                    └── src/
                        └── main/
                            ├── gui.py
                            ├── lexer.py
                            ├── main.py
                            │
                            └── resources/
                                ├── keywords.txt
                                └── tokens.txt
```

---

##  Module Description

### lexer1.py
Performs lexical analysis:

- Tokenizes source code  
- Classifies tokens  
- Detects lexical errors  

---

### parser_sdt.py
Implements:

- Recursive Descent Parser (Top-Down)  
- Grammar rules (CFG)  
- AST construction  
- Semantic validation (SDT)  

Includes checks for:

- Undeclared variables  
- Type mismatches  
- Invalid return types  
- Duplicate declarations  

---

### ast_visualizer.py

- Converts AST into a Graphviz graph  
- Exports a `.png` image  
- Uses color coding for node types  

---

### gui1.py

- Provides user interface  
- Displays tokens, derivation, and AST  
- Executes full compilation pipeline  

---

### main.py

Program entry point:

```bash
python main.py
```

---

##  Installation

### 1. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 2. Install dependencies

```bash
pip install graphviz pillow
```

### 3. Install Graphviz (system)

Download:  
https://graphviz.org/download/

Add to PATH (Windows):

```
C:\Program Files\Graphviz\bin
```

---

## ▶ Usage

```bash
python main.py
```

Steps:

- Enter source code  
- Click RUN COMPILER  
- Select output view:  
  - Lexical Analysis  
  - Syntactic Analysis  
  - AST Graph  

---

##  Example Input

```c
int x = 10;

int main() {
    int i = 1;
    x = x + i;
    return x;
}
```

---

## ✅ Expected Outputs

### Valid Input

```
Parsing Success!
SDT Verified!
```

---

### Semantic Error

```
Parsing Success!
SDT Error...
```

Example:

```c
int main() {
    int x;
    x = "hello";
}
```

---

### Syntax Error

```
Syntax Error...
```

Example:

```c
int main( {
```

---

### Lexical Error

```
Lexical analysis failed...
```

Example:

```c
int $x = 10;
```

---

##  AST Visualization

The system generates a graphical AST:

- Nodes represent program constructs  
- Edges represent structure  
- Helps debugging and understanding program flow  

---

##  Grammar (Simplified)

```
<PROGRAM> ::= <GLOBAL_LIST>

<GLOBAL> ::= <TYPE> id <GLOBAL_REST>

<GLOBAL_REST> ::= ( ) { <STMT_LIST> }
                | <OPT_ASSIGN> ;

<STMT> ::= <IF_STMT>
         | return <OPT_E> ;
         | <TYPE> id <OPT_ASSIGN_LOCAL> ;
         | id = <E> ;
         | id ( <ARG_LIST_OPT> ) ;

<E> ::= <LOGIC_OR>
```

---

##  Key Concepts

- Context-Free Grammar  
- Recursive Descent Parsing  
- Symbol Table and Scope Handling  
- Type Checking  
- AST Construction  
- Modular Design  

---

##  Authors

Team 7:

- Alvarez Salgado Eduardo Antonio  
- González Vázquez Alejandro  
- Jiménez Olivo Evelin  
- Lara Hernández Emmanuel  
- Parra Fernández Héctor Emilio  

---

## Notes

- Designed to meet Parser & SDT requirements  
- Includes additional AST visualization feature  
- Follows modular architecture principles  

---

## Conclusion

This project integrates:

- Lexical Analysis  
- Syntax Analysis  
- Semantic Validation (SDT)  
- AST Construction  
- Graphical Visualization  

Following compiler design principles and best practices.
