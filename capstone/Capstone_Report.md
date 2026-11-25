# CAPSTONE PROJECT REPORT
## MAKE THE COMPUTER DRAW A BOX

**Course:** Nand to Tetris – I  
**Subject Code:** ETCNTC301  
**Program:** B.Tech Computer Science & Engineering (AI & ML)  
**School:** School of Engineering & Technology, K.R. Mangalam University  
**Live Dashboard:** https://priyanshupandey2007.github.io/NAND-to-Tetris-SEM-3/capstone/dashboard.html  
**Video Explanation Link:** https://drive.google.com/file/d/1YRy0uXNaEcDIksSNbXDoT2BniHboCAlg/view?usp=sharing  

---

### Student Information & Personal Number ($K$)

- **Student Name:** Priyanshu Pandey
- **University Roll Number:** 2501730051
- **Course / Branch:** B.Tech CSE (AI/ML)
- **Personal Number ($K$):** **51** (Last two digits of Roll Number `2501730051`)

#### Parameter Calculations for $K = 51$:
- **Assembler Feature ($K \bmod 3$):** $51 \bmod 3 = \mathbf{0}$ — Export predefined symbols, ROM labels, and RAM variables with decimal addresses to `symbols.txt`.
- **Starting Row ($r = K$):** **Row 51** (Rows 51 to 70)
- **Box Height:** **20 rows**
- **Box Width:** $16 \times ((51 \bmod 4) + 1) = 16 \times (3 + 1) = \mathbf{64\text{ pixels}}$ (**4 words/row**)
- **Start Address:** $\text{SCREEN} + 32 \times 51 = 16384 + 1632 = \mathbf{18016}$ (`0x4660`)

---

### 1. Part A – Building the Hack Computer (HDL)

1. **`Memory.hdl`:**
   - Data RAM (`0x0000 – 0x3FFF`): Uses `RAM16K` when `address[14]` is `0`.
   - Screen Map (`0x4000 – 0x5FFF`): Uses `Screen` when `address[14]` is `1` and `address[13]` is `0`.
   - Keyboard Map (`0x6000`): Uses `Keyboard` when both `address[14]` and `address[13]` are `1`.
   - Uses a `DMux` chain on `load` so writes target only RAM or Screen, and `Mux4Way16` to select output from `address[13..14]`.
2. **`CPU.hdl` & `Computer.hdl`:**
   - Decodes bit 15 (`0` for A-instruction loading `ARegister`, `1` for C-instruction controlling `ALU`, `writeM`, `A`/`D` writes, and conditional `PC` jumps using `zr` and `ng`).
   - `Computer.hdl` integrates `ROM32K`, `CPU`, and `Memory`.

---

### 2. Part B – Python Assembler (`assembler.py`)

- **First Pass (Labels):** Strips whitespace and `//` comments, tracks ROM addresses starting at `0`, and records `(LABEL)` definitions without incrementing the instruction counter.
- **Second Pass (Machine Code & Variables):** Translates `@value` / `@symbol` A-instructions (allocating new variables starting from RAM address `16`) and `dest=comp;jump` C-instructions.
- **Extra Feature for $K = 51$ ($K \bmod 3 = 0$):** Calls `save_symbols_file(output_dir, symbol_table)` to export all predefined symbols, ROM labels, and RAM variables into `symbols.txt`.

---

### 3. Part C – Box Drawing Program (`Box.asm`)

- Polls `@KBD` in `MAIN_LOOP`:
  - Jumps to `DRAW_BOX` if `RAM[KBD] != 0`.
  - Jumps to `CLEAR_BOX` if `RAM[KBD] == 0`.
- Sets `@rowAddr = 18016` and `@rowCount = 20`.
- For each row, resets `wordAddr = rowAddr` and writes `-1` (in `DRAW_WORD_LOOP`) or `0` (in `CLEAR_WORD_LOOP`) across `4` consecutive words (`64` pixels), then advances `rowAddr` by `32`.

---

### 4. One Mistake Fixed

- **Problem:** Using a single pointer variable (`wordAddr`) across rows without resetting it back to the row start produced a slanted staircase shape instead of a straight rectangle.
- **Fix:** Separated tracking into `rowAddr` (start of each row, incremented by `32` per row) and `wordAddr` (stepped across the 4 words per row), resetting `wordAddr = rowAddr` at the start of every row loop.
