import re
from pathlib import Path


class Lexer:
    def __init__(self, lexemes, resource_dir: str):
        # Lexer attributes
        self.lexemes = lexemes
        self.resource_dir = Path(resource_dir)
        self.keywords = set()
        self.token_classification = {}
        self.total_tokens = 0

        # Initialize categories (hash table / dictionary)
        self.token_classification["Keywords"] = set()
        self.token_classification["Identifiers"] = set()
        self.token_classification["Operators"] = set()
        self.token_classification["Punctuation"] = set()
        self.token_classification["Constants"] = set()
        self.token_classification["Literals"] = set()
        self.token_classification["Unknown"] = set()

        # Load files
        self._load_keywords()
        self._load_tokens()

    def _load_keywords(self):
        keywords_path = self.resource_dir / "keywords.txt"

        if keywords_path.exists():
            with open(keywords_path, "r", encoding="utf-8") as file:
                for line in file:
                    word = line.strip()
                    if word:
                        self.keywords.add(word)

    def _load_tokens(self):
        tokens_path = self.resource_dir / "tokens.txt"

        if tokens_path.exists():
            with open(tokens_path, "r", encoding="utf-8") as file:
                for line in file:
                    token_name = line.strip()
                    if token_name and token_name not in self.token_classification:
                        self.token_classification[token_name] = set()

    def create_keyword_regex(self):
        if not self.keywords:
            return r"$^"

        regex_creator = "|".join(sorted(self.keywords))
        return rf"\b({regex_creator})\b"

    def reset(self):
        for category in self.token_classification:
            self.token_classification[category].clear()
        self.total_tokens = 0

    def tokenize(self):
        self.reset()

        keyword_regex = self.create_keyword_regex()

        # Regex definitions based on your project
        id_regex = r"[a-zA-Z_][a-zA-Z0-9_]*"

        op_regex = (
            r">>=|<<=|\+=|-=|\*=|/=|%=|==|!=|>=|<=|&&|\|\||\+\+|--|<<|>>|"
            r"&=|\|=|\^=|=|>|<|!|~|\+|-|\*|/|%|&|\||\^|\?|:"
        )

        punt_regex = r"\.\.\.|[()\[\]{};,.:]"

        # Floats first, then integers, then char constants
        const_regex = (
            r"(0[xX][0-9a-fA-F]+)"                              # hex
            r"|(0[0-7]+)"                                      # octal
            r"|(([0-9]+\.[0-9]+([eE][+-]?[0-9]+)?)"            # float 10.5 / 10.5e2
            r"|(\.[0-9]+([eE][+-]?[0-9]+)?)"                   # float .5 / .5e2
            r"|([0-9]+[eE][+-]?[0-9]+))"                       # float 10e2
            r"|(0|[1-9][0-9]*)"                                # decimal integer
            r"|('([^'\\]|\\.)')"                               # char constant
        )

        lit_regex = r'"([^"\\]|\\.)*"'

        # Join text to remove comments correctly
        full_text = "\n".join(str(lexeme) for lexeme in self.lexemes)

        # Remove block comments: /* ... */
        full_text = re.sub(r"/\*.*?\*/", "", full_text, flags=re.DOTALL)

        # Remove line comments: // ...
        full_text = re.sub(r"//.*", "", full_text)

        # Split again into lines
        lines = full_text.splitlines()

        # Token pattern in scanning order
        token_pattern = re.compile(
            rf"{lit_regex}"
            rf"|{const_regex}"
            rf"|{op_regex}"
            rf"|{punt_regex}"
            rf"|{id_regex}"
            rf"|#"
            rf"|[^\s]+"
        )

        # Process each line
        for line in lines:
            cleared_lexeme = line.strip()

            if not cleared_lexeme:
                continue

            preprocessing_line = cleared_lexeme.lstrip().startswith("#")

            matches = list(token_pattern.finditer(cleared_lexeme))
            consumed_ranges = []

            for match in matches:
                token = match.group()

                # Special rule for #
                if token == "#":
                    if preprocessing_line:
                        self.token_classification["Punctuation"].add("#")
                    else:
                        self.token_classification["Unknown"].add("#")
                    self.total_tokens += 1
                    consumed_ranges.append((match.start(), match.end()))
                    continue

                if re.fullmatch(lit_regex, token):
                    self.token_classification["Literals"].add(token)

                elif re.fullmatch(const_regex, token):
                    self.token_classification["Constants"].add(token)

                elif re.fullmatch(op_regex, token):
                    self.token_classification["Operators"].add(token)

                elif re.fullmatch(punt_regex, token):
                    self.token_classification["Punctuation"].add(token)

                elif re.fullmatch(id_regex, token):
                    if token in self.keywords:
                        self.token_classification["Keywords"].add(token)
                    else:
                        self.token_classification["Identifiers"].add(token)

                else:
                    self.token_classification["Unknown"].add(token)

                self.total_tokens += 1
                consumed_ranges.append((match.start(), match.end()))

            # Detect real unknown fragments not consumed
            unknown_chars = [True] * len(cleared_lexeme)

            for start, end in consumed_ranges:
                for i in range(start, end):
                    unknown_chars[i] = False

            buffer = []
            for i, ch in enumerate(cleared_lexeme):
                if unknown_chars[i] and not ch.isspace():
                    buffer.append(ch)
                elif buffer:
                    unknown_token = "".join(buffer).strip()
                    if unknown_token:
                        self.token_classification["Unknown"].add(unknown_token)
                        self.total_tokens += 1
                    buffer = []

            if buffer:
                unknown_token = "".join(buffer).strip()
                if unknown_token:
                    self.token_classification["Unknown"].add(unknown_token)
                    self.total_tokens += 1

        return self.token_classification

    def get_total_tokens(self):
        return self.total_tokens