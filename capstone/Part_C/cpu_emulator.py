"""
Hack CPU & Screen Emulator for Nand to Tetris Capstone Project
Student: Priyanshu Pandey (Roll No: 2501730051, K = 51)

Can be imported by verify_capstone.py or run directly:
    python cpu_emulator.py Box.hack
    python cpu_emulator.py Box.hack --headless --save-screenshots screenshots
"""

import os
import sys

SCREEN_BASE = 16384
SCREEN_ROWS = 256
SCREEN_WORDS_PER_ROW = 32
SCREEN_WIDTH = 512
KBD_ADDR = 24576


class HackCPUSimulator:
    """Cycle-accurate Hack CPU, 32K RAM/Screen/KBD memory, and ROM simulator."""

    def __init__(self, rom: list[int]):
        self.rom = rom
        self.ram = [0] * 32768
        self.pc = 0
        self.a_reg = 0
        self.d_reg = 0
        self.cycles = 0

    @classmethod
    def from_hack_file(cls, hack_path: str) -> "HackCPUSimulator":
        with open(hack_path, "r", encoding="utf-8") as f:
            rom = [int(line.strip(), 2) for line in f if line.strip()]
        return cls(rom)

    def set_key(self, key_code: int) -> None:
        self.ram[KBD_ADDR] = key_code

    def step(self, cycles: int = 1) -> None:
        for _ in range(cycles):
            if self.pc >= len(self.rom):
                break
            inst = self.rom[self.pc]
            self.cycles += 1

            if (inst & 0x8000) == 0:
                self.a_reg = inst & 0x7FFF
                self.pc += 1
                continue

            a_bit = (inst >> 12) & 1
            c_bits = (inst >> 6) & 0x3F
            dest_bits = (inst >> 3) & 7
            jump_bits = inst & 7

            x_val = self.d_reg
            y_val = self.ram[self.a_reg] if (a_bit == 1 and self.a_reg < 32768) else self.a_reg

            zx = (c_bits >> 5) & 1
            nx = (c_bits >> 4) & 1
            zy = (c_bits >> 3) & 1
            ny = (c_bits >> 2) & 1
            f_bit = (c_bits >> 1) & 1
            no = c_bits & 1

            x_comp = 0 if zx else x_val
            if nx:
                x_comp = (~x_comp) & 0xFFFF

            y_comp = 0 if zy else y_val
            if ny:
                y_comp = (~y_comp) & 0xFFFF

            res = (x_comp + y_comp) & 0xFFFF if f_bit else (x_comp & y_comp) & 0xFFFF
            if no:
                res = (~res) & 0xFFFF

            signed_res = res - 65536 if res >= 32768 else res

            if (dest_bits & 1) and self.a_reg < 32768:
                self.ram[self.a_reg] = signed_res
            if dest_bits & 2:
                self.d_reg = signed_res
            if dest_bits & 4:
                self.a_reg = signed_res & 0x7FFF

            zr = signed_res == 0
            ng = signed_res < 0
            pos = signed_res > 0

            if ((jump_bits & 4) and ng) or ((jump_bits & 2) and zr) or ((jump_bits & 1) and pos):
                self.pc = self.a_reg
            else:
                self.pc += 1

    def render_screen_png(self, output_path: str, title_note: str = "") -> str:
        """Render the 512x256 Hack screen buffer into a crisp PNG screenshot."""
        from PIL import Image, ImageDraw

        header_h = 34 if title_note else 0
        img = Image.new("RGB", (SCREEN_WIDTH, SCREEN_ROWS + header_h), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        if title_note:
            draw.rectangle([0, 0, SCREEN_WIDTH - 1, header_h - 1], fill=(15, 23, 42))
            draw.text((10, 10), title_note, fill=(248, 250, 252))

        pixels = img.load()
        for r in range(SCREEN_ROWS):
            row_offset = SCREEN_BASE + r * SCREEN_WORDS_PER_ROW
            y = r + header_h
            for w in range(SCREEN_WORDS_PER_ROW):
                word = self.ram[row_offset + w] & 0xFFFF
                if word == 0:
                    continue
                x_base = w * 16
                for bit in range(16):
                    if (word >> bit) & 1:
                        pixels[x_base + bit, y] = (15, 23, 42)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        draw.rectangle([0, header_h, SCREEN_WIDTH - 1, SCREEN_ROWS + header_h - 1], outline=(51, 65, 85))
        img.save(output_path)
        return output_path


def run_headless(hack_path: str, screenshot_dir: str | None = None) -> None:
    sim = HackCPUSimulator.from_hack_file(hack_path)

    sim.set_key(65)  # Simulate pressing 'A'
    sim.step(5000)
    print(f"[Headless] After 5000 cycles with KBD=65: RAM[18016]={sim.ram[18016]}, PC={sim.pc}")
    if screenshot_dir:
        out_pressed = os.path.join(screenshot_dir, "box_key_pressed.png")
        sim.render_screen_png(out_pressed, "CPU Emulator Screen (KBD = 65 | Box 64x20 at Row 51)")
        print(f"Saved screenshot: {out_pressed}")

    sim.set_key(0)  # Release key
    sim.step(5000)
    print(f"[Headless] After 5000 cycles with KBD=0 : RAM[18016]={sim.ram[18016]}, PC={sim.pc}")
    if screenshot_dir:
        out_released = os.path.join(screenshot_dir, "box_key_released.png")
        sim.render_screen_png(out_released, "CPU Emulator Screen (KBD = 0 | Box Cleared)")
        print(f"Saved screenshot: {out_released}")


def run_gui(hack_path: str) -> None:
    import tkinter as tk

    sim = HackCPUSimulator.from_hack_file(hack_path)
    root = tk.Tk()
    root.title("Hack CPU Emulator — Priyanshu Pandey (2501730051 | K = 51)")
    root.resizable(False, False)

    info_var = tk.StringVar(value="Hold any key (or click 'Simulate Key Press') to draw the 64x20 box at Row 51")
    tk.Label(root, textvariable=info_var, font=("Consolas", 10), bg="#0f172a", fg="#f8fafc", pady=6, padx=10).pack(fill="x")

    photo = tk.PhotoImage(width=SCREEN_WIDTH, height=SCREEN_ROWS)
    photo.put("#ffffff", to=(0, 0, SCREEN_WIDTH, SCREEN_ROWS))
    canvas = tk.Canvas(root, width=SCREEN_WIDTH, height=SCREEN_ROWS, bg="white", highlightthickness=1, highlightbackground="#334155")
    canvas.pack(padx=10, pady=10)
    canvas.create_image(0, 0, anchor="nw", image=photo)

    status_var = tk.StringVar(value="KBD: 0 | PC: 0 | RAM[18016]: 0")
    controls = tk.Frame(root, pady=6)
    controls.pack(fill="x", padx=10)
    tk.Label(controls, textvariable=status_var, font=("Consolas", 9)).pack(side="left")

    manual_hold = {"active": False}

    def on_key_press(event):
        code = ord(event.char) if event.char else (event.keysym_num & 0xFFFF)
        sim.set_key(code if code != 0 else 1)

    def on_key_release(_event):
        if not manual_hold["active"]:
            sim.set_key(0)

    def toggle_hold():
        manual_hold["active"] = not manual_hold["active"]
        sim.set_key(65 if manual_hold["active"] else 0)
        btn.config(text="Release Key (KBD=0)" if manual_hold["active"] else "Simulate Key Press (KBD=65)")

    btn = tk.Button(controls, text="Simulate Key Press (KBD=65)", command=toggle_hold)
    btn.pack(side="right")

    root.bind("<KeyPress>", on_key_press)
    root.bind("<KeyRelease>", on_key_release)

    prev_words = [0] * (SCREEN_ROWS * SCREEN_WORDS_PER_ROW)

    def tick():
        sim.step(2000)
        for idx in range(SCREEN_ROWS * SCREEN_WORDS_PER_ROW):
            val = sim.ram[SCREEN_BASE + idx] & 0xFFFF
            if val != prev_words[idx]:
                prev_words[idx] = val
                r = idx // SCREEN_WORDS_PER_ROW
                x0 = (idx % SCREEN_WORDS_PER_ROW) * 16
                if val == 0:
                    photo.put("#ffffff", to=(x0, r, x0 + 16, r + 1))
                elif val == 0xFFFF:
                    photo.put("#000000", to=(x0, r, x0 + 16, r + 1))
                else:
                    row_colors = " ".join("#000000" if (val >> b) & 1 else "#ffffff" for b in range(16))
                    photo.put("{" + row_colors + "}", to=(x0, r))
        status_var.set(f"KBD: {sim.ram[KBD_ADDR]} | PC: {sim.pc} | RAM[18016]: {sim.ram[18016]}")
        root.after(25, tick)

    tick()
    root.mainloop()


if __name__ == "__main__":
    hack = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "Box.hack")
    if "--headless" in sys.argv:
        shot_dir = None
        if "--save-screenshots" in sys.argv:
            idx = sys.argv.index("--save-screenshots")
            shot_dir = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "screenshots"
        run_headless(hack, shot_dir)
    else:
        run_gui(hack)
