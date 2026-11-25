"""
Local Capstone Workbench Server for Nand to Tetris - I (ETCNTC301)
Student: Priyanshu Pandey (Roll No: 2501730051, K = 51)

Serves dashboard.html and static assets, and provides JSON endpoints backed by
assembler.py, generate_box_asm.py, verify_capstone.py, and project files.

Usage:
    python dashboard_server.py [port]
"""

import contextlib
import io
import json
import mimetypes
import os
import socket
import sys
import tempfile
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PART_A_DIR = os.path.join(BASE_DIR, "Part_A")
PART_B_DIR = os.path.join(BASE_DIR, "Part_B")
PART_C_DIR = os.path.join(BASE_DIR, "Part_C")

for d in (BASE_DIR, PART_B_DIR, PART_C_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

from assembler import HackAssembler, PREDEFINED_SYMBOLS, save_symbols_file
from generate_box_asm import generate_box_asm
import verify_capstone

DEFAULT_PORT = 8085


def _read_text(rel_path: str) -> str:
    full = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full):
        return ""
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def compute_k_params(k: int) -> dict:
    w_words = (k % 4) + 1
    width_px = 16 * w_words
    base_addr = 16384 + (32 * k)
    k_mod_3 = k % 3
    mod3_map = {
        0: "Export all predefined symbols, ROM labels, and RAM variables to symbols.txt",
        1: "Print clear line-numbered syntax errors instead of crashing",
        2: "Warn when a duplicate label definition is encountered",
    }
    return {
        "k": k,
        "startRow": k,
        "endRow": k + 19,
        "height": 20,
        "wordsPerRow": w_words,
        "widthPx": width_px,
        "baseAddr": base_addr,
        "baseAddrHex": f"0x{base_addr:04X}",
        "endAddr": base_addr + (32 * 19) + (w_words - 1),
        "kMod3": k_mod_3,
        "kMod3Desc": mod3_map[k_mod_3],
    }


def assemble_source(asm_text: str, k_val: int = 51) -> dict:
    """Run the real two-pass HackAssembler on arbitrary .asm text."""
    lines = asm_text.splitlines(keepends=True)
    assembler = HackAssembler(k=k_val)

    stdout_buf = io.StringIO()
    with contextlib.redirect_stdout(stdout_buf):
        assembler.first_pass(lines)
        binary_code = assembler.second_pass()

    symbols_text = ""
    if k_val % 3 == 0 and not assembler.errors:
        with tempfile.TemporaryDirectory() as tmpdir:
            sym_path = save_symbols_file(tmpdir, assembler.symbol_table)
            with open(sym_path, "r", encoding="utf-8") as f:
                symbols_text = f.read()

    return {
        "ok": len(assembler.errors) == 0,
        "k": k_val,
        "kMod3": k_val % 3,
        "instructionCount": len(binary_code),
        "labelCount": len(assembler.labels),
        "variableCount": len(assembler.variables),
        "hack": "\n".join(binary_code),
        "romWords": [int(b, 2) for b in binary_code],
        "symbols": assembler.symbol_table,
        "labels": assembler.labels,
        "variables": assembler.variables,
        "predefinedCount": len(PREDEFINED_SYMBOLS),
        "symbolsText": symbols_text,
        "errors": assembler.errors,
        "warnings": assembler.warnings,
        "log": stdout_buf.getvalue().strip(),
    }


def run_verification_suite(k_val: int = 51) -> dict:
    """Execute verify_capstone checks and capture structured pass/fail output."""
    stdout_buf = io.StringIO()
    checks = []
    passed = True

    steps = [
        ("Two-Pass Assembler & K mod 3 Features", lambda: verify_capstone.test_assembler(k_val)),
        ("Part A HDL Netlists (Memory, CPU, Computer)", verify_capstone.test_hdl_chips),
        (f"Part C Box.asm CPU Simulation (K = {k_val})", lambda: verify_capstone.simulate_hack_box(k_val)),
    ]

    with contextlib.redirect_stdout(stdout_buf):
        for name, fn in steps:
            try:
                fn()
                checks.append({"name": name, "passed": True, "detail": "All assertions passed"})
            except Exception as exc:
                passed = False
                checks.append({"name": name, "passed": False, "detail": str(exc)})

    return {
        "ok": passed,
        "k": k_val,
        "checks": checks,
        "log": stdout_buf.getvalue().strip(),
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        return

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", ""):
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/dashboard.html")
            self.end_headers()
            return

        if parsed.path == "/api/project-data":
            box_asm = _read_text("Part_C/Box.asm")
            box_hack = _read_text("Part_C/Box.hack")
            add_asm = _read_text("Part_B/Add.asm")
            add_hack = _read_text("Part_B/Add.hack")
            symbols_txt = _read_text("Part_C/symbols.txt")
            rom_words = [int(line.strip(), 2) for line in box_hack.splitlines() if line.strip()]
            payload = {
                "student": {
                    "name": "Priyanshu Pandey",
                    "rollNumber": "2501730051",
                    "course": "Nand to Tetris - I (ETCNTC301)",
                    "program": "B.Tech CSE (AI/ML)",
                    "school": "School of Engineering & Technology, K.R. Mangalam University",
                },
                "params": compute_k_params(51),
                "programs": {
                    "boxAsm": box_asm,
                    "boxHack": box_hack,
                    "boxRomWords": rom_words,
                    "addAsm": add_asm,
                    "addHack": add_hack,
                    "symbolsTxt": symbols_txt,
                },
                "hdl": {
                    "Memory.hdl": _read_text("Part_A/Memory.hdl"),
                    "CPU.hdl": _read_text("Part_A/CPU.hdl"),
                    "Computer.hdl": _read_text("Part_A/Computer.hdl"),
                    "Memory.tst": _read_text("Part_A/Memory.tst"),
                    "Memory.cmp": _read_text("Part_A/Memory.cmp"),
                    "CPU.tst": _read_text("Part_A/CPU.tst"),
                    "CPU.cmp": _read_text("Part_A/CPU.cmp"),
                    "ComputerAdd.tst": _read_text("Part_A/ComputerAdd.tst"),
                    "ComputerAdd.cmp": _read_text("Part_A/ComputerAdd.cmp"),
                },
                "files": [
                    {
                        "name": fname,
                        "exists": os.path.exists(os.path.join(BASE_DIR, fname)),
                        "sizeBytes": os.path.getsize(os.path.join(BASE_DIR, fname))
                        if os.path.exists(os.path.join(BASE_DIR, fname)) else 0,
                    }
                    for fname in [
                        "Part_A/CPU.hdl", "Part_A/Memory.hdl", "Part_A/Computer.hdl",
                        "Part_B/assembler.py", "Part_B/Add.asm", "Part_B/Add.hack", "Part_B/symbols.txt",
                        "Part_C/Box.asm", "Part_C/Box.hack", "Part_C/symbols.txt",
                        "Part_C/generate_box_asm.py", "Part_C/cpu_emulator.py",
                        "verify_capstone.py", "Priyanshu_Pandey_2501730051_Capstone_Report.pdf",
                    ]
                ],
            }
            self._send_json(payload)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            body = self._read_json_body()
        except Exception as exc:
            self._send_json({"ok": False, "error": f"Invalid JSON body: {exc}"}, HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/assemble":
            asm_text = body.get("asm", "")
            k_val = int(body.get("k", 51))
            if not asm_text.strip():
                self._send_json({"ok": False, "errors": ["Assembly source cannot be empty."]}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(assemble_source(asm_text, k_val))
            return

        if parsed.path == "/api/generate-box":
            k_val = int(body.get("k", 51))
            if k_val < 0 or k_val > 235:
                self._send_json({"ok": False, "error": "K must be between 0 and 235 so 20 rows fit inside 256 screen rows."}, HTTPStatus.BAD_REQUEST)
                return
            asm_text = generate_box_asm(k_val)
            assembled = assemble_source(asm_text, k_val)
            self._send_json({
                "ok": assembled["ok"],
                "params": compute_k_params(k_val),
                "asm": asm_text,
                "assembled": assembled,
            })
            return

        if parsed.path == "/api/verify":
            k_val = int(body.get("k", 51))
            self._send_json(run_verification_suite(k_val))
            return

        self._send_json({"ok": False, "error": "Unknown endpoint"}, HTTPStatus.NOT_FOUND)


class ThreadingHTTPServerV6(ThreadingHTTPServer):
    address_family = socket.AF_INET6


def serve(port: int = DEFAULT_PORT) -> None:
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("application/javascript", ".js")
    server_v4 = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    try:
        server_v6 = ThreadingHTTPServerV6(("::1", port), DashboardHandler)
        threading.Thread(target=server_v6.serve_forever, daemon=True).start()
    except OSError:
        pass
    print(f"Capstone dashboard running at http://localhost:{port}/dashboard.html", flush=True)
    server_v4.serve_forever()


if __name__ == "__main__":
    chosen_port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    serve(chosen_port)
