"""
Hack Assembler for Nand to Tetris - I (ETCNTC301)
School of Engineering & Technology, K.R. Mangalam University
Student: Priyanshu Pandey (Roll No: 2501730051, K = 51)

Usage:
    python assembler.py <file.asm> [K]
Example:
    python assembler.py Box.asm 51
"""

import os
import re
import sys

# Predefined Symbols in Hack Platform
PREDEFINED_SYMBOLS = {
    'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4,
    'SCREEN': 16384, 'KBD': 24576,
    'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3,
    'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7,
    'R8': 8, 'R9': 9, 'R10': 10, 'R11': 11,
    'R12': 12, 'R13': 13, 'R14': 14, 'R15': 15
}

# Computation specifications (a c1 c2 c3 c4 c5 c6)
COMP_TABLE = {
    # When a = 0 (ALU operates on D and A)
    '0':   '0101010',
    '1':   '0111111',
    '-1':  '0111010',
    'D':   '0001100',
    'A':   '0110000',
    '!D':  '0001101',
    '!A':  '0110001',
    '-D':  '0001111',
    '-A':  '0110011',
    'D+1': '0011111',
    'A+1': '0110111',
    'D-1': '0001110',
    'A-1': '0110010',
    'D+A': '0000010',
    'A+D': '0000010',
    'D-A': '0010011',
    'A-D': '0000111',
    'D&A': '0000000',
    'A&D': '0000000',
    'D|A': '0010101',
    'A|D': '0010101',
    # When a = 1 (ALU operates on D and M)
    'M':   '1110000',
    '!M':  '1110001',
    '-M':  '1110011',
    'M+1': '1110111',
    'M-1': '1110010',
    'D+M': '1000010',
    'M+D': '1000010',
    'D-M': '1010011',
    'M-D': '1000111',
    'D&M': '1000000',
    'M&D': '1000000',
    'D|M': '1010101',
    'M|D': '1010101',
}

# Destination specifications (d1 d2 d3)
DEST_TABLE = {
    '':    '000',
    'M':   '001',
    'D':   '010',
    'MD':  '011',
    'DM':  '011',
    'A':   '100',
    'AM':  '101',
    'MA':  '101',
    'AD':  '110',
    'DA':  '110',
    'AMD': '111'
}

# Jump specifications (j1 j2 j3)
JUMP_TABLE = {
    '':    '000',
    'JGT': '001',
    'JEQ': '010',
    'JGE': '011',
    'JLT': '100',
    'JNE': '101',
    'JLE': '110',
    'JMP': '111'
}

SYMBOL_PATTERN = re.compile(r'^[A-Za-z_.$:][A-Za-z0-9_.$:]*$')


# Function in assembler.py for the K mod 3 == 0 requirement
def save_symbols_file(output_dir: str, symbol_table: dict[str, int]) -> str:
    """Export all predefined symbols, ROM labels, and RAM variables to symbols.txt."""
    symbols_path = os.path.join(output_dir, "symbols.txt")
    with open(symbols_path, "w", encoding="utf-8") as f:
        for name, addr in symbol_table.items():
            f.write(f"{name}: {addr}\n")
    return symbols_path


class HackAssembler:
    """Two-pass Hack assembler translating .asm programs into 16-bit .hack machine code."""

    def __init__(self, k=51):
        self.k = k
        self.symbol_table = dict(PREDEFINED_SYMBOLS)
        self.next_variable_address = 16
        self.clean_instructions = []  # list of (original_line_num, instruction_text)
        self.labels = {}
        self.variables = {}
        self.errors = []
        self.warnings = []

    def clean_line(self, line: str) -> str:
        """Strip // comments and surrounding whitespace."""
        idx = line.find('//')
        if idx != -1:
            line = line[:idx]
        return line.strip()

    def first_pass(self, lines: list[str]) -> None:
        """
        First Pass: Strip comments/whitespace and map ROM labels like (MAIN_LOOP)
        to their instruction address without incrementing the ROM counter.
        """
        rom_address = 0
        seen_labels = set()

        for line_num, raw_line in enumerate(lines, start=1):
            cleaned = self.clean_line(raw_line)
            if not cleaned:
                continue

            if cleaned.startswith('(') and cleaned.endswith(')'):
                label = cleaned[1:-1].strip()
                if not label or not SYMBOL_PATTERN.match(label):
                    err = f"Line {line_num}: invalid label '{cleaned}'"
                    self.errors.append(err)
                    print(err)
                    continue

                if label in seen_labels:
                    warning_msg = f"Warning: Duplicate label '({label})' at line {line_num}"
                    self.warnings.append(warning_msg)
                    print(warning_msg)
                else:
                    seen_labels.add(label)

                self.symbol_table[label] = rom_address
                self.labels[label] = rom_address
            else:
                self.clean_instructions.append((line_num, cleaned))
                rom_address += 1

    def parse_a_instruction(self, instruction: str, line_num: int) -> str:
        """Translate @value or @symbol into a 16-bit binary A-instruction."""
        symbol = instruction[1:].strip()
        if not symbol:
            raise ValueError(f"Line {line_num}: Invalid empty A-instruction '@'")

        if symbol.isdigit():
            address = int(symbol)
            if address > 32767:
                raise ValueError(f"Line {line_num}: Constant @{address} exceeds 15-bit address space")
        else:
            if not SYMBOL_PATTERN.match(symbol):
                raise ValueError(f"Line {line_num}: Invalid symbol '{symbol}'")
            if symbol not in self.symbol_table:
                self.symbol_table[symbol] = self.next_variable_address
                self.variables[symbol] = self.next_variable_address
                self.next_variable_address += 1
            address = self.symbol_table[symbol]

        return format(address, '016b')

    def parse_c_instruction(self, instruction: str, line_num: int) -> str:
        """Translate dest=comp;jump into a 16-bit binary C-instruction (111accccccdddjjj)."""
        dest_part = ""
        comp_part = instruction
        jump_part = ""

        if ';' in comp_part:
            comp_part, jump_part = comp_part.split(';', 1)
            jump_part = "".join(jump_part.split())

        if '=' in comp_part:
            dest_part, comp_part = comp_part.split('=', 1)
            dest_part = "".join(dest_part.split())

        comp_part = "".join(comp_part.split())

        if comp_part not in COMP_TABLE:
            raise ValueError(f"Line {line_num}: Invalid comp expression '{comp_part}' in '{instruction}'")
        if dest_part not in DEST_TABLE:
            raise ValueError(f"Line {line_num}: Invalid dest expression '{dest_part}' in '{instruction}'")
        if jump_part not in JUMP_TABLE:
            raise ValueError(f"Line {line_num}: Invalid jump expression '{jump_part}' in '{instruction}'")

        return f"111{COMP_TABLE[comp_part]}{DEST_TABLE[dest_part]}{JUMP_TABLE[jump_part]}"

    def second_pass(self) -> list[str]:
        """Second Pass: Encode cleaned instructions into 16-bit binary strings."""
        binary_code = []

        for line_num, inst in self.clean_instructions:
            try:
                if inst.startswith('@'):
                    bin_inst = self.parse_a_instruction(inst, line_num)
                else:
                    bin_inst = self.parse_c_instruction(inst, line_num)
                binary_code.append(bin_inst)
            except Exception as err:
                error_msg = f"Line {line_num}: invalid instruction ({err})"
                self.errors.append(error_msg)
                print(error_msg)

        return binary_code

    def assemble(self, asm_file_path: str, output_hack_path: str | None = None) -> bool:
        """Assemble an .asm file into a .hack file and export symbols.txt when K mod 3 == 0."""
        if not os.path.exists(asm_file_path):
            raise FileNotFoundError(f"Input file '{asm_file_path}' not found.")

        with open(asm_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        self.first_pass(lines)
        binary_code = self.second_pass()

        if self.errors:
            print(f"Assembly completed with {len(self.errors)} error(s).")
            return False

        if not output_hack_path:
            base, _ = os.path.splitext(asm_file_path)
            output_hack_path = base + ".hack"

        with open(output_hack_path, 'w', encoding='utf-8') as f:
            for b in binary_code:
                f.write(b + "\n")

        print(f"Successfully generated: {output_hack_path} ({len(binary_code)} instructions)")

        if self.k is None or (self.k % 3 == 0):
            output_dir = os.path.dirname(os.path.abspath(output_hack_path))
            symbols_path = save_symbols_file(output_dir, self.symbol_table)
            print(f"Exported symbol table to: {symbols_path}")

        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python assembler.py <file.asm> [K]")
        print("Example: python assembler.py Box.asm 51")
        sys.exit(1)

    asm_file = sys.argv[1]
    k_val = int(sys.argv[2]) if len(sys.argv) >= 3 else 51

    print(f"--- Hack Assembler Initialized (K = {k_val}) ---")
    k_mod_3 = k_val % 3
    print(f"K mod 3 = {k_mod_3}:")
    if k_mod_3 == 0:
        print("  -> Extra Feature: Saving predefined symbols, ROM labels, and RAM variables to symbols.txt")
    elif k_mod_3 == 1:
        print("  -> Extra Feature: Enhanced syntax error reporting with line numbers")
    elif k_mod_3 == 2:
        print("  -> Extra Feature: Warning on duplicate label definitions")

    assembler = HackAssembler(k=k_val)
    success = assembler.assemble(asm_file)
    if success:
        print("Assembly finished successfully.")
    else:
        print("Assembly encountered errors.")
        sys.exit(1)


if __name__ == '__main__':
    main()
