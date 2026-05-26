"""
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Program description:
Professional PySide6 GUI for the C-Pure Compiler.
Provides an IDE-like interface with a full pipeline:
  Lexer → Parser → Parse Tree → AST → Semantic → TAC → ASM → Execution

Pipeline Cases:
  Case 1: Parsing OK + SDT OK  → Full pipeline. AST shown and downloadable.
  Case 2: Parsing Error        → AST/TAC/ASM/EXEC show error messages.
  Case 3: Parsing OK + SDT Err → AST not generated; TAC/ASM/EXEC show error messages.

Dependencies:
    - PySide6
    - qt-material
    - graphviz (optional, for AST image export)
"""

import sys
import os
from pathlib import Path

# ── Resolve project root so imports work from any CWD ─────────────────────────
THIS_FILE  = Path(__file__).resolve()
GUI_DIR    = THIS_FILE.parent          # …/main/Gui/
MAIN_DIR   = GUI_DIR.parent            # …/main/
RES_DIR    = MAIN_DIR / "Lexer"        # keywords.txt & tokens.txt
OUTPUT_DIR = GUI_DIR / "output"        # …/main/Gui/output/

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

if str(MAIN_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_DIR))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPlainTextEdit, QTextEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton, QStatusBar,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QSizePolicy,
    QAbstractItemView, QTreeWidget, QTreeWidgetItem,
)
from PySide6.QtCore import (
    Qt, QRect, QSize, QThread, Signal, Slot, QTimer,
)
from PySide6.QtGui import (
    QColor, QPainter, QFont, QFontMetrics, QTextCharFormat,
    QSyntaxHighlighter, QKeySequence, QShortcut, QIcon, QPalette,
    QTextBlockUserData, QTextDocument, QAction, QPixmap,
)
from qt_material import apply_stylesheet

# ── Colours for token categories ──────────────────────────────────────────────
TOKEN_COLORS: dict[str, str] = {
    "Keywords":    "#82aaff",
    "Identifiers": "#c3e88d",
    "Operators":   "#f78c6c",
    "Punctuation": "#89ddff",
    "Constants":   "#f07178",
    "Literals":    "#c792ea",
    "Unknown":     "#ff5370",
}

# ── Pipeline stage definitions ─────────────────────────────────────────────────
STAGES = [
    ("LEX",    "Lexer Output",      "#82aaff"),
    ("PAR",    "Parser Output",     "#c3e88d"),
    ("TREE",   "Parse Tree",        "#f78c6c"),
    ("SEM",    "Semantic Output",   "#ffcb6b"),
    ("AST",    "AST",               "#c792ea"),
    ("TAC",    "TAC Output",        "#89ddff"),
    ("ASM",    "Assembly Output",   "#f07178"),
    ("EXEC",   "Execution Output",  "#80cbc4"),
]

# ── Error message templates ────────────────────────────────────────────────────
MSG_AST_PARSE_ERROR = (
    "AST was not generated.\n\n"
    "Reason: Parsing errors were found in the source code.\n"
    "The parser could not build a valid syntax tree.\n\n"
    "Please fix the syntax errors reported in the Errors tab and try again."
)

MSG_AST_SEMANTIC_ERROR = (
    "AST was not generated.\n\n"
    "Reason: Semantic (SDT) errors were found in the source code.\n"
    "The semantic analyzer detected invalid usage of variables or types.\n\n"
    "Please fix the semantic errors reported in the Errors tab and try again."
)

MSG_TAC_PARSE_ERROR = (
    "TAC was not generated due to parsing errors.\n\n"
    "The Three-Address Code requires a valid syntax tree.\n"
    "Fix the syntax errors and recompile."
)

MSG_TAC_SEMANTIC_ERROR = (
    "TAC was not generated due to semantic errors.\n\n"
    "The Three-Address Code requires a semantically valid program.\n"
    "Fix the semantic errors and recompile."
)

MSG_ASM_PARSE_ERROR = (
    "Assembly was not generated due to parsing errors.\n\n"
    "Assembly output requires a valid syntax tree and TAC.\n"
    "Fix the syntax errors and recompile."
)

MSG_ASM_SEMANTIC_ERROR = (
    "Assembly was not generated due to semantic errors.\n\n"
    "Assembly output requires a semantically valid program.\n"
    "Fix the semantic errors and recompile."
)

MSG_EXEC_PARSE_ERROR = (
    "No assembly code to execute.\n\n"
    "Execution requires a successfully compiled program.\n"
    "Parsing errors prevented compilation from completing."
)

MSG_EXEC_SEMANTIC_ERROR = (
    "No assembly code to execute due to semantic errors.\n\n"
    "Execution requires a successfully compiled program.\n"
    "Semantic errors prevented compilation from completing."
)


# ── Line-number gutter ─────────────────────────────────────────────────────────
class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """QPlainTextEdit with a line-number gutter on the left."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_area_width(0)
        self._highlight_current_line()

        font = QFont("JetBrains Mono")
        if not font.exactMatch():
            font = QFont("Consolas")
        font.setPointSize(12)
        self.setFont(font)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setPlaceholderText(
            "// Paste or type your C source code here…\n"
            "// Press F5 or Ctrl+R to run lexical analysis.\n"
            "// Press F6 or Ctrl+Shift+R to run the full compiler pipeline."
        )

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def _highlight_current_line(self):
        extra = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor("#1e3a5f"))
            sel.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#161b22"))

        block     = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top       = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom    = top + round(self.blockBoundingRect(block).height())

        font = QFont("Consolas", self.font().pointSize() - 1)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#4a5568"))
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    str(block_num + 1),
                )
            block     = block.next()
            top       = bottom
            bottom    = top + round(self.blockBoundingRect(block).height())
            block_num += 1


# ── x86 Assembly syntax highlighter ───────────────────────────────────────────
class AsmHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)

        def fmt(color: str, bold: bool = False) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            return f

        self._rules = [
            (r"\.\w+",                          fmt("#82aaff", bold=True)),
            (r"^\s*[A-Za-z_]\w*\s*:",           fmt("#ffcb6b", bold=True)),
            (r"\b(mov|add|sub|mul|div|imul|idiv|inc|dec|push|pop"
             r"|jmp|je|jne|jl|jle|jg|jge|cmp|test|call|ret"
             r"|and|or|xor|not|neg|lea|nop)\b", fmt("#c3e88d")),
            (r"\b(eax|ebx|ecx|edx|esi|edi|esp|ebp"
             r"|rax|rbx|rcx|rdx|rsi|rdi|rsp|rbp"
             r"|ax|bx|cx|dx|al|bl|cl|dl)\b",    fmt("#f07178")),
            (r"\b0x[0-9A-Fa-f]+\b|\b\d+\b",    fmt("#c792ea")),
            (r"#[^\n]*",                         fmt("#4a5568")),
        ]
        import re
        self._compiled = [(re.compile(p), f) for p, f in self._rules]

    def highlightBlock(self, text: str):
        for regex, fmt in self._compiled:
            for m in regex.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ── Metric card ────────────────────────────────────────────────────────────────
class MetricCard(QFrame):
    def __init__(self, label: str, value: str = "—", color: str = "#80cbc4", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("MetricCard")
        self.setStyleSheet("""
            #MetricCard {
                background: #1a2332;
                border: 1px solid #2d4a6e;
                border-radius: 10px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self._value_label = QLabel(value)
        self._value_label.setStyleSheet(
            f"color: {color}; font-size: 28px; font-weight: 700; font-family: 'Consolas';"
        )
        self._value_label.setAlignment(Qt.AlignCenter)

        self._title_label = QLabel(label)
        self._title_label.setStyleSheet(
            "color: #8892a4; font-size: 11px; font-weight: 600; letter-spacing: 1px;"
        )
        self._title_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self._value_label)
        layout.addWidget(self._title_label)

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_color(self, color: str):
        self._value_label.setStyleSheet(
            f"color: {color}; font-size: 28px; font-weight: 700; font-family: 'Consolas';"
        )


# ── Stage badge widget (pipeline progress bar) ────────────────────────────────
class PipelineBadge(QLabel):
    def __init__(self, code: str, label: str, color: str, parent=None):
        super().__init__(parent)
        self._code  = code
        self._color = color
        self._label = label
        self._state = "idle"
        self.set_state("idle")

    def set_state(self, state: str):
        """idle | running | ok | error"""
        self._state = state
        if state == "running":
            bg, fg, border = "#1e3a5f", "#89ddff", "#2d5486"
        elif state == "ok":
            bg, fg, border = "#1a3a2a", "#c3e88d", "#2d6a54"
        elif state == "error":
            bg, fg, border = "#3a1a1a", "#f07178", "#6a2d2d"
        else:  # idle
            bg, fg, border = "#161b22", "#4a5568", "#21262d"

        self.setStyleSheet(
            f"QLabel {{ background: {bg}; color: {fg}; "
            f"border: 1px solid {border}; border-radius: 6px; "
            f"padding: 3px 10px; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 1px; }}"
        )
        self.setText(self._code)
        self.setToolTip(self._label)

    def get_state(self) -> str:
        return self._state


# ══════════════════════════════════════════════════════════════════════════════
# Full compiler pipeline worker
# ══════════════════════════════════════════════════════════════════════════════
class CompilerWorker(QThread):
    """
    Runs all stages and emits per-stage results.

    Signals
    -------
    stage_done(stage_id, data)
    pipeline_error(stage_id, message)

    Pipeline cases:
      Case 1: Parsing OK + SDT OK  → full pipeline
      Case 2: Parsing Error        → remaining stages get error payloads
      Case 3: Parsing OK + SDT Err → AST/TAC/ASM/EXEC get error payloads
    """
    stage_done     = Signal(str, object)
    pipeline_error = Signal(str, str)

    def __init__(self, lines: list[str], resource_dir: str, output_dir: str):
        super().__init__()
        self._lines        = lines
        self._resource_dir = resource_dir
        self._output_dir   = output_dir

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _ast_to_text(node, indent: int = 0) -> str:
        if node is None:
            return ""
        prefix = "  " * indent
        type_info  = f" <{node.inferred_type}>" if node.inferred_type else ""
        value_info = f" : {node.value}"          if node.value is not None else ""
        result = f"{prefix}[{node.node_type}]{value_info}{type_info}\n"
        for child in node.children:
            if hasattr(child, "children"):
                result += CompilerWorker._ast_to_text(child, indent + 1)
        return result

    @staticmethod
    def _ast_to_tree_items(node) -> QTreeWidgetItem | None:
        if node is None:
            return None

        type_info  = f" <{node.inferred_type}>" if node.inferred_type else ""
        value_info = f" : {node.value}"          if node.value is not None else ""
        label = f"[{node.node_type}]{value_info}{type_info}"

        item = QTreeWidgetItem([label])

        if node.node_type in ("CONST", "constant"):
            item.setForeground(0, QColor("#f07178"))
        elif node.node_type in ("LITERAL", "literal"):
            item.setForeground(0, QColor("#c792ea"))
        elif node.node_type == "id":
            item.setForeground(0, QColor("#c3e88d"))
        elif node.node_type in ("BIN_OP", "UNARY"):
            item.setForeground(0, QColor("#f78c6c"))
        elif node.node_type == "FUNCTION":
            item.setForeground(0, QColor("#82aaff"))
        elif node.node_type in ("TYPE", "int", "float", "double", "char", "void"):
            item.setForeground(0, QColor("#82aaff"))
        elif node.node_type in ("return", "if", "else", "while", "for", "do"):
            item.setForeground(0, QColor("#ffcb6b"))
        else:
            item.setForeground(0, QColor("#8892a4"))

        for child in node.children:
            if hasattr(child, "children"):
                child_item = CompilerWorker._ast_to_tree_items(child)
                if child_item:
                    item.addChild(child_item)

        return item

    def _try_render_ast_image(self, ast) -> str | None:
        """
        Try to render the AST to a PNG using graphviz.
        Returns the output path on success, None on failure.
        """
        try:
            from Ast.ast_visualizer import ASTVisualizer
            out_path = str(Path(self._output_dir) / "ast")
            viz = ASTVisualizer()
            result = viz.render(ast, filename=out_path, format="png", view=False)
            # graphviz appends .png automatically
            if not result.endswith(".png"):
                result = result + ".png"
            if Path(result).exists():
                return result
        except Exception:
            pass
        return None

    # ── main run ──────────────────────────────────────────────────────────────
    def run(self):
        try:
            # ── LEX ──────────────────────────────────────────────────────────
            from Lexer.lexer import Lexer
            lexer  = Lexer(self._lines, self._resource_dir)
            tokens = lexer.tokenize()
            self.stage_done.emit("LEX", tokens)

            # ── PAR (build parsing table + report) ───────────────────────────
            from Parser.grammar import Grammar
            from Parser.first_follow import compute_first, compute_follow
            from Parser.Parsing_table import LL1Table
            from Parser.Parser import Parser

            g       = Grammar()
            firsts  = compute_first(g.productions, g.non_terminals)
            follows = compute_follow(g.productions, g.non_terminals, firsts, g.start_symbol)
            tabla   = LL1Table(g, firsts, follows)

            par_lines = ["LL(1) Parsing Table — non-terminal entries:\n"]
            for nt in sorted(tabla.table.keys()):
                entries = tabla.table[nt]
                if entries:
                    par_lines.append(f"  {nt}:")
                    for terminal, rules in entries.items():
                        for rule in rules:
                            par_lines.append(f"    [{terminal}]  →  {rule}")
            if tabla.conflicts:
                par_lines.append("\n⚠ Conflicts detected:")
                for c in tabla.conflicts:
                    par_lines.append(f"  {c}")
            else:
                par_lines.append("\n✓ Grammar is deterministic LL(1). No conflicts.")

            self.stage_done.emit("PAR", "\n".join(par_lines))

            # ── PARSE (build AST) ─────────────────────────────────────────────
            parser = Parser(tabla.table, g.start_symbol)

            try:
                ast = parser.parse(tokens)
            except SyntaxError as exc:
                # ── CASE 2: Parsing Error ─────────────────────────────────────
                self.pipeline_error.emit("Parsing", str(exc))
                # Emit TREE with the error
                self.stage_done.emit("TREE", ("error", f"Parse Tree was not built.\n\nReason:\n{exc}", None))
                # Emit AST/TAC/ASM/EXEC with error payloads
                self.stage_done.emit("SEM",  ("error", f"Semantic analysis skipped.\n\nReason: Parsing failed.\n{exc}"))
                self.stage_done.emit("AST",  ("error", MSG_AST_PARSE_ERROR, None))
                self.stage_done.emit("TAC",  ("error", MSG_TAC_PARSE_ERROR))
                self.stage_done.emit("ASM",  ("error", MSG_ASM_PARSE_ERROR))
                self.stage_done.emit("EXEC", ("error", MSG_EXEC_PARSE_ERROR))
                return

            # Parse succeeded → build parse tree text
            tree_text = self._ast_to_text(ast)
            self.stage_done.emit("TREE", ("text", tree_text, ast))

            # ── SEM ───────────────────────────────────────────────────────────
            from Semantic.semantic_analyzer import SemanticAnalyzer
            semantic   = SemanticAnalyzer()
            sem_errors = semantic.analyze(ast)

            sym_table = semantic.table.get_all_symbols()
            sem_lines = ["─── Symbol Table ───\n"]
            if sym_table:
                sem_lines.append(f"  {'Name':<20} {'Type':<10} {'Init':<8} {'Category'}")
                sem_lines.append("  " + "─" * 52)
                for name, sym in sym_table.items():
                    cat  = "FUNC" if sym.is_func else "VAR"
                    init = "✓" if sym.initialized else "✗"
                    sem_lines.append(f"  {name:<20} {sym.type:<10} {init:<8} {cat}")
            else:
                sem_lines.append("  (no symbols declared)")

            if sem_errors:
                # ── CASE 3: Parsing OK, SDT Error ────────────────────────────
                sem_lines.append("\n─── Semantic Errors ───\n")
                for e in sem_errors:
                    sem_lines.append(f"  ✕ {e}")
                self.stage_done.emit("SEM", ("error", "\n".join(sem_lines)))
                self.pipeline_error.emit("Semantic", "\n".join(sem_errors))
                # AST, TAC, ASM, EXEC get error messages
                self.stage_done.emit("AST",  ("error", MSG_AST_SEMANTIC_ERROR, None))
                self.stage_done.emit("TAC",  ("error", MSG_TAC_SEMANTIC_ERROR))
                self.stage_done.emit("ASM",  ("error", MSG_ASM_SEMANTIC_ERROR))
                self.stage_done.emit("EXEC", ("error", MSG_EXEC_SEMANTIC_ERROR))
                return

            # SDT OK
            sem_lines.append("\n✓ Semantic analysis passed. No errors found.")
            self.stage_done.emit("SEM", ("ok", "\n".join(sem_lines)))

            # ── AST ───────────────────────────────────────────────────────────
            # Try to render graphviz image; pass ast node + image path
            img_path = self._try_render_ast_image(ast)
            self.stage_done.emit("AST", ("ok", ast, img_path))

            # ── TAC ───────────────────────────────────────────────────────────
            from Tac.TAC import TACGenerator
            tac_gen   = TACGenerator()
            tac_instr = tac_gen.generate(ast)
            self.stage_done.emit("TAC", ("ok", tac_instr))

            # ── ASM ───────────────────────────────────────────────────────────
            from Assembly.Assembly import AssemblerGenerator
            asm_gen = AssemblerGenerator()
            asm_str = asm_gen.generate(tac_instr)
            if isinstance(asm_str, list):
                asm_str = "\n".join(asm_str)
            self.stage_done.emit("ASM", ("ok", asm_str if asm_str.strip() else "(No ASM generated)"))

            # ── EXEC ──────────────────────────────────────────────────────────
            exec_lines = [
                "─── Execution Simulation ───\n",
                "Execution Success!",
                "",
                "Program finished correctly.",
                "",
                "Program Output:",
                "(no output)",
                "",
                "─── Compilation Statistics ───\n",
                f"  TAC instructions : {len(tac_instr)}",
                f"  ASM lines        : {len(asm_str.splitlines())}",
                f"  Tokens processed : {len(tokens)}",
                "\n✓ Compilation pipeline completed successfully.",
                "\nTo execute the program, assemble and link the output:",
                "  $ as -o program.o output.s",
                "  $ ld -o program program.o",
                "  $ ./program",
            ]
            self.stage_done.emit("EXEC", ("ok", "\n".join(exec_lines)))

        except Exception as exc:
            import traceback
            self.pipeline_error.emit("Critical", traceback.format_exc())


# ── Lexer-only worker ─────────────────────────────────────────────────────────
class LexerWorker(QThread):
    finished = Signal(list)
    error    = Signal(str)

    def __init__(self, lines: list[str], resource_dir: str):
        super().__init__()
        self._lines        = lines
        self._resource_dir = resource_dir

    def run(self):
        try:
            from Lexer.lexer import Lexer
            lexer  = Lexer(self._lines, self._resource_dir)
            tokens = lexer.tokenize()
            self.finished.emit(tokens)
        except Exception as exc:
            self.error.emit(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Main Window
# ══════════════════════════════════════════════════════════════════════════════
class LexicalAnalyzerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("C-Pure Compiler IDE — Team 7")
        self.setMinimumSize(1380, 820)
        self.resize(1600, 960)

        self._tokens:          list[dict]       = []
        self._worker:          LexerWorker    | None = None
        self._compiler_worker: CompilerWorker  | None = None
        self._last_ast_img:    str | None      = None   # path to last rendered AST PNG

        self._build_ui()
        self._connect_shortcuts()
        self._set_status("Ready", "idle")

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_center(), stretch=1)
        root.addLayout(body, stretch=1)

        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(
            "QStatusBar { background: #0d1117; border-top: 1px solid #21262d; "
            "color: #8892a4; font-size: 12px; padding: 2px 12px; }"
        )
        self.setStatusBar(self._status_bar)

        self._status_label      = QLabel("● Ready")
        self._token_count_label = QLabel("Tokens: 0")
        self._error_count_label = QLabel("Errors: 0")
        self._line_count_label  = QLabel("Lines: 0")
        for lbl in (self._status_label, self._token_count_label,
                    self._error_count_label, self._line_count_label):
            lbl.setStyleSheet("color: #8892a4; padding: 0 12px;")
            self._status_bar.addPermanentWidget(lbl)

    # ── Header ─────────────────────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(58)
        header.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #0d1117, stop:0.5 #111827, stop:1 #0d1117);"
            "border-bottom: 1px solid #21262d;"
        )
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        for text, style in [
            ("⟨/⟩", "color:#80cbc4;font-size:22px;font-weight:700;margin-right:10px;"),
            ("C-Pure Compiler IDE", "color:#e6edf3;font-size:20px;font-weight:700;letter-spacing:0.5px;"),
            ("·", "color:#4a5568;font-size:20px;margin:0 8px;"),
            ("Full Pipeline  ·  Team 7", "color:#6b7280;font-size:13px;"),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(style)
            layout.addWidget(lbl)

        layout.addStretch()

        self._badges: dict[str, PipelineBadge] = {}
        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        for code, label, color in STAGES:
            b = PipelineBadge(code, label, color)
            self._badges[code] = b
            badge_row.addWidget(b)
        layout.addLayout(badge_row)

        layout.addSpacing(16)
        tag = QLabel("v2.1")
        tag.setStyleSheet(
            "color: #80cbc4; background: #1e3a46; border: 1px solid #2d6a54;"
            "border-radius: 10px; padding: 2px 10px; font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(tag)
        return header

    # ── Sidebar ────────────────────────────────────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background: #0d1117; border-right: 1px solid #21262d;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        def section(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: #4a5568; font-size: 10px; font-weight: 700; "
                "letter-spacing: 2px; margin-bottom: 4px;"
            )
            return lbl

        def make_btn(text, icon, primary=False, blue=False, danger=False, teal=False):
            btn = QPushButton(f"  {icon}  {text}")
            btn.setCursor(Qt.PointingHandCursor)
            if primary:
                s = ("QPushButton{background:#00897b;color:#fff;border:none;"
                     "border-radius:8px;padding:10px 8px;font-size:13px;"
                     "font-weight:600;text-align:left;}"
                     "QPushButton:hover{background:#00acc1;}"
                     "QPushButton:pressed{background:#007c6d;}"
                     "QPushButton:disabled{background:#1a3a36;color:#2d6a54;}")
            elif blue:
                s = ("QPushButton{background:#1a2b4a;color:#89ddff;"
                     "border:1px solid #2d5486;border-radius:8px;"
                     "padding:10px 8px;font-size:13px;font-weight:600;text-align:left;}"
                     "QPushButton:hover{background:#1e3a5f;color:#e6edf3;}"
                     "QPushButton:pressed{background:#0f2340;}"
                     "QPushButton:disabled{color:#30363d;border-color:#21262d;}")
            elif teal:
                s = ("QPushButton{background:#1a3a36;color:#80cbc4;"
                     "border:1px solid #2d6a54;border-radius:8px;"
                     "padding:10px 8px;font-size:13px;text-align:left;}"
                     "QPushButton:hover{background:#1e4a44;color:#e6edf3;}"
                     "QPushButton:pressed{background:#0f2d28;}"
                     "QPushButton:disabled{color:#30363d;border-color:#21262d;}")
            elif danger:
                s = ("QPushButton{background:#1a2332;color:#f07178;"
                     "border:1px solid #f07178;border-radius:8px;"
                     "padding:10px 8px;font-size:13px;text-align:left;}"
                     "QPushButton:hover{background:#2d1a1e;}"
                     "QPushButton:pressed{background:#1a0e10;}")
            else:
                s = ("QPushButton{background:#161b22;color:#c9d1d9;"
                     "border:1px solid #30363d;border-radius:8px;"
                     "padding:10px 8px;font-size:13px;text-align:left;}"
                     "QPushButton:hover{background:#21262d;color:#e6edf3;}"
                     "QPushButton:pressed{background:#30363d;}")
            btn.setStyleSheet(s)
            return btn

        def hint(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #4a5568; font-size: 10px; margin-left: 8px;")
            return lbl

        layout.addWidget(section("ACTIONS"))

        self._btn_analyze    = make_btn("Analyze",     "▶", primary=True)
        self._btn_compile    = make_btn("Full Compile", "⚙", blue=True)
        self._btn_open       = make_btn("Open File",   "📂")
        self._btn_save       = make_btn("Save Input",  "💾")
        self._btn_export     = make_btn("Export Tokens","📤")
        self._btn_save_ast   = make_btn("Save AST",    "🖼", teal=True)
        self._btn_clear      = make_btn("Clear All",   "✕", danger=True)

        self._btn_analyze.clicked.connect(self._on_analyze)
        self._btn_compile.clicked.connect(self._on_compile)
        self._btn_open.clicked.connect(self._on_open)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_export.clicked.connect(self._on_export)
        self._btn_save_ast.clicked.connect(self._on_save_ast)
        self._btn_clear.clicked.connect(self._on_clear)
        self._btn_save_ast.setEnabled(False)

        for widget in [
            self._btn_analyze,   hint("F5  /  Ctrl+R"),
            self._btn_compile,   hint("F6  /  Ctrl+Shift+R"),
            self._btn_open,      hint("Ctrl+O"),
            self._btn_save,      hint("Ctrl+S"),
            self._btn_export,
            self._btn_save_ast,  hint("Saves to output/"),
            self._btn_clear,     hint("Ctrl+L"),
        ]:
            layout.addWidget(widget)

        layout.addStretch()

        layout.addWidget(section("TOKEN TYPES"))
        for cat, color in TOKEN_COLORS.items():
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            lbl = QLabel(cat)
            lbl.setStyleSheet("color: #8892a4; font-size: 11px;")
            row.addWidget(dot)
            row.addWidget(lbl)
            row.addStretch()
            layout.addLayout(row)

        return sidebar

    # ── Center (editor + output tabs) ─────────────────────────────────────────
    def _build_center(self) -> QWidget:
        center = QWidget()
        center.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(center)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle{background:#21262d;height:3px;}")

        # ── Editor ────────────────────────────────────────────────────────────
        editor_container = QWidget()
        editor_container.setStyleSheet("background: #0d1117;")
        ec_layout = QVBoxLayout(editor_container)
        ec_layout.setContentsMargins(0, 0, 0, 0)
        ec_layout.setSpacing(0)

        editor_hdr = QWidget()
        editor_hdr.setFixedHeight(36)
        editor_hdr.setStyleSheet("background:#161b22;border-bottom:1px solid #21262d;")
        eh_l = QHBoxLayout(editor_hdr)
        eh_l.setContentsMargins(16, 0, 16, 0)
        src_lbl = QLabel("SOURCE CODE")
        src_lbl.setStyleSheet(
            "color:#4a5568;font-size:10px;font-weight:700;letter-spacing:2px;"
        )
        eh_l.addWidget(src_lbl)
        eh_l.addStretch()
        self._cursor_pos_label = QLabel("Ln 1, Col 1")
        self._cursor_pos_label.setStyleSheet("color:#4a5568;font-size:11px;")
        eh_l.addWidget(self._cursor_pos_label)
        ec_layout.addWidget(editor_hdr)

        self._editor = CodeEditor()
        self._editor.setStyleSheet(
            "QPlainTextEdit{background:#0d1117;color:#e6edf3;border:none;"
            "selection-background-color:#264f78;}"
        )
        self._editor.cursorPositionChanged.connect(self._update_cursor_pos)
        ec_layout.addWidget(self._editor)
        splitter.addWidget(editor_container)

        # ── Output tabs ───────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(self._tab_style())

        self._stage_tab_idx: dict[str, int] = {}

        self._tabs.addTab(self._build_tokens_tab(),  "  ▦  Tokens  ")
        self._tabs.addTab(self._build_errors_tab(),  "  ✕  Errors  ")
        self._tabs.addTab(self._build_summary_tab(), "  ◈  Summary ")

        for code, label, color in STAGES:
            tab_widget = self._build_stage_tab(code, label, color)
            idx = self._tabs.count()
            self._stage_tab_idx[code] = idx
            self._tabs.addTab(tab_widget, f"  {label}  ")

        splitter.addWidget(self._tabs)
        splitter.setSizes([400, 380])
        layout.addWidget(splitter)
        return center

    def _tab_style(self) -> str:
        return (
            "QTabWidget::pane{border:none;background:#0d1117;}"
            "QTabBar::tab{background:#161b22;color:#8892a4;padding:7px 16px;"
            "font-size:11px;font-weight:600;border:none;"
            "border-bottom:2px solid transparent;}"
            "QTabBar::tab:selected{color:#80cbc4;border-bottom:2px solid #80cbc4;"
            "background:#0d1117;}"
            "QTabBar::tab:hover:!selected{background:#1c2230;color:#c9d1d9;}"
        )

    # ── Tokens tab ────────────────────────────────────────────────────────────
    def _build_tokens_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:#0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        self._token_table = QTableWidget(0, 4)
        self._token_table.setHorizontalHeaderLabels(["Lexeme", "Type", "Line", "Column"])
        self._token_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1, 2, 3):
            self._token_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeToContents
            )
        self._token_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._token_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._token_table.setAlternatingRowColors(True)
        self._token_table.verticalHeader().setVisible(False)
        self._token_table.setShowGrid(False)
        self._token_table.setStyleSheet(self._table_style())
        layout.addWidget(self._token_table)
        return w

    def _table_style(self) -> str:
        return (
            "QTableWidget{background:#0d1117;alternate-background-color:#111827;"
            "color:#e6edf3;border:none;gridline-color:#21262d;font-size:13px;}"
            "QTableWidget::item:selected{background:#1e3a5f;}"
            "QHeaderView::section{background:#161b22;color:#8892a4;font-size:11px;"
            "font-weight:700;letter-spacing:1px;padding:8px 12px;border:none;"
            "border-bottom:1px solid #21262d;}"
            "QScrollBar:vertical{background:#161b22;width:8px;border:none;}"
            "QScrollBar::handle:vertical{background:#30363d;border-radius:4px;min-height:20px;}"
        )

    # ── Errors tab ────────────────────────────────────────────────────────────
    def _build_errors_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:#0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        self._errors_text = QTextEdit()
        self._errors_text.setReadOnly(True)
        self._errors_text.setStyleSheet(self._readonly_textedit_style())
        self._errors_text.setPlaceholderText("No errors detected.")
        layout.addWidget(self._errors_text)
        return w

    # ── Summary tab ───────────────────────────────────────────────────────────
    def _build_summary_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#0d1117;}")

        w = QWidget()
        w.setStyleSheet("background:#0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._card_total  = MetricCard("TOTAL TOKENS",   "—", "#80cbc4")
        self._card_errors = MetricCard("LEXICAL ERRORS", "—", "#f07178")
        self._card_lines  = MetricCard("LINES ANALYZED", "—", "#c3e88d")
        self._card_status = MetricCard("STATUS",         "—", "#ffcb6b")
        for card in (self._card_total, self._card_errors, self._card_lines, self._card_status):
            cards_row.addWidget(card)
        layout.addLayout(cards_row)

        breakdown_label = QLabel("TOKEN DISTRIBUTION")
        breakdown_label.setStyleSheet(
            "color:#4a5568;font-size:10px;font-weight:700;letter-spacing:2px;margin-top:8px;"
        )
        layout.addWidget(breakdown_label)

        self._breakdown_table = QTableWidget(0, 3)
        self._breakdown_table.setHorizontalHeaderLabels(["Category", "Count", "Unique"])
        self._breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._breakdown_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._breakdown_table.setAlternatingRowColors(True)
        self._breakdown_table.verticalHeader().setVisible(False)
        self._breakdown_table.setShowGrid(False)
        self._breakdown_table.setMaximumHeight(260)
        self._breakdown_table.setStyleSheet(
            "QTableWidget{background:#111827;alternate-background-color:#161b22;"
            "color:#e6edf3;border:1px solid #21262d;border-radius:8px;font-size:13px;}"
            "QTableWidget::item:selected{background:#1e3a5f;}"
            "QHeaderView::section{background:#161b22;color:#8892a4;font-size:11px;"
            "font-weight:700;letter-spacing:1px;padding:8px 12px;border:none;"
            "border-bottom:1px solid #21262d;}"
        )
        layout.addWidget(self._breakdown_table)
        layout.addStretch()
        scroll.setWidget(w)
        return scroll

    # ── Generic pipeline stage tab ────────────────────────────────────────────
    def _build_stage_tab(self, code: str, label: str, color: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:#0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Mini header
        hdr = QWidget()
        hdr.setFixedHeight(36)
        hdr.setStyleSheet("background:#161b22;border-bottom:1px solid #21262d;")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(16, 0, 16, 0)
        hdr_lbl = QLabel(label.upper())
        hdr_lbl.setStyleSheet(
            f"color:{color};font-size:10px;font-weight:700;letter-spacing:2px;"
        )
        hdr_l.addWidget(hdr_lbl)
        hdr_l.addStretch()

        if code == "AST":
            # Download button in AST header
            self._ast_download_btn = QPushButton("⬇ Download AST")
            self._ast_download_btn.setCursor(Qt.PointingHandCursor)
            self._ast_download_btn.setEnabled(False)
            self._ast_download_btn.setStyleSheet(
                "QPushButton{background:#1a3a36;color:#80cbc4;"
                "border:1px solid #2d6a54;border-radius:5px;"
                "font-size:11px;padding:3px 12px;}"
                "QPushButton:hover{background:#1e4a44;color:#e6edf3;}"
                "QPushButton:disabled{color:#30363d;border-color:#21262d;background:#111;}"
            )
            self._ast_download_btn.clicked.connect(self._on_save_ast)
            hdr_l.addWidget(self._ast_download_btn)
            hdr_l.addSpacing(8)

        # Copy button
        copy_btn = QPushButton("⎘ Copy")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#4a5568;border:none;"
            "font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#e6edf3;}"
        )
        hdr_l.addWidget(copy_btn)
        layout.addWidget(hdr)

        # ── AST tab: stacked layout (tree widget + image viewer) ──────────────
        if code == "AST":
            # We use a stacked approach: tree + error label share a container
            ast_container = QWidget()
            ast_container.setStyleSheet("background:#0d1117;")
            ast_layout = QVBoxLayout(ast_container)
            ast_layout.setContentsMargins(0, 0, 0, 0)
            ast_layout.setSpacing(0)

            # Interactive tree widget
            self._ast_tree = QTreeWidget()
            self._ast_tree.setHeaderHidden(True)
            self._ast_tree.setStyleSheet(
                "QTreeWidget{background:#0d1117;color:#e6edf3;border:none;"
                "font-family:Consolas,monospace;font-size:12px;}"
                "QTreeWidget::item:selected{background:#1e3a5f;}"
                "QTreeWidget::item:hover{background:#111827;}"
                "QTreeWidget::branch{background:#0d1117;}"
            )
            ast_layout.addWidget(self._ast_tree)

            # Scrollable image area (graphviz PNG)
            self._ast_img_scroll = QScrollArea()
            self._ast_img_scroll.setWidgetResizable(True)
            self._ast_img_scroll.setStyleSheet(
                "QScrollArea{border:none;background:#0d1117;}"
            )
            self._ast_img_label = QLabel()
            self._ast_img_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self._ast_img_label.setStyleSheet("background:#0d1117;padding:12px;")
            self._ast_img_scroll.setWidget(self._ast_img_label)
            self._ast_img_scroll.setVisible(False)
            ast_layout.addWidget(self._ast_img_scroll)

            # Error / info label
            self._ast_msg_label = QLabel()
            self._ast_msg_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self._ast_msg_label.setWordWrap(True)
            self._ast_msg_label.setStyleSheet(
                "QLabel{color:#f07178;font-family:Consolas,monospace;"
                "font-size:13px;padding:24px;background:#0d1117;}"
            )
            self._ast_msg_label.setVisible(False)
            ast_layout.addWidget(self._ast_msg_label)

            layout.addWidget(ast_container)

            copy_btn.clicked.connect(self._copy_ast_tree)
            return w

        # ── TREE tab ──────────────────────────────────────────────────────────
        if code == "TREE":
            tree = QTreeWidget()
            tree.setHeaderHidden(True)
            tree.setStyleSheet(
                "QTreeWidget{background:#0d1117;color:#e6edf3;border:none;"
                "font-family:Consolas,monospace;font-size:12px;}"
                "QTreeWidget::item:selected{background:#1e3a5f;}"
                "QTreeWidget::item:hover{background:#111827;}"
                "QTreeWidget::branch{background:#0d1117;}"
            )
            setattr(self, "_stage_tree_TREE", tree)
            layout.addWidget(tree)
            copy_btn.clicked.connect(lambda checked=False, t=tree: self._copy_tree(t))
            return w

        # ── All other stages: plain text ──────────────────────────────────────
        pte = QPlainTextEdit()
        pte.setReadOnly(True)
        pte.setPlaceholderText(f"Run ⚙ Full Compile to generate {label}…")
        font = QFont("Consolas")
        font.setPointSize(12)
        pte.setFont(font)
        pte.setStyleSheet(
            f"QPlainTextEdit{{background:#0d1117;color:{color};"
            "border:none;selection-background-color:#264f78;}"
        )
        if code == "ASM":
            setattr(self, "_asm_highlighter", AsmHighlighter(pte.document()))
        setattr(self, f"_stage_pte_{code}", pte)
        layout.addWidget(pte)
        copy_btn.clicked.connect(
            lambda checked=False, p=pte: QApplication.clipboard().setText(p.toPlainText())
        )
        return w

    # ── AST helpers ───────────────────────────────────────────────────────────
    def _copy_ast_tree(self):
        lines = []
        def recurse(item, depth=0):
            lines.append("  " * depth + item.text(0))
            for i in range(item.childCount()):
                recurse(item.child(i), depth + 1)
        for i in range(self._ast_tree.topLevelItemCount()):
            recurse(self._ast_tree.topLevelItem(i))
        QApplication.clipboard().setText("\n".join(lines))

    def _show_ast_tree(self, ast_node):
        """Show the interactive tree and optionally the graphviz image."""
        self._ast_msg_label.setVisible(False)
        self._ast_tree.setVisible(True)
        self._ast_tree.clear()
        root_item = CompilerWorker._ast_to_tree_items(ast_node)
        if root_item:
            self._ast_tree.addTopLevelItem(root_item)
            self._ast_tree.expandToDepth(3)

    def _show_ast_image(self, img_path: str | None):
        """Show the graphviz-rendered AST image below the tree."""
        if img_path and Path(img_path).exists():
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                self._ast_img_label.setPixmap(pixmap)
                self._ast_img_scroll.setVisible(True)
                return
        self._ast_img_scroll.setVisible(False)

    def _show_ast_error(self, message: str):
        """Show an error message in the AST tab (no tree)."""
        self._ast_tree.clear()
        self._ast_tree.setVisible(False)
        self._ast_img_scroll.setVisible(False)
        self._ast_msg_label.setText(message)
        self._ast_msg_label.setVisible(True)

    def _copy_tree(self, tree: QTreeWidget):
        lines = []
        def recurse(item, depth=0):
            lines.append("  " * depth + item.text(0))
            for i in range(item.childCount()):
                recurse(item.child(i), depth + 1)
        for i in range(tree.topLevelItemCount()):
            recurse(tree.topLevelItem(i))
        QApplication.clipboard().setText("\n".join(lines))

    # ── Style helpers ─────────────────────────────────────────────────────────
    def _readonly_textedit_style(self) -> str:
        return (
            "QTextEdit{background:#0d1117;color:#e6edf3;border:none;"
            "font-family:Consolas,'JetBrains Mono',monospace;font-size:13px;}"
        )

    # ── Shortcuts ─────────────────────────────────────────────────────────────
    def _connect_shortcuts(self):
        QShortcut(QKeySequence("F5"),           self).activated.connect(self._on_analyze)
        QShortcut(QKeySequence("Ctrl+R"),       self).activated.connect(self._on_analyze)
        QShortcut(QKeySequence("F6"),           self).activated.connect(self._on_compile)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self).activated.connect(self._on_compile)
        QShortcut(QKeySequence("Ctrl+O"),       self).activated.connect(self._on_open)
        QShortcut(QKeySequence("Ctrl+S"),       self).activated.connect(self._on_save)
        QShortcut(QKeySequence("Ctrl+L"),       self).activated.connect(self._on_clear)

    # ── Status helpers ────────────────────────────────────────────────────────
    def _set_status(self, text: str, state: str = "idle"):
        colors = {"idle": "#8892a4", "running": "#ffcb6b",
                  "success": "#c3e88d", "error": "#f07178"}
        color = colors.get(state, "#8892a4")
        self._status_label.setText(f"● {text}")
        self._status_label.setStyleSheet(
            f"color:{color};padding:0 12px;font-weight:600;"
        )

    def _reset_badges(self):
        for b in self._badges.values():
            b.set_state("idle")

    def _update_status_bar_counts(self, tokens: list[dict]):
        errors = [t for t in tokens if t["type"] == "Unknown"]
        lines  = set(t["line"] for t in tokens)
        self._token_count_label.setText(f"Tokens: {len(tokens)}")
        self._error_count_label.setText(f"Errors: {len(errors)}")
        self._line_count_label.setText(f"Lines: {len(lines)}")

    def _update_cursor_pos(self):
        cursor = self._editor.textCursor()
        self._cursor_pos_label.setText(
            f"Ln {cursor.blockNumber()+1}, Col {cursor.columnNumber()+1}"
        )

    # ── Analyze (Lexer only) ──────────────────────────────────────────────────
    def _on_analyze(self):
        source = self._editor.toPlainText().strip()
        if not source:
            QMessageBox.warning(self, "No Input", "Please enter source code first.")
            return

        self._reset_badges()
        self._badges["LEX"].set_state("running")
        self._set_status("Running lexical analysis…", "running")
        self._btn_analyze.setEnabled(False)
        self._btn_compile.setEnabled(False)
        QApplication.processEvents()

        lines = source.splitlines()
        self._worker = LexerWorker(lines, str(RES_DIR))
        self._worker.finished.connect(self._on_lex_done)
        self._worker.error.connect(self._on_lex_error)
        self._worker.start()

    @Slot(list)
    def _on_lex_done(self, tokens: list[dict]):
        self._tokens = tokens
        self._btn_analyze.setEnabled(True)
        self._btn_compile.setEnabled(True)
        errors = [t for t in tokens if t["type"] == "Unknown"]

        self._populate_token_table(tokens)
        self._populate_errors_tab(errors)
        self._populate_summary_tab(tokens)
        self._update_status_bar_counts(tokens)
        self._populate_stage_pte("LEX", self._build_lex_report(tokens))
        self._badges["LEX"].set_state("error" if errors else "ok")

        if errors:
            self._set_status(f"Lexer — {len(errors)} error(s)", "error")
            self._tabs.setCurrentIndex(1)
        else:
            self._set_status("Lexer — OK", "success")
            self._tabs.setCurrentIndex(self._stage_tab_idx["LEX"])

    @Slot(str)
    def _on_lex_error(self, message: str):
        self._btn_analyze.setEnabled(True)
        self._btn_compile.setEnabled(True)
        self._badges["LEX"].set_state("error")
        self._set_status("Lexer failed", "error")
        QMessageBox.critical(self, "Lexer Error", message)

    def _build_lex_report(self, tokens: list[dict]) -> str:
        from collections import Counter
        by_type = Counter(t["type"] for t in tokens)
        lines = [
            "─── Lexer Output Report ───\n",
            f"  Total tokens   : {len(tokens)}",
            f"  Lexical errors : {sum(1 for t in tokens if t['type'] == 'Unknown')}",
            f"  Lines scanned  : {len(set(t['line'] for t in tokens))}",
            "\n─── Token Distribution ───\n",
        ]
        for cat, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  {cat:<15} {count:>5} token(s)")
        lines.append("\n─── First 50 Tokens ───\n")
        for t in tokens[:50]:
            lines.append(
                f"  [{t['line']:>4}:{t['column']:<3}]  "
                f"{t['type']:<14}  {t['value']}"
            )
        if len(tokens) > 50:
            lines.append(f"  … ({len(tokens)-50} more tokens)")
        return "\n".join(lines)

    # ── Full Compile ──────────────────────────────────────────────────────────
    def _on_compile(self):
        source = self._editor.toPlainText().strip()
        if not source:
            QMessageBox.warning(self, "No Input", "Please enter source code first.")
            return

        self._last_ast_img = None
        self._btn_save_ast.setEnabled(False)
        self._ast_download_btn.setEnabled(False)

        self._reset_badges()
        self._set_status("Running full pipeline…", "running")
        self._btn_analyze.setEnabled(False)
        self._btn_compile.setEnabled(False)

        for code, _, _ in STAGES:
            self._badges[code].set_state("running")

        # Clear all stage panes
        for code, _, _ in STAGES:
            if code == "TREE":
                tree = getattr(self, "_stage_tree_TREE", None)
                if tree:
                    tree.clear()
            elif code == "AST":
                self._show_ast_error("Waiting for compilation…")
            else:
                pte = getattr(self, f"_stage_pte_{code}", None)
                if pte:
                    pte.clear()

        self._token_table.setRowCount(0)
        self._errors_text.clear()
        QApplication.processEvents()

        lines = source.splitlines()
        self._compiler_worker = CompilerWorker(lines, str(RES_DIR), str(OUTPUT_DIR))
        self._compiler_worker.stage_done.connect(self._on_stage_done)
        self._compiler_worker.pipeline_error.connect(self._on_pipeline_error)
        self._compiler_worker.finished.connect(self._on_pipeline_finished)
        self._compiler_worker.start()

    @Slot(str, object)
    def _on_stage_done(self, code: str, data: object):
        """Handle completion of one pipeline stage — all cases."""

        # ── LEX ──────────────────────────────────────────────────────────────
        if code == "LEX":
            tokens = data
            self._tokens = tokens
            errors = [t for t in tokens if t["type"] == "Unknown"]
            self._populate_token_table(tokens)
            self._populate_errors_tab(errors)
            self._populate_summary_tab(tokens)
            self._update_status_bar_counts(tokens)
            self._populate_stage_pte("LEX", self._build_lex_report(tokens))
            self._badges["LEX"].set_state("ok")

        # ── PAR ──────────────────────────────────────────────────────────────
        elif code == "PAR":
            self._populate_stage_pte("PAR", data)
            self._badges["PAR"].set_state("ok")

        # ── TREE ─────────────────────────────────────────────────────────────
        elif code == "TREE":
            kind = data[0]
            if kind == "text":
                _, text, ast = data
                self._populate_stage_tree("TREE", ast)
                self._badges["TREE"].set_state("ok")
            else:  # error
                _, msg, _ = data
                tree = getattr(self, "_stage_tree_TREE", None)
                if tree:
                    tree.clear()
                    err_item = QTreeWidgetItem([msg])
                    err_item.setForeground(0, QColor("#f07178"))
                    tree.addTopLevelItem(err_item)
                self._badges["TREE"].set_state("error")

        # ── SEM ───────────────────────────────────────────────────────────────
        elif code == "SEM":
            status, text = data
            color = "#c3e88d" if status == "ok" else "#f07178"
            pte = getattr(self, "_stage_pte_SEM", None)
            if pte:
                pte.setStyleSheet(
                    f"QPlainTextEdit{{background:#0d1117;color:{color};"
                    "border:none;selection-background-color:#264f78;}"
                )
                pte.setPlainText(text)
            self._badges["SEM"].set_state("ok" if status == "ok" else "error")

        # ── AST ───────────────────────────────────────────────────────────────
        elif code == "AST":
            kind = data[0]
            if kind == "ok":
                _, ast_node, img_path = data
                self._show_ast_tree(ast_node)
                self._show_ast_image(img_path)
                self._last_ast_img = img_path
                has_img = img_path and Path(img_path).exists()
                self._btn_save_ast.setEnabled(True)
                self._ast_download_btn.setEnabled(True)
                if has_img:
                    self._btn_save_ast.setToolTip(f"AST saved to: {img_path}")
                else:
                    self._btn_save_ast.setToolTip("Graphviz not installed — tree view available")
                self._badges["AST"].set_state("ok")
            else:  # error
                _, msg, _ = data
                self._show_ast_error(msg)
                self._last_ast_img = None
                self._btn_save_ast.setEnabled(False)
                self._ast_download_btn.setEnabled(False)
                self._badges["AST"].set_state("error")

        # ── TAC ───────────────────────────────────────────────────────────────
        elif code == "TAC":
            kind = data[0]
            if kind == "ok":
                _, tac_instr = data
                numbered = "\n".join(
                    f"{i+1:>4}:  {line}" for i, line in enumerate(tac_instr)
                )
                self._populate_stage_pte("TAC", numbered if tac_instr else "(No TAC generated)")
                self._badges["TAC"].set_state("ok")
            else:
                _, msg = data
                self._set_stage_pte_error("TAC", msg)
                self._badges["TAC"].set_state("error")

        # ── ASM ───────────────────────────────────────────────────────────────
        elif code == "ASM":
            kind = data[0]
            if kind == "ok":
                _, asm_str = data
                self._populate_stage_pte("ASM", asm_str)
                self._badges["ASM"].set_state("ok")
            else:
                _, msg = data
                self._set_stage_pte_error("ASM", msg)
                self._badges["ASM"].set_state("error")

        # ── EXEC ──────────────────────────────────────────────────────────────
        elif code == "EXEC":
            kind = data[0]
            if kind == "ok":
                _, exec_str = data
                self._populate_stage_pte("EXEC", exec_str)
                self._badges["EXEC"].set_state("ok")
            else:
                _, msg = data
                self._set_stage_pte_error("EXEC", msg)
                self._badges["EXEC"].set_state("error")

        QApplication.processEvents()

    def _set_stage_pte_error(self, code: str, message: str):
        """Show an error message in a plain-text stage tab with red colour."""
        pte = getattr(self, f"_stage_pte_{code}", None)
        if pte:
            pte.setStyleSheet(
                "QPlainTextEdit{background:#0d1117;color:#f07178;"
                "border:none;selection-background-color:#264f78;}"
            )
            pte.setPlainText(message)

    def _populate_stage_pte(self, code: str, text: str):
        pte = getattr(self, f"_stage_pte_{code}", None)
        if pte:
            pte.setPlainText(text)

    def _populate_stage_tree(self, code: str, ast_node):
        tree = getattr(self, f"_stage_tree_{code}", None)
        if tree is None or ast_node is None:
            return
        tree.clear()
        root_item = CompilerWorker._ast_to_tree_items(ast_node)
        if root_item:
            tree.addTopLevelItem(root_item)
            tree.expandToDepth(3)

    @Slot(str, str)
    def _on_pipeline_error(self, stage: str, message: str):
        self._set_status(f"{stage} error — pipeline stopped", "error")

        if stage in ("Semantic", "Parsing"):
            html = (
                f"<p style='color:#f07178;font-size:14px;font-weight:700;margin:0 0 12px;'>"
                f"⚠ {stage} Error(s)</p>"
                "<pre style='color:#ff5370;font-family:Consolas,monospace;font-size:13px;'>"
                f"{message}</pre>"
            )
            self._errors_text.setHtml(html)
            self._tabs.setCurrentIndex(1)
        else:
            QMessageBox.critical(self, f"{stage} Error",
                                 f"Pipeline error at stage {stage}:\n\n{message[:800]}")

    def _on_pipeline_finished(self):
        self._btn_analyze.setEnabled(True)
        self._btn_compile.setEnabled(True)

        # Check if all badges are OK
        all_ok = all(
            self._badges[code].get_state() == "ok"
            for code, _, _ in STAGES
        )

        if all_ok:
            self._set_status("Pipeline complete ✓", "success")
            self._tabs.setCurrentIndex(self._stage_tab_idx.get("EXEC", 0))
        else:
            # Find first error stage and switch to it
            for code, _, _ in STAGES:
                if self._badges[code].get_state() == "error":
                    self._tabs.setCurrentIndex(self._stage_tab_idx.get(code, 1))
                    break

    # ── File actions ──────────────────────────────────────────────────────────
    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Source File", "",
            "C Source Files (*.c);;All Files (*.*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._editor.setPlainText(f.read())
                self._set_status(f"Opened: {Path(path).name}", "idle")
            except Exception as exc:
                QMessageBox.critical(self, "Open Error", str(exc))

    def _on_save(self):
        content = self._editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "Nothing to Save", "Editor is empty.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Input", "",
            "C Source Files (*.c);;Text Files (*.txt);;All Files (*.*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._set_status(f"Saved: {Path(path).name}", "success")
            except Exception as exc:
                QMessageBox.critical(self, "Save Error", str(exc))

    def _on_export(self):
        if not self._tokens:
            QMessageBox.information(self, "No Tokens", "Run analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Tokens", "tokens.csv",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("Lexeme,Type,Line,Column\n")
                    for t in self._tokens:
                        lexeme = str(t["value"]).replace('"', '""')
                        f.write(f'"{lexeme}",{t["type"]},{t["line"]},{t["column"]}\n')
                self._set_status(f"Exported → {Path(path).name}", "success")
            except Exception as exc:
                QMessageBox.critical(self, "Export Error", str(exc))

    def _on_save_ast(self):
        """Save the AST image to the output/ folder (or open a save dialog)."""
        if self._last_ast_img and Path(self._last_ast_img).exists():
            # Already saved automatically by graphviz render
            dest = OUTPUT_DIR / "ast.png"
            if str(Path(self._last_ast_img).resolve()) != str(dest.resolve()):
                import shutil
                shutil.copy2(self._last_ast_img, dest)
            QMessageBox.information(
                self, "AST Saved",
                f"AST image saved to:\n{dest}"
            )
            self._set_status(f"AST saved → output/ast.png", "success")
        else:
            # Graphviz not available — offer to save the tree as text
            path, _ = QFileDialog.getSaveFileName(
                self, "Save AST (text)", str(OUTPUT_DIR / "ast.txt"),
                "Text Files (*.txt);;All Files (*.*)"
            )
            if path:
                lines = []
                def recurse(item, depth=0):
                    lines.append("  " * depth + item.text(0))
                    for i in range(item.childCount()):
                        recurse(item.child(i), depth + 1)
                for i in range(self._ast_tree.topLevelItemCount()):
                    recurse(self._ast_tree.topLevelItem(i))
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))
                    self._set_status(f"AST saved → {Path(path).name}", "success")
                except Exception as exc:
                    QMessageBox.critical(self, "Save Error", str(exc))

    def _on_clear(self):
        self._editor.clear()
        self._tokens = []
        self._last_ast_img = None
        self._token_table.setRowCount(0)
        self._errors_text.clear()
        self._breakdown_table.setRowCount(0)
        for card in (self._card_total, self._card_errors, self._card_lines, self._card_status):
            card.set_value("—")
        self._token_count_label.setText("Tokens: 0")
        self._error_count_label.setText("Errors: 0")
        self._line_count_label.setText("Lines: 0")

        for code, _, _ in STAGES:
            if code == "TREE":
                tree = getattr(self, "_stage_tree_TREE", None)
                if tree:
                    tree.clear()
            elif code == "AST":
                self._show_ast_error("")
                self._ast_msg_label.setVisible(False)
                self._ast_tree.setVisible(True)
            else:
                pte = getattr(self, f"_stage_pte_{code}", None)
                if pte:
                    pte.clear()
                    # Restore default colour
                    _, _, color = next(s for s in STAGES if s[0] == code)
                    pte.setStyleSheet(
                        f"QPlainTextEdit{{background:#0d1117;color:{color};"
                        "border:none;selection-background-color:#264f78;}}"
                    )

        self._btn_save_ast.setEnabled(False)
        self._ast_download_btn.setEnabled(False)
        self._reset_badges()
        self._set_status("Ready", "idle")

    # ── Populate helpers ──────────────────────────────────────────────────────
    def _populate_token_table(self, tokens: list[dict]):
        self._token_table.setRowCount(0)
        self._token_table.setSortingEnabled(False)
        for token in tokens:
            row = self._token_table.rowCount()
            self._token_table.insertRow(row)
            color = QColor(TOKEN_COLORS.get(token["type"], "#e6edf3"))
            items = [
                QTableWidgetItem(str(token["value"])),
                QTableWidgetItem(str(token["type"])),
                QTableWidgetItem(str(token["line"])),
                QTableWidgetItem(str(token["column"])),
            ]
            items[0].setForeground(color)
            items[1].setForeground(color)
            for col, item in enumerate(items):
                item.setTextAlignment(
                    Qt.AlignVCenter | (Qt.AlignLeft if col < 2 else Qt.AlignCenter)
                )
                self._token_table.setItem(row, col, item)
        self._token_table.setSortingEnabled(True)

    def _populate_errors_tab(self, errors: list[dict]):
        self._errors_text.clear()
        if not errors:
            self._errors_text.setPlaceholderText("✓  No lexical errors detected.")
            return
        lines = [
            "<p style='color:#f07178;font-size:14px;font-weight:700;margin:0 0 12px;'>"
            f"⚠  {len(errors)} Lexical Error(s) Found</p>"
        ]
        for i, t in enumerate(errors, 1):
            lines.append(
                f"<p style='color:#ff5370;font-family:Consolas,monospace;margin:4px 0;'>"
                f"<span style='color:#4a5568;'>[{i:03d}]</span>  "
                f"Unknown token &nbsp;<b style='color:#f07178;'>'{t['value']}'</b>"
                f"&nbsp; at line <b style='color:#ffcb6b;'>{t['line']}</b>, "
                f"col <b style='color:#89ddff;'>{t['column']}</b></p>"
            )
        self._errors_text.setHtml("".join(lines))

    def _populate_summary_tab(self, tokens: list[dict]):
        from collections import Counter
        errors     = [t for t in tokens if t["type"] == "Unknown"]
        lines_used = set(t["line"] for t in tokens)

        self._card_total.set_value(str(len(tokens)))
        self._card_errors.set_value(str(len(errors)))
        self._card_lines.set_value(str(len(lines_used)))

        if errors:
            self._card_status.set_value("⚠ Errors")
            self._card_status.set_color("#f07178")
        else:
            self._card_status.set_value("✓ OK")
            self._card_status.set_color("#c3e88d")

        by_type   = Counter(t["type"] for t in tokens)
        unique_by = {}
        for t in tokens:
            unique_by.setdefault(t["type"], set()).add(t["value"])

        self._breakdown_table.setRowCount(0)
        for cat in ["Keywords", "Identifiers", "Operators", "Punctuation",
                    "Constants", "Literals", "Unknown"]:
            count  = by_type.get(cat, 0)
            unique = len(unique_by.get(cat, set()))
            if count == 0:
                continue
            row = self._breakdown_table.rowCount()
            self._breakdown_table.insertRow(row)
            color = QColor(TOKEN_COLORS.get(cat, "#e6edf3"))
            cat_item    = QTableWidgetItem(cat)
            count_item  = QTableWidgetItem(str(count))
            unique_item = QTableWidgetItem(str(unique))
            cat_item.setForeground(color)
            count_item.setTextAlignment(Qt.AlignCenter)
            unique_item.setTextAlignment(Qt.AlignCenter)
            self._breakdown_table.setItem(row, 0, cat_item)
            self._breakdown_table.setItem(row, 1, count_item)
            self._breakdown_table.setItem(row, 2, unique_item)


# ── Entry point ────────────────────────────────────────────────────────────────
def run_gui():
    app = QApplication.instance() or QApplication(sys.argv)

    apply_stylesheet(app, theme="dark_teal.xml", extra={
        "density_scale": "0",
        "font_family":   "Roboto",
    })

    app.setStyleSheet(app.styleSheet() + """
        QMainWindow, QWidget { background-color: #0d1117; }
        QToolTip {
            background: #161b22; color: #e6edf3;
            border: 1px solid #30363d; border-radius: 4px; padding: 4px 8px;
        }
        QMessageBox { background: #161b22; }
        QMessageBox QLabel { color: #e6edf3; }
        QScrollBar:vertical {
            background: #161b22; width: 8px; border: none;
        }
        QScrollBar::handle:vertical {
            background: #30363d; border-radius: 4px; min-height: 20px;
        }
        QScrollBar::handle:vertical:hover { background: #4a5568; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal {
            background: #161b22; height: 8px; border: none;
        }
        QScrollBar::handle:horizontal {
            background: #30363d; border-radius: 4px; min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover { background: #4a5568; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
    """)

    window = LexicalAnalyzerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()