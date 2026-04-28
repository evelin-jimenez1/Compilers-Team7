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

    def tokenize(self):
        """
        Perform lexical analysis over the stored lexemes.

        Processing steps:
        1. Reset previous results.
        2. Define the regular expressions for token categories.
        3. Join all lexemes into a single text block.
        4. Remove block and line comments.
        5. Split the cleaned text into lines again.
        6. Scan each line using the token regex pattern.
        7. Classify every recognized token.
        8. Detect unknown fragments not matched by any valid pattern.

        Returns
        -------
        dict
            A dictionary mapping token categories to sets of recognized tokens.
        """
        # Reset any previous analysis results
        self.reset()

        # Build regex dynamically for keywords
        keyword_regex = self.create_keyword_regex()

        # Regex for identifiers:
        # starts with a letter or underscore, followed by letters, digits, or underscores
        id_regex = r"[a-zA-Z_][a-zA-Z0-9_]*"

        # Regex for operators used in the project
        op_regex = (
            r">>=|<<=|\+=|-=|\*=|/=|%=|==|!=|>=|<=|&&|\|\||\+\+|--|<<|>>|"
            r"&=|\|=|\^=|=|>|<|!|~|\+|-|\*|/|%|&|\||\^|\?|:"
        )

        # Regex for punctuation symbols
        punt_regex = r"\.\.\.|[()\[\]{};,.:]"

        # Regex for constants.
        # Floating-point patterns are placed before integer patterns
        # to avoid splitting values like 10.5 into 10 and .5.
        const_regex = (
            r"(0[xX][0-9a-fA-F]+)"                              # hexadecimal
            r"|(0[0-7]+)"                                      # octal
            r"|(([0-9]+\.[0-9]+([eE][+-]?[0-9]+)?)"            # float: 10.5 or 10.5e2
            r"|(\.[0-9]+([eE][+-]?[0-9]+)?)"                   # float: .5 or .5e2
            r"|([0-9]+[eE][+-]?[0-9]+))"                       # float: 10e2
            r"|(0|[1-9][0-9]*)"                                # decimal integer
            r"|('([^'\\]|\\.)')"                               # char constant
        )

        # Regex for string literals
        lit_regex = r'"([^"\\]|\\.)*"'

        # Join all lexemes into one text block to remove comments correctly
        full_text = "\n".join(str(lexeme) for lexeme in self.lexemes)

        # Remove block comments: /* ... */
        full_text = re.sub(r"/\*.*?\*/", "", full_text, flags=re.DOTALL)

        # Remove line comments: // ...
        full_text = re.sub(r"//.*", "", full_text)

        # Split the cleaned text back into lines
        lines = full_text.splitlines()

        # Token scanning pattern.
        # The order is important to correctly match longer or more specific tokens first.
        token_pattern = re.compile(
            rf"{lit_regex}"
            rf"|{const_regex}"
            rf"|{op_regex}"
            rf"|{punt_regex}"
            rf"|{id_regex}"
            rf"|#"
            rf"|[^\s]+"
        )

        # Process each line independently
        for line in lines:
            cleared_lexeme = line.strip()

            # Ignore empty lines
            if not cleared_lexeme:
                continue

            # Special rule:
            # '#' is valid punctuation only at the beginning of preprocessing lines
            preprocessing_line = cleared_lexeme.lstrip().startswith("#")

            # Find all token candidates in the line
            matches = list(token_pattern.finditer(cleared_lexeme))

            # Store ranges already consumed by valid matches
            consumed_ranges = []

            for match in matches:
                token = match.group()

                # Special handling for '#'
                if token == "#":
                    if preprocessing_line:
                        self.token_classification["Punctuation"].add("#")
                    else:
                        self.token_classification["Unknown"].add("#")

                    self.total_tokens += 1
                    consumed_ranges.append((match.start(), match.end()))
                    continue

                # Classify token according to the category it matches
                if re.fullmatch(lit_regex, token):
                    self.token_classification["Literals"].add(token)

                elif re.fullmatch(const_regex, token):
                    self.token_classification["Constants"].add(token)

                elif re.fullmatch(op_regex, token):
                    self.token_classification["Operators"].add(token)

                elif re.fullmatch(punt_regex, token):
                    self.token_classification["Punctuation"].add(token)

                elif re.fullmatch(id_regex, token):
                    # If the token matches the identifier pattern,
                    # it may still be a reserved keyword
                    if token in self.keywords:
                        self.token_classification["Keywords"].add(token)
                    else:
                        self.token_classification["Identifiers"].add(token)

                else:
                    # If no valid category matches, classify as unknown
                    self.token_classification["Unknown"].add(token)

                # Update counters and mark the consumed range
                self.total_tokens += 1
                consumed_ranges.append((match.start(), match.end()))

            # Detect any remaining fragments not consumed by valid tokens
            unknown_chars = [True] * len(cleared_lexeme)

            # Mark consumed positions as False
            for start, end in consumed_ranges:
                for i in range(start, end):
                    unknown_chars[i] = False

            # Build unknown fragments from leftover characters
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

            # If the line ends while the buffer still has unknown characters,
            # store them as an Unknown token
            if buffer:
                unknown_token = "".join(buffer).strip()
                if unknown_token:
                    self.token_classification["Unknown"].add(unknown_token)
                    self.total_tokens += 1

        return self.token_classification

    def get_total_tokens(self):
        """
        Return the total number of recognized tokens.

        Returns
        -------
        int
            The total count of tokens recognized during lexical analysis.
        """
        return self.total_tokens