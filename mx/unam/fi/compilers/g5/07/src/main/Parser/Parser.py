"""
LL(1) Parser
---------------------------------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date:
    April 28, 2026

Program description:
This module implements the execution driver for the LL(1) syntax analyzer. 
It operates based on an explicit symbol data stack and a deterministic 
routing matrix, completely avoiding nested recursive function overhead 
or external parsing packages to comply with pure compilation theory rules.

Responsibilities:
- Maintain an explicit symbol validation stack initialized with ['$', 'PROGRAM'].
- Evaluate lookahead tokens provided by the Lexer against the stack's top element.
- Interpret and expand syntactic variables using predictive matrix records.
- Match and consume terminal boundary values while handling epsilon (λ) paths.
- Capture unexpected token distributions to output descriptive syntax error lines.

Key Logic:
- Match Operation: If TOP == Lookahead, consume token and pop symbol from stack.
- Expand Operation: If TOP is Non-Terminal, query M[TOP, Lookahead] to pop TOP 
  and push production body string elements in reverse order.
"""

from grammar import Grammar
from first_follow import compute_first, compute_follow
from Parsing_table import LL1Table

class Parser:
    """
    Driven by an explicit list-based stack array, this class processes token 
    streams syntactically according to pre-computed LL(1) table production paths.
    """
    def __init__(self, parsing_table, start_symbol):
        """
        Initializes the analytical validation driver framework.

        Parameters
        ----------
        parsing_table : dict
            Two-dimensional dictionary mapping M[Non-Terminal][Terminal] -> rule_string.
        start_symbol : str
            The designated structural entry axiom string of the grammar.
        """
        self.parsing_table = parsing_table
        self.start_symbol = start_symbol

    def parse(self, token_stream):
        """
        Processes a sequence of source tokens step-by-step using structural lookahead constraints.

        Parameters
        ----------
        token_stream : list
            A collection of dictionary elements emitted by the Lexer.
            Expected layout: {'type': str, 'value': str, 'line': int}

        Returns
        -------
        bool
            True if the token sequence successfully complies with all syntactic grammar laws.

        Raises
        ------
        SyntaxError
            If a terminal mismatch happens or an empty cell path is hit during matrix query.
        """
        # Append the theoretical End-Of-File boundary marker to copy of incoming data stream
        tokens = list(token_stream) + [{'type': '$', 'value': '$', 'line': -1}]
        
        # Initialize the explicit data stack as mandated by the predictive algorithm
        stack = ['$', self.start_symbol]
        
        token_index = 0
        current_token = tokens[token_index]
        
        # Execution evaluation driver block controlled by stack fullness bounds
        while len(stack) > 0:
            top = stack[-1]
            
            # Safe boundary lookahead property mapping extraction
            lookahead_type = current_token['type']
            lookahead_value = current_token['value']
            current_line = current_token['line']

            # Map the selection token key. Reverts to type if literal values aren't explicit column markers
            if lookahead_value in self.parsing_table.get(self.start_symbol, {}):
                lookahead_key = lookahead_value
            else:
                lookahead_key = lookahead_type

            # Case 1: Match Condition — Tope is identical to the active lookahead token
            if top == lookahead_key:
                stack.pop()
                token_index += 1
                if token_index < len(tokens):
                    current_token = tokens[token_index]
            
            # Case 2: Panic Condition — Tope is a terminal but fails to achieve a valid match
            elif top not in self.parsing_table:
                raise SyntaxError(
                    f"Syntax Error on line {current_line}: Expected token '{top}' "
                    f"but instead found source value '{lookahead_value}'."
                )
            
            # Case 3: Expand Condition — Tope is a Non-Terminal structural variable
            else:
                raw_cell_content = self.parsing_table[top].get(lookahead_key, [])
                
                # Verify cell validity. An empty lookup array indicates an analytical syntax error path
                if not raw_cell_content:
                    raise SyntaxError(
                        f"Syntax Error on line {current_line}: Unexpected token token '{lookahead_value}' "
                        f"encountered while processing structural context <{top}>."
                    )
                
                # Extract clean rule list tokens from string format (e.g., "PROGRAM -> GLOBAL PROGRAM")
                full_rule_str = raw_cell_content[0]
                body_part_str = full_rule_str.split("->")[1].strip()
                production_body = body_part_str.split()

                stack.pop() # Remove the resolved Non-Terminal variable head
                
                # Push production body parts onto the stack array sequentially in reverse sequence
                if production_body != ['epsilon']:
                    for symbol in reversed(production_body):
                        stack.append(symbol)

        print("\nGrammar verification successful: Deterministic LL(1) parser finished execution without errors.\n")
        return True


# -------------------------------------------------------------------
# MAIN RUNTIME TESTING AND MOCK INTEGRATION DRIVER
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Compile internal language components to trigger lookahead bounds
    g = Grammar()
    
    # Context patch tool initialization layer to support strict single symbol definitions
    if '!' not in g.terminals:
        g.terminals.add('!')
        
    first_res = compute_first(g.productions, g.non_terminals)
    follow_res = compute_follow(g.productions, g.non_terminals, first_res, g.start_symbol)
    
    # Instantiate matrix generator to fetch internal multi-dimensional dictionary table structures
    table_compiler = LL1Table(g, first_res, follow_res)
    
    # Initialize the structural parsing engine instance
    parser_engine = Parser(table_compiler.table, g.start_symbol)

    # Simulation Stream Mock Array mimicking an input sequence for: "int id ;"
    mock_lexer_tokens = [
        {'type': 'int', 'value': 'int', 'line': 1},
        {'type': 'id', 'value': 'counter', 'line': 1},
        {'type': ';', 'value': ';', 'line': 1}
    ]

    # Trigger syntax validation process test block
    try:
        parser_engine.parse(mock_lexer_tokens)
    except SyntaxError as syntax_failure:
        print(f"\nParser trace execution aborted: {syntax_failure}\n")