"""
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Program description:
Professional PySide6 GUI for the C-Pure Lexical Analyzer.
Provides an IDE-like interface for running lexical analysis,
viewing tokens in a styled table, inspecting lexical errors,
and reviewing a summary with key metrics.

Dependencies:
    - PySide6
    - qt-material
"""

import sys
import os
from pathlib import Path

# ── Resolve project root so imports work when run from any CWD ────────────────
THIS_FILE = Path(__file__).resolve()
MAIN_DIR  = THIS_FILE.parent.parent          # …/src/main
RES_DIR   = MAIN_DIR / "Lexer"              # keywords.txt & tokens.txt live here

if str(MAIN_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_DIR))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPlainTextEdit, QTextEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton, QStatusBar,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QSizePolicy,
    QAbstractItemView,
)
from PySide6.QtCore import (
    Qt, QRect, QSize, QThread, Signal, Slot, QTimer,
)
from PySide6.QtGui import (
    QColor, QPainter, QFont, QFontMetrics, QTextCharFormat,
    QSyntaxHighlighter, QKeySequence, QShortcut, QIcon, QPalette,
    QTextBlockUserData, QTextDocument, QAction,
)
from qt_material import apply_stylesheet

# ── Colours for token categories ─────────────────────────────────────────────
TOKEN_COLORS: dict[str, str] = {
    "Keywords":    "#82aaff",
    "Identifiers": "#c3e88d",
    "Operators":   "#f78c6c",
    "Punctuation": "#89ddff",
    "Constants":   "#f07178",
    "Literals":    "#c792ea",
    "Unknown":     "#ff5370",
}

# ── Line-number gutter ────────────────────────────────────────────────────────
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

        # Editor font
        font = QFont("JetBrains Mono")
        if not font.exactMatch():
            font = QFont("Consolas")
        font.setPointSize(12)
        self.setFont(font)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setPlaceholderText(
            "// Paste or type your C source code here…\n"
            "// Press F5 or Ctrl+R to run lexical analysis."
        )

    # ── Width helpers ─────────────────────────────────────────────────────────
    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        space  = 12 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

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

    # ── Current-line highlight ────────────────────────────────────────────────
    def _highlight_current_line(self):
        extra: list = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            line_color = QColor("#1e3a5f")
            sel.format.setBackground(line_color)
            sel.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

    # ── Paint line numbers ────────────────────────────────────────────────────
    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#161b22"))

        block      = self.firstVisibleBlock()
        block_num  = block.blockNumber()
        top        = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom     = top + round(self.blockBoundingRect(block).height())

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
            block      = block.next()
            top        = bottom
            bottom     = top + round(self.blockBoundingRect(block).height())
            block_num += 1


# ── Worker thread for lexing ──────────────────────────────────────────────────
class LexerWorker(QThread):
    finished = Signal(list)   # tokens list
    error    = Signal(str)    # error message

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


# ── Worker thread for full compiler pipeline ───────────────────────────────────
class CompilerWorker(QThread):
    """Runs the full Lexer→Parser→Semantic→TAC→ASM pipeline in a background thread."""

    # (tac_instructions: list[str], asm_code: str, tokens: list[dict])
    pipeline_done  = Signal(list, str, list)
    # (stage: str, message: str)
    pipeline_error = Signal(str, str)

    def __init__(self, lines: list[str], resource_dir: str):
        super().__init__()
        self._lines        = lines
        self._resource_dir = resource_dir

    def run(self):
        try:
            from Lexer.lexer import Lexer
            from Parser.grammar import Grammar
            from Parser.first_follow import compute_first, compute_follow
            from Parser.Parsing_table import LL1Table
            from Parser.Parser import Parser
            from Semantic.semantic_analyzer import SemanticAnalyzer
            from TAC.TAC import TACGenerator
            from TAC.Ensamblador import AssemblerGenerator

            # — Lexer —
            lexer  = Lexer(self._lines, self._resource_dir)
            tokens = lexer.tokenize()

            # — Parser —
            g       = Grammar()
            firsts  = compute_first(g.productions, g.non_terminals)
            follows = compute_follow(g.productions, g.non_terminals, firsts, g.start_symbol)
            tabla   = LL1Table(g, firsts, follows)
            parser  = Parser(tabla.table, g.start_symbol)
            ast     = parser.parse(tokens)

            # — Semantic —
            semantic = SemanticAnalyzer()
            errores  = semantic.analyze(ast)
            if errores:
                msg = "\n".join(f"  • {e}" for e in errores)
                self.pipeline_error.emit("Semantic", msg)
                return

            # — TAC —
            tac_gen   = TACGenerator()
            tac_instr = tac_gen.generate(ast)

            # — ASM —
            asm_gen = AssemblerGenerator()
            asm_str = asm_gen.generate(tac_instr)
            if isinstance(asm_str, list):
                asm_str = "\n".join(asm_str)

            self.pipeline_done.emit(tac_instr, asm_str, tokens)

        except SyntaxError as exc:
            self.pipeline_error.emit("Syntax", str(exc))
        except Exception as exc:
            self.pipeline_error.emit("Critical", str(exc))


# ── x86 Assembly syntax highlighter ───────────────────────────────────────────
class AsmHighlighter(QSyntaxHighlighter):
    """Very lightweight syntax highlighter for x86 AT&T / NASM-like assembly."""

    def __init__(self, document: QTextDocument):
        super().__init__(document)

        def fmt(color: str, bold: bool = False) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            return f

        self._rules: list[tuple] = [
            # Directives: .section .data .text .global .ascii ...
            (r"\.\w+", fmt("#82aaff", bold=True)),
            # Labels: identifier followed by colon
            (r"^\s*[A-Za-z_]\w*\s*:", fmt("#ffcb6b", bold=True)),
            # Instructions: mov, add, sub, jmp, je, ret …
            (r"\b(mov|add|sub|mul|div|imul|idiv|inc|dec|push|pop"
             r"|jmp|je|jne|jl|jle|jg|jge|cmp|test|call|ret"
             r"|and|or|xor|not|neg|lea|nop)\b",
             fmt("#c3e88d")),
            # Registers: eax, ebx, ecx …
            (r"\b(eax|ebx|ecx|edx|esi|edi|esp|ebp"
             r"|rax|rbx|rcx|rdx|rsi|rdi|rsp|rbp"
             r"|ax|bx|cx|dx|al|bl|cl|dl)\b",
             fmt("#f07178")),
            # Numbers
            (r"\b0x[0-9A-Fa-f]+\b|\b\d+\b", fmt("#c792ea")),
            # Comments
            (r"#[^\n]*", fmt("#4a5568")),
        ]
        import re
        self._compiled = [(re.compile(p), f) for p, f in self._rules]

    def highlightBlock(self, text: str):
        for regex, fmt in self._compiled:
            for m in regex.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ── Summary card widget ───────────────────────────────────────────────────────
class MetricCard(QFrame):
    def __init__(self, label: str, value: str = "—", color: str = "#80cbc4", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("MetricCard")
        self.setStyleSheet(f"""
            #MetricCard {{
                background: #1a2332;
                border: 1px solid #2d4a6e;
                border-radius: 10px;
            }}
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


# ── Main window ───────────────────────────────────────────────────────────────
class LexicalAnalyzerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("C-Pure Compiler IDE — Team 7")
        self.setMinimumSize(1280, 780)
        self.resize(1440, 880)

        self._tokens:          list[dict] = []
        self._worker:          LexerWorker    | None = None
        self._compiler_worker: CompilerWorker | None = None

        self._build_ui()
        self._connect_shortcuts()
        self._set_status("Ready", "idle")

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header
        root_layout.addWidget(self._build_header())

        # Main body (sidebar + editor/output)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_center(), stretch=1)
        root_layout.addLayout(body, stretch=1)

        # Status bar
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

        icon_lbl = QLabel("⟨/⟩")
        icon_lbl.setStyleSheet(
            "color: #80cbc4; font-size: 22px; font-weight: 700; margin-right: 10px;"
        )
        layout.addWidget(icon_lbl)

        title = QLabel("Lexical Analyzer")
        title.setStyleSheet(
            "color: #e6edf3; font-size: 20px; font-weight: 700; letter-spacing: 0.5px;"
        )
        layout.addWidget(title)

        sep = QLabel("·")
        sep.setStyleSheet("color: #4a5568; font-size: 20px; margin: 0 8px;")
        layout.addWidget(sep)

        sub = QLabel("C-Pure Compiler  ·  Team 7")
        sub.setStyleSheet("color: #6b7280; font-size: 13px;")
        layout.addWidget(sub)

        layout.addStretch()

        tag = QLabel("v1.0")
        tag.setStyleSheet(
            "color: #80cbc4; background: #1e3a46; border: 1px solid #2d6a54;"
            "border-radius: 10px; padding: 2px 10px; font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(tag)

        return header

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(190)
        sidebar.setStyleSheet(
            "background: #0d1117; border-right: 1px solid #21262d;"
        )
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        section_label = QLabel("ACTIONS")
        section_label.setStyleSheet(
            "color: #4a5568; font-size: 10px; font-weight: 700; "
            "letter-spacing: 2px; margin-bottom: 4px;"
        )
        layout.addWidget(section_label)

        def make_btn(text: str, icon: str, primary: bool = False,
                     danger: bool = False) -> QPushButton:
            btn = QPushButton(f"  {icon}  {text}")
            btn.setCursor(Qt.PointingHandCursor)
            if primary:
                style = (
                    "QPushButton { background: #00897b; color: #ffffff; "
                    "border: none; border-radius: 8px; padding: 10px 8px; "
                    "font-size: 13px; font-weight: 600; text-align: left; }"
                    "QPushButton:hover { background: #00acc1; }"
                    "QPushButton:pressed { background: #007c6d; }"
                )
            elif danger:
                style = (
                    "QPushButton { background: #1a2332; color: #f07178; "
                    "border: 1px solid #f07178; border-radius: 8px; "
                    "padding: 10px 8px; font-size: 13px; text-align: left; }"
                    "QPushButton:hover { background: #2d1a1e; }"
                    "QPushButton:pressed { background: #1a0e10; }"
                )
            else:
                style = (
                    "QPushButton { background: #161b22; color: #c9d1d9; "
                    "border: 1px solid #30363d; border-radius: 8px; "
                    "padding: 10px 8px; font-size: 13px; text-align: left; }"
                    "QPushButton:hover { background: #21262d; color: #e6edf3; }"
                    "QPushButton:pressed { background: #30363d; }"
                )
            btn.setStyleSheet(style)
            return btn

        self._btn_analyze = make_btn("Analyze", "▶", primary=True)
        self._btn_compile = make_btn("Compile + ASM", "⚙")
        self._btn_compile.setStyleSheet(
            "QPushButton { background: #1a2b4a; color: #89ddff; "
            "border: 1px solid #2d5486; border-radius: 8px; "
            "padding: 10px 8px; font-size: 13px; font-weight: 600; text-align: left; }"
            "QPushButton:hover { background: #1e3a5f; color: #e6edf3; }"
            "QPushButton:pressed { background: #0f2340; }"
            "QPushButton:disabled { color: #30363d; border-color: #21262d; }"
        )
        self._btn_open    = make_btn("Open File", "📂")
        self._btn_save    = make_btn("Save Input", "💾")
        self._btn_export  = make_btn("Export Tokens", "📤")
        self._btn_clear   = make_btn("Clear", "✕", danger=True)

        self._btn_analyze.clicked.connect(self._on_analyze)
        self._btn_compile.clicked.connect(self._on_compile)
        self._btn_open.clicked.connect(self._on_open)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_export.clicked.connect(self._on_export)
        self._btn_clear.clicked.connect(self._on_clear)

        # Shortcuts hints
        def hint(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: #4a5568; font-size: 10px; margin-left: 8px;"
            )
            return lbl

        layout.addWidget(self._btn_analyze)
        layout.addWidget(hint("F5  /  Ctrl+R"))
        layout.addSpacing(4)
        layout.addWidget(self._btn_compile)
        layout.addWidget(hint("F6  /  Ctrl+Shift+R"))
        layout.addSpacing(4)
        layout.addWidget(self._btn_open)
        layout.addWidget(hint("Ctrl+O"))
        layout.addSpacing(4)
        layout.addWidget(self._btn_save)
        layout.addWidget(hint("Ctrl+S"))
        layout.addSpacing(4)
        layout.addWidget(self._btn_export)
        layout.addSpacing(4)
        layout.addWidget(self._btn_clear)
        layout.addWidget(hint("Ctrl+L"))

        layout.addStretch()

        # Legend
        legend_title = QLabel("TOKEN TYPES")
        legend_title.setStyleSheet(
            "color: #4a5568; font-size: 10px; font-weight: 700; "
            "letter-spacing: 2px; margin-top: 8px;"
        )
        layout.addWidget(legend_title)
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

    def _build_center(self) -> QWidget:
        center = QWidget()
        center.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(center)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet(
            "QSplitter::handle { background: #21262d; height: 3px; }"
        )

        # ── Editor pane ───────────────────────────────────────────────────────
        editor_container = QWidget()
        editor_container.setStyleSheet("background: #0d1117;")
        ec_layout = QVBoxLayout(editor_container)
        ec_layout.setContentsMargins(0, 0, 0, 0)
        ec_layout.setSpacing(0)

        editor_header = QWidget()
        editor_header.setFixedHeight(36)
        editor_header.setStyleSheet(
            "background: #161b22; border-bottom: 1px solid #21262d;"
        )
        eh_layout = QHBoxLayout(editor_header)
        eh_layout.setContentsMargins(16, 0, 16, 0)
        QLabel("SOURCE CODE", editor_header).setStyleSheet(
            "color: #4a5568; font-size: 10px; font-weight: 700; letter-spacing: 2px;"
        )
        eh_layout.addWidget(QLabel("SOURCE CODE", editor_header))
        eh_layout.addStretch()
        self._cursor_pos_label = QLabel("Ln 1, Col 1")
        self._cursor_pos_label.setStyleSheet("color: #4a5568; font-size: 11px;")
        eh_layout.addWidget(self._cursor_pos_label)
        ec_layout.addWidget(editor_header)

        self._editor = CodeEditor()
        self._editor.setStyleSheet(
            "QPlainTextEdit {"
            "  background: #0d1117;"
            "  color: #e6edf3;"
            "  border: none;"
            "  selection-background-color: #264f78;"
            "}"
        )
        self._editor.cursorPositionChanged.connect(self._update_cursor_pos)
        ec_layout.addWidget(self._editor)

        splitter.addWidget(editor_container)

        # ── Output pane ───────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            "QTabWidget::pane {"
            "  border: none;"
            "  background: #0d1117;"
            "}"
            "QTabBar::tab {"
            "  background: #161b22;"
            "  color: #8892a4;"
            "  padding: 8px 24px;"
            "  font-size: 12px;"
            "  font-weight: 600;"
            "  border: none;"
            "  border-bottom: 2px solid transparent;"
            "}"
            "QTabBar::tab:selected {"
            "  color: #80cbc4;"
            "  border-bottom: 2px solid #80cbc4;"
            "  background: #0d1117;"
            "}"
            "QTabBar::tab:hover:!selected {"
            "  background: #1c2230;"
            "  color: #c9d1d9;"
            "}"
        )
        self._tabs.addTab(self._build_tokens_tab(),  "  ▦  Tokens  ")
        self._tabs.addTab(self._build_errors_tab(),  "  ✕  Errors  ")
        self._tabs.addTab(self._build_summary_tab(), "  ◈  Summary ")
        self._tabs.addTab(self._build_tac_tab(),     "  ≡  TAC     ")
        self._tabs.addTab(self._build_asm_tab(),     "  ⊞  ASM     ")

        splitter.addWidget(self._tabs)
        splitter.setSizes([420, 320])

        layout.addWidget(splitter)
        return center

    # ── Tokens tab ────────────────────────────────────────────────────────────
    def _build_tokens_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        self._token_table = QTableWidget(0, 4)
        self._token_table.setHorizontalHeaderLabels(
            ["Lexeme", "Type", "Line", "Column"]
        )
        self._token_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._token_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._token_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._token_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._token_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._token_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._token_table.setAlternatingRowColors(True)
        self._token_table.verticalHeader().setVisible(False)
        self._token_table.setShowGrid(False)
        self._token_table.setStyleSheet(
            "QTableWidget {"
            "  background: #0d1117;"
            "  alternate-background-color: #111827;"
            "  color: #e6edf3;"
            "  border: none;"
            "  gridline-color: #21262d;"
            "  font-size: 13px;"
            "}"
            "QTableWidget::item:selected {"
            "  background: #1e3a5f;"
            "}"
            "QHeaderView::section {"
            "  background: #161b22;"
            "  color: #8892a4;"
            "  font-size: 11px;"
            "  font-weight: 700;"
            "  letter-spacing: 1px;"
            "  padding: 8px 12px;"
            "  border: none;"
            "  border-bottom: 1px solid #21262d;"
            "}"
            "QScrollBar:vertical {"
            "  background: #161b22; width: 8px; border: none;"
            "}"
            "QScrollBar::handle:vertical {"
            "  background: #30363d; border-radius: 4px; min-height: 20px;"
            "}"
        )
        layout.addWidget(self._token_table)
        return w

    # ── Errors tab ────────────────────────────────────────────────────────────
    def _build_errors_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        self._errors_text = QTextEdit()
        self._errors_text.setReadOnly(True)
        self._errors_text.setStyleSheet(
            "QTextEdit {"
            "  background: #0d1117;"
            "  color: #e6edf3;"
            "  border: none;"
            "  font-family: 'Consolas', 'JetBrains Mono', monospace;"
            "  font-size: 13px;"
            "}"
        )
        self._errors_text.setPlaceholderText("No lexical errors detected.")
        layout.addWidget(self._errors_text)
        return w

    # ── Summary tab ───────────────────────────────────────────────────────────
    def _build_summary_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: #0d1117; }"
        )

        w = QWidget()
        w.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Metric cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self._card_total   = MetricCard("TOTAL TOKENS",    "—", "#80cbc4")
        self._card_errors  = MetricCard("LEXICAL ERRORS",  "—", "#f07178")
        self._card_lines   = MetricCard("LINES ANALYZED",  "—", "#c3e88d")
        self._card_status  = MetricCard("STATUS",          "—", "#ffcb6b")

        for card in (self._card_total, self._card_errors,
                     self._card_lines, self._card_status):
            cards_row.addWidget(card)

        layout.addLayout(cards_row)

        # Category breakdown
        breakdown_label = QLabel("TOKEN DISTRIBUTION")
        breakdown_label.setStyleSheet(
            "color: #4a5568; font-size: 10px; font-weight: 700; "
            "letter-spacing: 2px; margin-top: 8px;"
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
            "QTableWidget {"
            "  background: #111827;"
            "  alternate-background-color: #161b22;"
            "  color: #e6edf3;"
            "  border: 1px solid #21262d;"
            "  border-radius: 8px;"
            "  font-size: 13px;"
            "}"
            "QTableWidget::item:selected { background: #1e3a5f; }"
            "QHeaderView::section {"
            "  background: #161b22;"
            "  color: #8892a4;"
            "  font-size: 11px;"
            "  font-weight: 700;"
            "  letter-spacing: 1px;"
            "  padding: 8px 12px;"
            "  border: none;"
            "  border-bottom: 1px solid #21262d;"
            "}"
        )
        layout.addWidget(self._breakdown_table)
        layout.addStretch()

        scroll.setWidget(w)
        return scroll

    # ── TAC tab ────────────────────────────────────────────────────────────────
    def _build_tac_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # mini header
        hdr = QWidget()
        hdr.setFixedHeight(30)
        hdr.setStyleSheet("background: #161b22; border-bottom: 1px solid #21262d;")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(16, 0, 16, 0)
        lbl = QLabel("THREE-ADDRESS CODE  (TAC)")
        lbl.setStyleSheet("color: #89ddff; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        hdr_l.addWidget(lbl)
        hdr_l.addStretch()
        layout.addWidget(hdr)

        self._tac_view = QPlainTextEdit()
        self._tac_view.setReadOnly(True)
        self._tac_view.setPlaceholderText("Run  ⚙ Compile + ASM  to generate TAC…")
        font = QFont("Consolas"); font.setPointSize(12)
        self._tac_view.setFont(font)
        self._tac_view.setStyleSheet(
            "QPlainTextEdit {"
            "  background: #0d1117;"
            "  color: #c3e88d;"
            "  border: none;"
            "  selection-background-color: #264f78;"
            "}"
        )
        layout.addWidget(self._tac_view)
        return w

    # ── ASM tab ────────────────────────────────────────────────────────────────
    def _build_asm_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # mini header
        hdr = QWidget()
        hdr.setFixedHeight(30)
        hdr.setStyleSheet("background: #161b22; border-bottom: 1px solid #21262d;")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(16, 0, 16, 0)
        lbl = QLabel("x86 ASSEMBLER OUTPUT")
        lbl.setStyleSheet("color: #ffcb6b; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        hdr_l.addWidget(lbl)
        hdr_l.addStretch()
        self._asm_copy_btn = QPushButton("⎘ Copy")
        self._asm_copy_btn.setCursor(Qt.PointingHandCursor)
        self._asm_copy_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #4a5568; border: none;"
            " font-size: 11px; padding: 2px 8px; }"
            "QPushButton:hover { color: #e6edf3; }"
        )
        self._asm_copy_btn.clicked.connect(self._on_copy_asm)
        hdr_l.addWidget(self._asm_copy_btn)
        layout.addWidget(hdr)

        self._asm_view = QPlainTextEdit()
        self._asm_view.setReadOnly(True)
        self._asm_view.setPlaceholderText("Run  ⚙ Compile + ASM  to generate assembler code…")
        font = QFont("Consolas"); font.setPointSize(12)
        self._asm_view.setFont(font)
        self._asm_view.setStyleSheet(
            "QPlainTextEdit {"
            "  background: #0d1117;"
            "  color: #e6edf3;"
            "  border: none;"
            "  selection-background-color: #264f78;"
            "}"
        )
        # Attach the syntax highlighter
        self._asm_highlighter = AsmHighlighter(self._asm_view.document())
        layout.addWidget(self._asm_view)
        return w

    # ── Shortcuts ─────────────────────────────────────────────────────────────
    def _connect_shortcuts(self):
        QShortcut(QKeySequence("F5"),          self).activated.connect(self._on_analyze)
        QShortcut(QKeySequence("Ctrl+R"),      self).activated.connect(self._on_analyze)
        QShortcut(QKeySequence("F6"),          self).activated.connect(self._on_compile)
        QShortcut(QKeySequence("Ctrl+Shift+R"),self).activated.connect(self._on_compile)
        QShortcut(QKeySequence("Ctrl+O"),      self).activated.connect(self._on_open)
        QShortcut(QKeySequence("Ctrl+S"),      self).activated.connect(self._on_save)
        QShortcut(QKeySequence("Ctrl+L"),      self).activated.connect(self._on_clear)

    # ── Status helpers ────────────────────────────────────────────────────────
    def _set_status(self, text: str, state: str = "idle"):
        colors = {
            "idle":      "#8892a4",
            "running":   "#ffcb6b",
            "success":   "#c3e88d",
            "error":     "#f07178",
        }
        color = colors.get(state, "#8892a4")
        self._status_label.setText(f"● {text}")
        self._status_label.setStyleSheet(f"color: {color}; padding: 0 12px; font-weight: 600;")

    def _update_status_bar_counts(self, tokens: list[dict]):
        errors = [t for t in tokens if t["type"] == "Unknown"]
        self._token_count_label.setText(f"Tokens: {len(tokens)}")
        self._error_count_label.setText(f"Errors: {len(errors)}")
        lines  = set(t["line"] for t in tokens)
        self._line_count_label.setText(f"Lines: {len(lines)}")

    def _update_cursor_pos(self):
        cursor = self._editor.textCursor()
        ln  = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self._cursor_pos_label.setText(f"Ln {ln}, Col {col}")

    # ── Action handlers ───────────────────────────────────────────────────────
    def _on_analyze(self):
        source = self._editor.toPlainText().strip()
        if not source:
            QMessageBox.warning(self, "No Input",
                                "Please enter or open source code before analyzing.")
            return

        self._set_status("Analyzing…", "running")
        self._btn_analyze.setEnabled(False)
        QApplication.processEvents()

        lines = source.splitlines()
        self._worker = LexerWorker(lines, str(RES_DIR))
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    @Slot(list)
    def _on_analysis_done(self, tokens: list[dict]):
        self._tokens = tokens
        self._btn_analyze.setEnabled(True)

        errors = [t for t in tokens if t["type"] == "Unknown"]

        self._populate_token_table(tokens)
        self._populate_errors_tab(errors)
        self._populate_summary_tab(tokens)
        self._update_status_bar_counts(tokens)

        if errors:
            self._set_status(f"Analysis complete — {len(errors)} error(s) found", "error")
            self._tabs.setCurrentIndex(1)   # switch to Errors tab
        else:
            self._set_status("Analysis complete — No errors", "success")
            self._tabs.setCurrentIndex(0)   # switch to Tokens tab

    @Slot(str)
    def _on_analysis_error(self, message: str):
        self._btn_analyze.setEnabled(True)
        self._set_status("Analysis failed", "error")
        QMessageBox.critical(self, "Lexer Error",
                             f"An error occurred during lexical analysis:\n\n{message}")

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Source File", "",
            "C Source Files (*.c);;All Files (*.*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._editor.setPlainText(content)
                self._set_status(f"Opened: {Path(path).name}", "idle")
            except Exception as exc:
                QMessageBox.critical(self, "Open Error",
                                     f"Could not open file:\n{exc}")

    def _on_save(self):
        content = self._editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "Nothing to Save",
                                "The editor is empty.")
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
                QMessageBox.critical(self, "Save Error",
                                     f"Could not save file:\n{exc}")

    def _on_export(self):
        if not self._tokens:
            QMessageBox.information(self, "No Tokens",
                                    "Run analysis first before exporting.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Tokens", "tokens.csv",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*.*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("Lexeme,Type,Line,Column\n")
                    for t in self._tokens:
                        lexeme = str(t["value"]).replace('"', '""')
                        f.write(f'"{lexeme}",{t["type"]},{t["line"]},{t["column"]}\n')
                self._set_status(f"Tokens exported → {Path(path).name}", "success")
                QMessageBox.information(self, "Export Complete",
                                        f"Tokens saved to:\n{path}")
            except Exception as exc:
                QMessageBox.critical(self, "Export Error",
                                     f"Could not export tokens:\n{exc}")

    def _on_compile(self):
        """Full pipeline: Lexer → Parser → Semantic → TAC → ASM."""
        source = self._editor.toPlainText().strip()
        if not source:
            QMessageBox.warning(self, "No Input",
                                "Please enter or open source code before compiling.")
            return

        self._set_status("Compiling pipeline…", "running")
        self._btn_compile.setEnabled(False)
        self._btn_analyze.setEnabled(False)
        # Clear previous results
        self._tac_view.clear()
        self._asm_view.clear()
        QApplication.processEvents()

        lines = source.splitlines()
        self._compiler_worker = CompilerWorker(lines, str(RES_DIR))
        self._compiler_worker.pipeline_done.connect(self._on_pipeline_done)
        self._compiler_worker.pipeline_error.connect(self._on_pipeline_error)
        self._compiler_worker.start()

    @Slot(list, str, list)
    def _on_pipeline_done(self, tac_instr: list, asm_str: str, tokens: list):
        self._btn_compile.setEnabled(True)
        self._btn_analyze.setEnabled(True)

        # ── Populate token side panels with lexer results ──────────────────
        self._tokens = tokens
        self._populate_token_table(tokens)
        errors = [t for t in tokens if t["type"] == "Unknown"]
        self._populate_errors_tab(errors)
        self._populate_summary_tab(tokens)
        self._update_status_bar_counts(tokens)

        # ── TAC pane ───────────────────────────────────────────────────────
        if tac_instr:
            numbered = "\n".join(
                f"{i+1:>3}:  {line}" for i, line in enumerate(tac_instr)
            )
        else:
            numbered = "(No TAC instructions generated)"
        self._tac_view.setPlainText(numbered)

        # ── ASM pane ───────────────────────────────────────────────────────
        self._asm_view.setPlainText(asm_str if asm_str.strip() else "(No assembler output generated)")

        self._set_status(
            f"Pipeline complete — {len(tac_instr)} TAC instruction(s)", "success"
        )
        # Switch to ASM tab automatically
        self._tabs.setCurrentIndex(4)

    @Slot(str, str)
    def _on_pipeline_error(self, stage: str, message: str):
        self._btn_compile.setEnabled(True)
        self._btn_analyze.setEnabled(True)
        self._set_status(f"{stage} error", "error")

        if stage == "Semantic":
            # Show semantic errors in the Errors tab
            html = (
                "<p style='color:#f07178; font-size:14px; font-weight:700; margin:0 0 12px;'>"
                f"⚠  Semantic Error(s) Found</p>"
                "<pre style='color:#ff5370; font-family:Consolas,monospace; font-size:13px;'>"
                f"{message}</pre>"
            )
            self._errors_text.setHtml(html)
            self._tabs.setCurrentIndex(1)
        else:
            QMessageBox.critical(
                self, f"{stage} Error",
                f"The compiler pipeline encountered a {stage} error:\n\n{message}"
            )

    def _on_copy_asm(self):
        text = self._asm_view.toPlainText()
        if text.strip():
            QApplication.clipboard().setText(text)
            self._set_status("ASM copied to clipboard", "success")
        else:
            QMessageBox.information(self, "Nothing to Copy",
                                    "Generate assembler code first.")

    def _on_clear(self):
        self._editor.clear()
        self._tokens = []
        self._token_table.setRowCount(0)
        self._errors_text.clear()
        self._breakdown_table.setRowCount(0)
        self._card_total.set_value("—")
        self._card_errors.set_value("—")
        self._card_lines.set_value("—")
        self._card_status.set_value("—")
        self._token_count_label.setText("Tokens: 0")
        self._error_count_label.setText("Errors: 0")
        self._tac_view.clear()
        self._asm_view.clear()
        self._line_count_label.setText("Lines: 0")
        self._set_status("Ready", "idle")

    # ── Populate helpers ──────────────────────────────────────────────────────
    def _populate_token_table(self, tokens: list[dict]):
        self._token_table.setRowCount(0)
        self._token_table.setSortingEnabled(False)

        for token in tokens:
            row = self._token_table.rowCount()
            self._token_table.insertRow(row)

            color_hex = TOKEN_COLORS.get(token["type"], "#e6edf3")
            color     = QColor(color_hex)

            items = [
                QTableWidgetItem(str(token["value"])),
                QTableWidgetItem(str(token["type"])),
                QTableWidgetItem(str(token["line"])),
                QTableWidgetItem(str(token["column"])),
            ]
            items[0].setForeground(color)
            items[1].setForeground(color)

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignVCenter | (Qt.AlignLeft if col < 2 else Qt.AlignCenter))
                self._token_table.setItem(row, col, item)

        self._token_table.setSortingEnabled(True)

    def _populate_errors_tab(self, errors: list[dict]):
        self._errors_text.clear()
        if not errors:
            self._errors_text.setPlaceholderText("✓  No lexical errors detected.")
            return

        self._errors_text.setPlaceholderText("")
        html_lines = []
        html_lines.append(
            "<p style='color:#f07178; font-size:14px; font-weight:700; margin:0 0 12px;'>"
            f"⚠  {len(errors)} Lexical Error(s) Found</p>"
        )
        for i, t in enumerate(errors, 1):
            html_lines.append(
                f"<p style='color:#ff5370; font-family:Consolas,monospace; margin:4px 0;'>"
                f"<span style='color:#4a5568;'>[{i:03d}]</span>  "
                f"Unknown token &nbsp;<b style='color:#f07178;'>'{t['value']}'</b>"
                f"  &nbsp;at line <b style='color:#ffcb6b;'>{t['line']}</b>, "
                f"col <b style='color:#89ddff;'>{t['column']}</b>"
                f"</p>"
            )
        self._errors_text.setHtml("".join(html_lines))

    def _populate_summary_tab(self, tokens: list[dict]):
        errors     = [t for t in tokens if t["type"] == "Unknown"]
        lines_used = set(t["line"] for t in tokens)

        self._card_total.set_value(str(len(tokens)))
        self._card_errors.set_value(str(len(errors)))
        self._card_lines.set_value(str(len(lines_used)))

        if errors:
            self._card_status.set_value("⚠ Errors")
            self._card_status._value_label.setStyleSheet(
                "color: #f07178; font-size: 22px; font-weight: 700;"
            )
        else:
            self._card_status.set_value("✓ OK")
            self._card_status._value_label.setStyleSheet(
                "color: #c3e88d; font-size: 28px; font-weight: 700;"
            )

        # Breakdown by category
        from collections import Counter
        by_type    = Counter(t["type"] for t in tokens)
        unique_by  = {}
        for t in tokens:
            unique_by.setdefault(t["type"], set()).add(t["value"])

        self._breakdown_table.setRowCount(0)
        # Keep a consistent order
        order = ["Keywords", "Identifiers", "Operators", "Punctuation",
                 "Constants", "Literals", "Unknown"]
        for cat in order:
            count  = by_type.get(cat, 0)
            unique = len(unique_by.get(cat, set()))
            if count == 0:
                continue
            row = self._breakdown_table.rowCount()
            self._breakdown_table.insertRow(row)

            color_hex = TOKEN_COLORS.get(cat, "#e6edf3")
            color     = QColor(color_hex)

            cat_item    = QTableWidgetItem(cat)
            count_item  = QTableWidgetItem(str(count))
            unique_item = QTableWidgetItem(str(unique))

            cat_item.setForeground(color)
            count_item.setTextAlignment(Qt.AlignCenter)
            unique_item.setTextAlignment(Qt.AlignCenter)

            self._breakdown_table.setItem(row, 0, cat_item)
            self._breakdown_table.setItem(row, 1, count_item)
            self._breakdown_table.setItem(row, 2, unique_item)


# ── Entry point ───────────────────────────────────────────────────────────────
def run_gui():
    app = QApplication.instance() or QApplication(sys.argv)

    # Apply qt-material dark theme
    apply_stylesheet(app, theme="dark_teal.xml", extra={
        "density_scale": "0",
        "font_family":   "Roboto",
    })

    # Overlay custom overrides on top of qt-material
    app.setStyleSheet(app.styleSheet() + """
        QMainWindow, QWidget {
            background-color: #0d1117;
        }
        QToolTip {
            background: #161b22;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 4px 8px;
        }
        QMessageBox {
            background: #161b22;
        }
        QMessageBox QLabel {
            color: #e6edf3;
        }
        QScrollBar:vertical {
            background: #161b22;
            width: 8px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background: #30363d;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #4a5568;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar:horizontal {
            background: #161b22;
            height: 8px;
            border: none;
        }
        QScrollBar::handle:horizontal {
            background: #30363d;
            border-radius: 4px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #4a5568;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0;
        }
    """)

    window = LexicalAnalyzerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()