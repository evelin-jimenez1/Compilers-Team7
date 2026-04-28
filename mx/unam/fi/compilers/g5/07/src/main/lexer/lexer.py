"""
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date:
    March 15, 2026

Description:
The Lexer class is responsible for performing lexical analysis over a list of
lexemes extracted from source code written in the C language.

Responsibilities:
- Load reserved keywords from an external file.
- Load token category names from an external file.
- Define regular expressions for token recognition.
- Remove comments before tokenization.
- Process and classify tokens into predefined categories.
- Detect unknown or invalid lexical sequences.
- Count the total number of recognized tokens.

Token Categories:
- Keywords
- Identifiers
- Operators
- Punctuation
- Constants
- Literals
- Unknown

Resource Files Required:
- keywords.txt: Contains the reserved words of the C language.
- tokens.txt: Contains the token category names used by the lexer.
"""

import re
from pathlib import Path


class Lexer:
    """
    The Lexer class performs lexical analysis over a list of lexemes.

    Parameters
    ----------
    lexemes : list
        A list of strings representing the source code to be analyzed.
        Usually, each element corresponds to one line of input.
    resource_dir : str
        Path to the directory containing the resource files:
        - keywords.txt
        - tokens.txt
    """

    def __init__(self, lexemes, resource_dir: str):
        """
        Initialize the lexer with the input lexemes and resource directory.

        This constructor:
        - stores the input lexemes,
        - initializes the token classification dictionary,
        - initializes the total token counter,
        - loads keywords and token names from external files.
        """
        # Store input source code split into lexemes (typically lines)
        self.lexemes = lexemes

        # Store path to resource directory
        self.resource_dir = Path(resource_dir)

        # Set containing the reserved words of the language
        self.keywords = set()

        # Hash table / dictionary used to group tokens by category
        self.token_classification = {}

        # Total number of recognized tokens
        self.total_tokens = 0
        self.tokens_list = []

        # Initialize the token categories used in the project
        self.token_classification["Keywords"] = set()
        self.token_classification["Identifiers"] = set()
        self.token_classification["Operators"] = set()
        self.token_classification["Punctuation"] = set()
        self.token_classification["Constants"] = set()
        self.token_classification["Literals"] = set()
        self.token_classification["Unknown"] = set()

        # Load external resources
        self._load_keywords()
        self._load_tokens()

    def _load_keywords(self):
        """
        Load reserved keywords from 'keywords.txt'.

        Each non-empty line from the file is stored in the keyword set.
        """
        keywords_path = self.resource_dir / "keywords.txt"

        if keywords_path.exists():
            with open(keywords_path, "r", encoding="utf-8") as file:
                for line in file:
                    word = line.strip()
                    if word:
                        self.keywords.add(word)

    def _load_tokens(self):
        """
        Load token category names from 'tokens.txt'.

        If the file contains token categories not already initialized,
        they are added to the classification dictionary.
        """
        tokens_path = self.resource_dir / "tokens.txt"

        if tokens_path.exists():
            with open(tokens_path, "r", encoding="utf-8") as file:
                for line in file:
                    token_name = line.strip()
                    if token_name and token_name not in self.token_classification:
                        self.token_classification[token_name] = set()

    def create_keyword_regex(self):
        """
        Build a regular expression that matches any loaded keyword.

        Returns
        -------
        str
            A regex representing all keywords as complete words.
            If the keyword set is empty, a regex that matches nothing is returned.
        """
        if not self.keywords:
            return r"$^"  # Regex that matches nothing

        regex_creator = "|".join(sorted(self.keywords))
        return rf"\b({regex_creator})\b"

    def reset(self):
        """
        Reset the lexical analyzer state.

        This method clears all token category sets and resets
        the total token counter before a new analysis.
        """
        for category in self.token_classification:
            self.token_classification[category].clear()
        self.total_tokens = 0
        self.tokens_list.clear()

    def tokenize(self):
        """
        Perform lexical analysis over the stored lexemes.
        """
        # Reset any previous analysis results
        self.reset()

        keyword_regex = self.create_keyword_regex()
        id_regex = r"[a-zA-Z_][a-zA-Z0-9_]*"
        op_regex = (
            r">>=|<<=|\+=|-=|\*=|/=|%=|==|!=|>=|<=|&&|\|\||\+\+|--|<<|>>|"
            r"&=|\|=|\^=|=|>|<|!|~|\+|-|\*|/|%|&|\||\^|\?|:"
        )
        punt_regex = r"\.\.\.|[()\[\]{};,.:]"
        const_regex = (
            r"(0[xX][0-9a-fA-F]+)"
            r"|(0[0-7]+)"
            r"|(([0-9]+\.[0-9]+([eE][+-]?[0-9]+)?)"
            r"|(\.[0-9]+([eE][+-]?[0-9]+)?)"
            r"|([0-9]+[eE][+-]?[0-9]+))"
            r"|(0|[1-9][0-9]*)"
            r"|('([^'\\]|\\.)')"
        )
        lit_regex = r'"([^"\\]|\\.)*"'

        full_text = "\n".join(str(lexeme) for lexeme in self.lexemes)
        full_text = re.sub(r"/\*.*?\*/", "", full_text, flags=re.DOTALL)
        full_text = re.sub(r"//.*", "", full_text)

        lines = full_text.splitlines()

        token_pattern = re.compile(
            rf"{lit_regex}|{const_regex}|{op_regex}|{punt_regex}|{id_regex}|#|[^\s]+"
        )

        for line_num, line in enumerate(lines, 1):
            cleared_lexeme = line.strip()
            if not cleared_lexeme:
                continue

            preprocessing_line = cleared_lexeme.lstrip().startswith("#")
            matches = list(token_pattern.finditer(line))
            consumed_ranges = []

            for match in matches:
                token = match.group()
                category = "Unknown" # Categoría por defecto

                # 1. Manejo especial para '#'
                if token == "#":
                    category = "Punctuation" if preprocessing_line else "Unknown"
                    self.token_classification[category].add(token)
                    self.total_tokens += 1
                    self.tokens_list.append({
                        'type': category,
                        'value': token,
                        'line': line_num,
                        'column': match.start() + 1
                    })
                    consumed_ranges.append((match.start(), match.end()))
                    continue

                # 2. Clasificación del resto de los tokens
                if re.fullmatch(lit_regex, token):
                    category = "Literals"
                elif re.fullmatch(const_regex, token):
                    category = "Constants"
                elif re.fullmatch(op_regex, token):
                    category = "Operators"
                elif re.fullmatch(punt_regex, token):
                    category = "Punctuation"
                elif re.fullmatch(id_regex, token):
                    category = "Keywords" if token in self.keywords else "Identifiers"
                else:
                    category = "Unknown"

                # Guardado para la GUI (Sets) y Lista Secuencial (Parser/Output)
                self.token_classification[category].add(token)
                self.tokens_list.append({
                    'type': category,
                    'value': token,
                    'line': line_num,
                    'column': match.start() + 1
                })
                self.total_tokens += 1
                consumed_ranges.append((match.start(), match.end()))

            # 3. Detección de fragmentos desconocidos (Buffer)
            unknown_chars = [True] * len(line)
            for start, end in consumed_ranges:
                for i in range(start, end):
                    unknown_chars[i] = False

            buffer = []
            for i, ch in enumerate(line):
                if unknown_chars[i] and not ch.isspace():
                    buffer.append(ch)
                elif buffer:
                    unknown_token = "".join(buffer).strip()
                    if unknown_token:
                        self.token_classification["Unknown"].add(unknown_token)
                        self.tokens_list.append({
                            'type': 'Unknown',
                            'value': unknown_token,
                            'line': line_num,
                            'column': line.find(unknown_token) + 1
                        })
                        self.total_tokens += 1
                    buffer = []

            if buffer:
                unknown_token = "".join(buffer).strip()
                if unknown_token:
                    self.token_classification["Unknown"].add(unknown_token)
                    self.tokens_list.append({
                        'type': 'Unknown',
                        'value': unknown_token,
                        'line': line_num,
                        'column': line.find(unknown_token) + 1
                    })
                    self.total_tokens += 1

        return self.tokens_list

    def get_total_tokens(self):
        """
        Return the total number of recognized tokens.

        Returns
        -------
        int
            The total count of tokens recognized during lexical analysis.
        """
        return self.total_tokens