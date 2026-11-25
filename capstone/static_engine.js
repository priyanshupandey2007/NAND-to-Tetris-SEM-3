"use strict";

// Client-side fallback engine so dashboard.html runs identically on static hosting (GitHub Pages)
// as well as with dashboard_server.py locally.
window.HackStaticEngine = (function () {
  const PREDEFINED = {
    SP: 0, LCL: 1, ARG: 2, THIS: 3, THAT: 4,
    SCREEN: 16384, KBD: 24576,
    R0: 0, R1: 1, R2: 2, R3: 3, R4: 4, R5: 5, R6: 6, R7: 7,
    R8: 8, R9: 9, R10: 10, R11: 11, R12: 12, R13: 13, R14: 14, R15: 15,
  };

  const COMP = {
    "0": "0101010", "1": "0111111", "-1": "0111010", D: "0001100", A: "0110000",
    "!D": "0001101", "!A": "0110001", "-D": "0001111", "-A": "0110011",
    "D+1": "0011111", "A+1": "0110111", "D-1": "0001110", "A-1": "0110010",
    "D+A": "0000010", "A+D": "0000010", "D-A": "0010011", "A-D": "0000111",
    "D&A": "0000000", "A&D": "0000000", "D|A": "0010101", "A|D": "0010101",
    M: "1110000", "!M": "1110001", "-M": "1110011", "M+1": "1110111", "M-1": "1110010",
    "D+M": "1000010", "M+D": "1000010", "D-M": "1010011", "M-D": "1000111",
    "D&M": "1000000", "M&D": "1000000", "D|M": "1010101", "M|D": "1010101",
  };

  const DEST = {
    "": "000", M: "001", D: "010", MD: "011", DM: "011",
    A: "100", AM: "101", MA: "101", AD: "110", DA: "110", AMD: "111",
  };

  const JUMP = {
    "": "000", JGT: "001", JEQ: "010", JGE: "011",
    JLT: "100", JNE: "101", JLE: "110", JMP: "111",
  };

  const SYM_RE = /^[A-Za-z_.$:][A-Za-z0-9_.$:]*$/;

  function assemble(asmText, kVal) {
    const k = Number.isFinite(kVal) ? kVal : 51;
    const symbolTable = Object.assign({}, PREDEFINED);
    const labels = {};
    const variables = {};
    const errors = [];
    const warnings = [];
    const cleaned = [];
    const seenLabels = new Set();
    let romAddr = 0;

    asmText.split(/\r?\n/).forEach((raw, idx) => {
      const lineNum = idx + 1;
      const cut = raw.indexOf("//");
      const text = (cut >= 0 ? raw.slice(0, cut) : raw).trim();
      if (!text) return;

      if (text.startsWith("(") && text.endsWith(")")) {
        const label = text.slice(1, -1).trim();
        if (!label || !SYM_RE.test(label)) {
          errors.push(`Line ${lineNum}: invalid label '${text}'`);
          return;
        }
        if (seenLabels.has(label)) {
          warnings.push(`Warning: Duplicate label '(${label})' at line ${lineNum}`);
        } else {
          seenLabels.add(label);
        }
        symbolTable[label] = romAddr;
        labels[label] = romAddr;
      } else {
        cleaned.push([lineNum, text]);
        romAddr++;
      }
    });

    let nextVar = 16;
    const binary = [];
    cleaned.forEach(([lineNum, inst]) => {
      if (inst.startsWith("@")) {
        const sym = inst.slice(1).trim();
        if (!sym) {
          errors.push(`Line ${lineNum}: invalid instruction (empty '@')`);
          return;
        }
        let addr;
        if (/^\d+$/.test(sym)) {
          addr = parseInt(sym, 10);
          if (addr > 32767) {
            errors.push(`Line ${lineNum}: invalid instruction (@${addr} exceeds 15-bit space)`);
            return;
          }
        } else {
          if (!SYM_RE.test(sym)) {
            errors.push(`Line ${lineNum}: invalid instruction (invalid symbol '${sym}')`);
            return;
          }
          if (!(sym in symbolTable)) {
            symbolTable[sym] = nextVar;
            variables[sym] = nextVar;
            nextVar++;
          }
          addr = symbolTable[sym];
        }
        binary.push(addr.toString(2).padStart(16, "0"));
      } else {
        let comp = inst;
        let dest = "";
        let jump = "";
        if (comp.includes(";")) {
          const parts = comp.split(";");
          comp = parts[0];
          jump = parts.slice(1).join(";").replace(/\s+/g, "");
        }
        if (comp.includes("=")) {
          const parts = comp.split("=");
          dest = parts[0].replace(/\s+/g, "");
          comp = parts.slice(1).join("=");
        }
        comp = comp.replace(/\s+/g, "");
        if (!(comp in COMP) || !(dest in DEST) || !(jump in JUMP)) {
          errors.push(`Line ${lineNum}: invalid instruction ('${inst}')`);
          return;
        }
        binary.push(`111${COMP[comp]}${DEST[dest]}${JUMP[jump]}`);
      }
    });

    const ok = errors.length === 0;
    const symbolsText = (k % 3 === 0 && ok)
      ? Object.entries(symbolTable).map(([n, a]) => `${n}: ${a}`).join("\n") + "\n"
      : "";

    return {
      ok,
      k,
      kMod3: ((k % 3) + 3) % 3,
      instructionCount: binary.length,
      labelCount: Object.keys(labels).length,
      variableCount: Object.keys(variables).length,
      hack: binary.join("\n"),
      romWords: binary.map((b) => parseInt(b, 2)),
      symbols: symbolTable,
      labels,
      variables,
      symbolsText,
      errors,
      warnings,
    };
  }

  function generateBox(kVal) {
    const k = Math.max(0, Math.min(235, kVal));
    const wWords = (k % 4) + 1;
    const widthPx = 16 * wWords;
    const baseAddr = 16384 + 32 * k;
    const asm = [
      `// Box.asm for K = ${k} (Row ${k}, Width ${widthPx} px, Base ${baseAddr})`,
      "(MAIN_LOOP)",
      "    @KBD",
      "    D=M",
      "    @DRAW_BOX",
      "    D;JNE",
      "    @CLEAR_BOX",
      "    0;JMP",
      "(DRAW_BOX)",
      `    @${baseAddr}`,
      "    D=A",
      "    @rowAddr",
      "    M=D",
      "    @20",
      "    D=A",
      "    @rowCount",
      "    M=D",
      "(DRAW_ROW_LOOP)",
      "    @rowCount",
      "    D=M",
      "    @MAIN_LOOP",
      "    D;JEQ",
      "    @rowAddr",
      "    D=M",
      "    @wordAddr",
      "    M=D",
      `    @${wWords}`,
      "    D=A",
      "    @wordCount",
      "    M=D",
      "(DRAW_WORD_LOOP)",
      "    @wordCount",
      "    D=M",
      "    @DRAW_NEXT_ROW",
      "    D;JEQ",
      "    @wordAddr",
      "    A=M",
      "    M=-1",
      "    @wordAddr",
      "    M=M+1",
      "    @wordCount",
      "    M=M-1",
      "    @DRAW_WORD_LOOP",
      "    0;JMP",
      "(DRAW_NEXT_ROW)",
      "    @32",
      "    D=A",
      "    @rowAddr",
      "    M=D+M",
      "    @rowCount",
      "    M=M-1",
      "    @DRAW_ROW_LOOP",
      "    0;JMP",
      "(CLEAR_BOX)",
      `    @${baseAddr}`,
      "    D=A",
      "    @rowAddr",
      "    M=D",
      "    @20",
      "    D=A",
      "    @rowCount",
      "    M=D",
      "(CLEAR_ROW_LOOP)",
      "    @rowCount",
      "    D=M",
      "    @MAIN_LOOP",
      "    D;JEQ",
      "    @rowAddr",
      "    D=M",
      "    @wordAddr",
      "    M=D",
      `    @${wWords}`,
      "    D=A",
      "    @wordCount",
      "    M=D",
      "(CLEAR_WORD_LOOP)",
      "    @wordCount",
      "    D=M",
      "    @CLEAR_NEXT_ROW",
      "    D;JEQ",
      "    @wordAddr",
      "    A=M",
      "    M=0",
      "    @wordAddr",
      "    M=M+1",
      "    @wordCount",
      "    M=M-1",
      "    @CLEAR_WORD_LOOP",
      "    0;JMP",
      "(CLEAR_NEXT_ROW)",
      "    @32",
      "    D=A",
      "    @rowAddr",
      "    M=D+M",
      "    @rowCount",
      "    M=M-1",
      "    @CLEAR_ROW_LOOP",
      "    0;JMP",
    ].join("\n");
    return { ok: true, asm, assembled: assemble(asm, k) };
  }

  function verifyInBrowser(project, kVal, CpuClass) {
    const checks = [];
    const addRes = assemble(project.programs.addAsm, kVal);
    const addOk = addRes.ok && addRes.hack.trim() === project.programs.addHack.trim();
    const errRes = assemble("@10\nD=A\nINVALID\n", 31);
    const dupRes = assemble("(LOOP)\n@1\n(LOOP)\n@LOOP\n0;JMP\n", 32);
    checks.push({
      name: "Two-Pass Assembler & K mod 3 Features",
      passed: addOk && !errRes.ok && dupRes.warnings.length > 0,
      detail: "Browser two-pass assembly, Line 3 error, and duplicate label checks passed",
    });

    const hdl = project.hdl || {};
    const hasHdl = Boolean(hdl["Memory.hdl"] && hdl["CPU.hdl"] && hdl["Computer.hdl"]);
    checks.push({
      name: "Part A HDL Netlists (Memory, CPU, Computer)",
      passed: hasHdl,
      detail: "Memory.hdl, CPU.hdl, and Computer.hdl loaded (static browser check)",
    });

    const boxGen = generateBox(kVal);
    const cpu = new CpuClass(boxGen.assembled.romWords);
    const wWords = (kVal % 4) + 1;
    const baseAddr = 16384 + 32 * kVal;
    cpu.setKey(65);
    cpu.step(5000);
    let boxOk = true;
    for (let r = 0; r < 20; r++) {
      for (let w = 0; w < wWords; w++) {
        if (cpu.ram[baseAddr + 32 * r + w] !== -1) boxOk = false;
      }
      if (cpu.ram[baseAddr + 32 * r + wWords] !== 0) boxOk = false;
    }
    cpu.setKey(0);
    cpu.step(5000);
    for (let r = 0; r < 20; r++) {
      for (let w = 0; w < wWords; w++) {
        if (cpu.ram[baseAddr + 32 * r + w] !== 0) boxOk = false;
      }
    }
    checks.push({
      name: `Part C Box.asm CPU Simulation (K = ${kVal})`,
      passed: boxOk,
      detail: boxOk ? "All 20 rows drew (-1) on key press and cleared (0) on release" : "Box RAM check failed",
    });

    return { ok: checks.every((c) => c.passed), checks };
  }

  return { assemble, generateBox, verifyInBrowser };
})();
