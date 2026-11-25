# Nand to Tetris - I (ETCNTC301)
## Capstone Project: Make the Computer Draw a Box
**School of Engineering & Technology, K.R. Mangalam University**  
**Student:** Priyanshu Pandey | **Roll Number:** 2501730051 | **Personal Number (K):** 51  
**Live Dashboard:** [https://priyanshupandey2007.github.io/NAND-to-Tetris-SEM-3/capstone/dashboard.html](https://priyanshupandey2007.github.io/NAND-to-Tetris-SEM-3/capstone/dashboard.html)

---

### Repository Structure (Organized into 3 Parts)

- **`Part_A/` — Hack Computer HDL Implementation**
  - `Memory.hdl` : 15-bit memory unit (`RAM16K`, `Screen`, `Keyboard`) using `DMux` on `load` and `Mux4Way16`.
  - `CPU.hdl` : Hack Central Processing Unit implementation.
  - `Computer.hdl` : Top-level Hack Computer wiring `ROM32K`, `CPU`, and `Memory`.
  - Test scripts & expected outputs: `Memory.tst`, `Memory.cmp`, `CPU.tst`, `CPU.cmp`, `ComputerAdd.tst`, `ComputerAdd.cmp`.

- **`Part_B/` — Two-Pass Python Assembler**
  - `assembler.py` : Two-pass assembler converting `.asm` files into 16-bit `.hack` machine code.
  - Feature for $K = 51$ ($51 \bmod 3 = 0$): Saves all predefined symbols, ROM labels, and RAM variables to `symbols.txt` via `save_symbols_file(output_dir, symbol_table)`.
  - `Add.asm`, `Add.hack`, and `symbols.txt`.

- **`Part_C/` — Box Drawing Assembly Program & Emulator**
  - `Box.asm` : Hack assembly program for $K = 51$ drawing a $64 \times 20$ black box starting at Row 51 (RAM address `18016`, 4 words/row) while any key is pressed, and clearing it when released.
  - `Box.hack` : Assembled 16-bit binary machine code.
  - `symbols.txt` : Symbol table generated when assembling `Box.asm`.
  - `generate_box_asm.py` : Parametric `Box.asm` generator (defaults to $K = 51$).
  - `cpu_emulator.py` : Hack CPU & 512×256 Screen emulator (`--headless` screenshot capture + Tkinter GUI).
  - `screenshots/` : Verified CPU Emulator captures (`box_key_pressed.png`, `box_key_released.png`).

- **Root — Verification, Interactive Dashboard & Report**
  - `verify_capstone.py` : End-to-end verification suite covering `Part_A`, `Part_B`, and `Part_C`.
  - `dashboard_server.py`, `dashboard.html`, `dashboard.css`, `dashboard.js`, `tokens.css`, `base.css` : Interactive web workbench on `localhost:8085`.
  - `Capstone_Report.md`, `build_complete_capstone_pdf.py`, `Priyanshu_Pandey_2501730051_Capstone_Report.pdf`.

---

### Quick Commands

1. **Generate `Part_C/Box.asm` for $K = 51$:**
   ```bash
   python Part_C/generate_box_asm.py 51 Part_C/Box.asm
   ```

2. **Assemble `Add.asm` or `Box.asm` using `Part_B/assembler.py`:**
   ```bash
   python Part_B/assembler.py Part_B/Add.asm 51
   python Part_B/assembler.py Part_C/Box.asm 51
   ```

3. **Run Full Verification Suite (Parts A, B, and C):**
   ```bash
   python verify_capstone.py 51
   ```

4. **Launch Interactive Web Dashboard:**
   ```bash
   python dashboard_server.py 8085
   ```
   Open `http://localhost:8085/dashboard.html`

5. **Run Standalone Desktop CPU Emulator Window:**
   ```bash
   python Part_C/cpu_emulator.py Part_C/Box.hack
   ```
