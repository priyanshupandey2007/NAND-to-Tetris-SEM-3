"use strict";

class HackBrowserCPU {
  constructor(rom) {
    this.rom = rom || [];
    this.ram = new Int16Array(32768);
    this.pc = 0;
    this.aReg = 0;
    this.dReg = 0;
    this.cycles = 0;
  }

  reset(rom) {
    if (rom) this.rom = rom;
    this.ram.fill(0);
    this.pc = 0;
    this.aReg = 0;
    this.dReg = 0;
    this.cycles = 0;
  }

  setKey(code) {
    this.ram[24576] = code & 0xFFFF;
  }

  step(count) {
    const romLen = this.rom.length;
    if (romLen === 0) return;

    for (let i = 0; i < count; i++) {
      if (this.pc >= romLen) break;
      const inst = this.rom[this.pc];
      this.cycles++;

      if ((inst & 0x8000) === 0) {
        this.aReg = inst & 0x7FFF;
        this.pc++;
        continue;
      }

      const aBit = (inst >> 12) & 1;
      const cBits = (inst >> 6) & 0x3F;
      const destBits = (inst >> 3) & 7;
      const jumpBits = inst & 7;

      const xVal = this.dReg & 0xFFFF;
      const yVal = (aBit === 1 && this.aReg < 32768) ? (this.ram[this.aReg] & 0xFFFF) : (this.aReg & 0xFFFF);

      let xComp = (cBits & 32) ? 0 : xVal;
      if (cBits & 16) xComp = (~xComp) & 0xFFFF;

      let yComp = (cBits & 8) ? 0 : yVal;
      if (cBits & 4) yComp = (~yComp) & 0xFFFF;

      let res = (cBits & 2) ? ((xComp + yComp) & 0xFFFF) : (xComp & yComp);
      if (cBits & 1) res = (~res) & 0xFFFF;

      const signedRes = (res >= 32768) ? (res - 65536) : res;

      if ((destBits & 1) && this.aReg < 32768) this.ram[this.aReg] = signedRes;
      if (destBits & 2) this.dReg = signedRes;
      if (destBits & 4) this.aReg = signedRes & 0x7FFF;

      const zr = signedRes === 0;
      const ng = signedRes < 0;
      const pos = signedRes > 0;

      if (((jumpBits & 4) && ng) || ((jumpBits & 2) && zr) || ((jumpBits & 1) && pos)) {
        this.pc = this.aReg;
      } else {
        this.pc++;
      }
    }
  }
}

(function initDashboard() {
  const state = {
    k: 51,
    baseAddr: 18016,
    wordsPerRow: 4,
    cpu: new HackBrowserCPU([]),
    paused: false,
    manualHold: false,
    pulseActive: false,
    pulseTimer: null,
    pulseHigh: false,
    project: null,
    lastAssembled: null,
  };

  const canvas = document.getElementById("hack-screen");
  const ctx = canvas.getContext("2d");
  const imgData = ctx.createImageData(512, 256);

  const tabs = Array.from(document.querySelectorAll(".tab-btn"));
  const panels = {
    simulator: document.getElementById("panel-simulator"),
    assembler: document.getElementById("panel-assembler"),
    hdl: document.getElementById("panel-hdl"),
    viva: document.getElementById("panel-viva"),
    reports: document.getElementById("panel-reports"),
  };

  function setActiveTab(tabName, updateUrl = true) {
    if (!panels[tabName]) tabName = "simulator";
    tabs.forEach((btn) => {
      const active = btn.dataset.tab === tabName;
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    Object.entries(panels).forEach(([key, el]) => {
      el.hidden = key !== tabName;
    });
    if (updateUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set("tab", tabName);
      window.history.replaceState({}, "", url);
    }
  }

  tabs.forEach((btn) => {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.tab));
  });

  const initialTab = new URLSearchParams(window.location.search).get("tab") || "simulator";
  setActiveTab(initialTab, false);

  function computeParams(k) {
    const words = (k % 4) + 1;
    const widthPx = 16 * words;
    const baseAddr = 16384 + 32 * k;
    const kMod3 = k % 3;
    const mod3Labels = [
      "Save all labels and variables to symbols.txt",
      "Line-numbered syntax error diagnostics",
      "Duplicate label warning",
    ];
    return { k, words, widthPx, baseAddr, kMod3, mod3Desc: mod3Labels[kMod3] };
  }

  function updateParameterDisplays(k) {
    const p = computeParams(k);
    state.k = p.k;
    state.baseAddr = p.baseAddr;
    state.wordsPerRow = p.words;

    const hex = "0x" + p.baseAddr.toString(16).toUpperCase().padStart(4, "0");
    document.getElementById("global-status").textContent = `K = ${p.k} | Row ${p.k} | ${p.widthPx} x 20 px`;
    document.getElementById("tel-k").textContent = String(p.k);
    document.getElementById("tel-row").textContent = `Row ${p.k} (Address ${p.baseAddr} / ${hex})`;
    document.getElementById("tel-dims").textContent = `${p.widthPx} px width x 20 rows height (${p.words} words/row)`;
    for (let w = 0; w < 4; w++) {
      document.getElementById(`tel-word${w}-label`).textContent = `RAM[${p.baseAddr + w}] (Screen Row ${p.k}, Word ${w})`;
    }
    document.getElementById("memory-proof").innerHTML =
      `<div class="proof-title">Memory Calculation Proof (K = ${p.k})</div>` +
      `<div>Base Address = SCREEN + (32 x ${p.k}) = 16384 + ${32 * p.k} = ${p.baseAddr} (${hex})</div>` +
      `<div>Width = 16 x ((${p.k} mod 4) + 1) = 16 x ${p.words} = ${p.widthPx} pixels (${p.words} words/row, ${p.words * 20} words across 20 rows)</div>`;
    document.getElementById("sim-helper").textContent =
      `Interactive keyboard: hold any physical key on your keyboard while this tab is focused to draw the ${p.widthPx} x 20 box at Row ${p.k}, and release to clear it.`;

    // Viva calculator fields
    document.getElementById("viva-k-chip").textContent = `K = ${p.k}`;
    document.getElementById("calc-start-row").textContent = `Row ${p.k} (Rows ${p.k} to ${p.k + 19})`;
    document.getElementById("calc-base-addr").textContent = `${p.baseAddr} (${hex})`;
    document.getElementById("calc-words").textContent = `${p.words} word(s)/row`;
    document.getElementById("calc-width").textContent = `${p.widthPx} pixels`;
    document.getElementById("calc-mod3").textContent = `${p.k} mod 3 = ${p.kMod3}: ${p.mod3Desc}`;
  }

  function renderCanvasAndTelemetry() {
    const ram = state.cpu.ram;
    const data = imgData.data;
    // Screen lit = crisp near-white phosphor, Screen dark = deep ink
    let ptr = 0;
    for (let r = 0; r < 256; r++) {
      const rowOffset = 16384 + r * 32;
      for (let w = 0; w < 32; w++) {
        const word = ram[rowOffset + w] & 0xFFFF;
        for (let b = 0; b < 16; b++) {
          const black = ((word >> b) & 1) === 1;
          if (black) {
            data[ptr++] = 15;
            data[ptr++] = 24;
            data[ptr++] = 18;
            data[ptr++] = 255;
          } else {
            data[ptr++] = 243;
            data[ptr++] = 249;
            data[ptr++] = 244;
            data[ptr++] = 255;
          }
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);

    const kbdVal = ram[24576];
    const kbdBadge = document.getElementById("kbd-badge");
    const kbdTel = document.getElementById("tel-kbd");
    if (kbdVal !== 0) {
      kbdBadge.textContent = `Key: Pressed (${kbdVal}) - Drawing Box`;
      kbdBadge.classList.add("is-active");
      kbdTel.textContent = `${kbdVal} (Pressed)`;
    } else {
      kbdBadge.textContent = "Key: Idle (0) - Screen Clear";
      kbdBadge.classList.remove("is-active");
      kbdTel.textContent = "0 (No Key)";
    }

    document.getElementById("tel-pc").textContent = String(state.cpu.pc);
    document.getElementById("tel-a").textContent = String(state.cpu.aReg);
    document.getElementById("tel-d").textContent = String(state.cpu.dReg);
    document.getElementById("tel-cycles").textContent = state.cpu.cycles.toLocaleString();

    for (let w = 0; w < 4; w++) {
      const val = ram[state.baseAddr + w];
      const u16 = val & 0xFFFF;
      document.getElementById(`tel-word${w}`).textContent = `0x${u16.toString(16).toUpperCase().padStart(4, "0")} (${val})`;
    }
  }

  function frameLoop() {
    if (!state.paused) {
      state.cpu.step(2000);
    }
    renderCanvasAndTelemetry();
    window.requestAnimationFrame(frameLoop);
  }

  // Interactive Key Controls
  const btnHold = document.getElementById("btn-hold-key");
  const btnPulse = document.getElementById("btn-pulse-key");
  const btnPause = document.getElementById("btn-pause-cpu");
  const btnReset = document.getElementById("btn-reset-cpu");

  function setHoldActive(active, keyCode = 65) {
    state.manualHold = active;
    state.cpu.setKey(active ? keyCode : 0);
    btnHold.textContent = active ? "Release key (pressed)" : "Hold key";
    btnHold.classList.toggle("btn--selected", active);
  }

  btnHold.addEventListener("pointerdown", () => setHoldActive(true, 65));
  btnHold.addEventListener("pointerup", () => setHoldActive(false));
  btnHold.addEventListener("pointerleave", () => { if (state.manualHold) setHoldActive(false); });
  btnHold.addEventListener("keydown", (e) => { if (e.key === " " || e.key === "Enter") setHoldActive(true, 65); });
  btnHold.addEventListener("keyup", (e) => { if (e.key === " " || e.key === "Enter") setHoldActive(false); });

  btnPulse.addEventListener("click", () => {
    state.pulseActive = !state.pulseActive;
    btnPulse.classList.toggle("btn--selected", state.pulseActive);
    if (state.pulseTimer) {
      clearInterval(state.pulseTimer);
      state.pulseTimer = null;
    }
    if (state.pulseActive) {
      state.pulseHigh = true;
      state.cpu.setKey(65);
      state.pulseTimer = setInterval(() => {
        state.pulseHigh = !state.pulseHigh;
        state.cpu.setKey(state.pulseHigh ? 65 : 0);
      }, 500);
    } else {
      state.cpu.setKey(0);
    }
  });

  btnPause.addEventListener("click", () => {
    state.paused = !state.paused;
    btnPause.textContent = state.paused ? "Resume CPU" : "Pause CPU";
    const fpsBadge = document.getElementById("fps-badge");
    fpsBadge.textContent = state.paused ? "CPU Paused" : "Running at 60 FPS";
    fpsBadge.classList.toggle("is-active", !state.paused);
  });

  btnReset.addEventListener("click", () => {
    state.pulseActive = false;
    if (state.pulseTimer) clearInterval(state.pulseTimer);
    btnPulse.classList.remove("btn--selected");
    setHoldActive(false);
    state.cpu.reset();
  });

  window.addEventListener("keydown", (e) => {
    const tag = (e.target && e.target.tagName) || "";
    if (tag === "TEXTAREA" || tag === "INPUT") return;
    if (!panels.simulator.hidden && !state.pulseActive) {
      const code = e.key && e.key.length === 1 ? e.key.charCodeAt(0) : (e.keyCode || 65);
      state.cpu.setKey(code || 65);
    }
  });

  window.addEventListener("keyup", (e) => {
    const tag = (e.target && e.target.tagName) || "";
    if (tag === "TEXTAREA" || tag === "INPUT") return;
    if (!state.manualHold && !state.pulseActive) {
      state.cpu.setKey(0);
    }
  });

  // Assembler Tab
  function renderAssemblerOutput(res) {
    state.lastAssembled = res;
    const statusChip = document.getElementById("asm-status-chip");
    const feedback = document.getElementById("asm-feedback");
    const hackTbody = document.getElementById("hack-tbody");
    const symTbody = document.getElementById("symbols-tbody");

    const kMod3 = res.kMod3 !== undefined ? res.kMod3 : (Number(document.getElementById("asm-k-input").value) % 3);
    const modDesc = ["Save symbols.txt", "Line-numbered errors", "Duplicate label warning"][kMod3];
    document.getElementById("asm-k-badge").textContent = `K mod 3 = ${kMod3} (${modDesc})`;

    const labelEntries = Object.entries(res.labels || {}).map(([k, v]) => `${k}=${v}`).join(", ") || "none";
    const varEntries = Object.entries(res.variables || {}).map(([k, v]) => `${k}@${v}`).join(", ") || "none";
    document.getElementById("asm-pass1-line").textContent =
      `Pass 1 (Labels): ${res.labelCount || 0} label(s) recorded (${labelEntries}).`;
    document.getElementById("asm-pass2-line").textContent =
      `Pass 2 (Variables & Binary): ${res.variableCount || 0} RAM variable(s) allocated from 16 (${varEntries}).`;
    document.getElementById("asm-mod3-line").textContent =
      `K = ${res.k !== undefined ? res.k : 51} (K mod 3 = ${kMod3}): ${modDesc}.`;

    if (!res.ok) {
      statusChip.textContent = `${res.errors.length} error(s)`;
      statusChip.className = "status-chip is-error";
      feedback.className = "message-banner is-error";
      feedback.textContent = res.errors.join(" | ");
      hackTbody.innerHTML = "";
    } else {
      statusChip.textContent = `${res.instructionCount} instructions`;
      statusChip.className = "status-chip is-active";
      feedback.className = "message-banner is-success";
      const warnTxt = res.warnings && res.warnings.length ? ` Warnings: ${res.warnings.join(" | ")}` : "";
      feedback.textContent = `Assembly succeeded: ${res.instructionCount} 16-bit instructions generated.${warnTxt}`;

      const lines = res.hack ? res.hack.split("\n").filter(Boolean) : [];
      hackTbody.innerHTML = lines.map((bin, idx) => {
        const hex = "0x" + parseInt(bin, 2).toString(16).toUpperCase().padStart(4, "0");
        return `<tr><td class="num">${idx}</td><td><code>${bin}</code></td><td class="num">${hex}</td></tr>`;
      }).join("");
    }

    const predefined = new Set(["SP","LCL","ARG","THIS","THAT","SCREEN","KBD","R0","R1","R2","R3","R4","R5","R6","R7","R8","R9","R10","R11","R12","R13","R14","R15"]);
    const labels = new Set(Object.keys(res.labels || {}));
    const entries = Object.entries(res.symbols || {});
    symTbody.innerHTML = entries.map(([name, addr]) => {
      const kind = predefined.has(name) ? "Predefined" : (labels.has(name) ? "ROM Label" : "RAM Var");
      return `<tr><td><code>${name}</code></td><td class="num">${addr}</td><td>${kind}</td></tr>`;
    }).join("");
  }

  async function runPythonAssemble(asmText, kVal) {
    const btn = document.getElementById("btn-assemble");
    btn.disabled = true;
    btn.textContent = "Assembling...";
    try {
      let data;
      try {
        const resp = await fetch("/api/assemble", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ asm: asmText, k: kVal }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        data = await resp.json();
      } catch (_) {
        data = window.HackStaticEngine.assemble(asmText, kVal);
      }
      renderAssemblerOutput(data);
    } catch (err) {
      renderAssemblerOutput({ ok: false, errors: [`Assembler error: ${err.message}`], symbols: {}, warnings: [] });
    } finally {
      btn.disabled = false;
      btn.textContent = "Assemble with Python";
    }
  }

  document.getElementById("btn-assemble").addEventListener("click", () => {
    const asmText = document.getElementById("asm-editor").value;
    const kVal = Number(document.getElementById("asm-k-input").value || 51);
    runPythonAssemble(asmText, kVal);
  });

  document.getElementById("btn-load-sim").addEventListener("click", () => {
    if (state.lastAssembled && state.lastAssembled.ok && state.lastAssembled.romWords) {
      state.cpu.reset(state.lastAssembled.romWords);
      setActiveTab("simulator");
    }
  });

  document.getElementById("preset-box").addEventListener("click", () => {
    if (!state.project) return;
    document.getElementById("asm-editor").value = state.project.programs.boxAsm;
    document.getElementById("asm-k-input").value = "51";
    runPythonAssemble(state.project.programs.boxAsm, 51);
  });

  document.getElementById("preset-add").addEventListener("click", () => {
    if (!state.project) return;
    document.getElementById("asm-editor").value = state.project.programs.addAsm;
    document.getElementById("asm-k-input").value = "51";
    runPythonAssemble(state.project.programs.addAsm, 51);
  });

  document.getElementById("preset-bad").addEventListener("click", () => {
    const bad = "@10\nD=A\nINVALID_MNEMONIC\n@20\nM=D\n";
    document.getElementById("asm-editor").value = bad;
    document.getElementById("asm-k-input").value = "52";
    runPythonAssemble(bad, 52);
  });

  document.getElementById("preset-dup").addEventListener("click", () => {
    const dup = "(LOOP)\n@1\n(LOOP)\n@LOOP\n0;JMP\n";
    document.getElementById("asm-editor").value = dup;
    document.getElementById("asm-k-input").value = "53";
    runPythonAssemble(dup, 53);
  });

  // HDL Tab
  const hdlButtons = Array.from(document.querySelectorAll("[data-hdl]"));
  hdlButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      hdlButtons.forEach((b) => b.classList.remove("btn--selected"));
      btn.classList.add("btn--selected");
      const name = btn.dataset.hdl;
      document.getElementById("hdl-file-chip").textContent = name;
      if (state.project && state.project.hdl[name] !== undefined) {
        document.getElementById("hdl-source-view").textContent = state.project.hdl[name];
      }
    });
  });

  document.getElementById("btn-run-verify").addEventListener("click", async () => {
    const btn = document.getElementById("btn-run-verify");
    const banner = document.getElementById("verify-banner");
    const tbody = document.getElementById("verify-tbody");
    btn.disabled = true;
    btn.textContent = "Running tests...";
    banner.className = "message-banner";
    banner.textContent = "Executing verify_capstone.py suite...";

    try {
      let data;
      try {
        const resp = await fetch("/api/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ k: 51 }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        data = await resp.json();
      } catch (_) {
        data = window.HackStaticEngine.verifyInBrowser(state.project, 51, HackBrowserCPU);
      }
      banner.className = data.ok ? "message-banner is-success" : "message-banner is-error";
      banner.textContent = data.ok
        ? "All verification checks passed."
        : "One or more verification checks failed.";
      tbody.innerHTML = data.checks.map((chk) => (
        `<tr><td>${chk.name}</td><td>${chk.passed ? "PASSED" : "FAILED"}</td><td>${chk.detail}</td></tr>`
      )).join("");
    } catch (err) {
      banner.className = "message-banner is-error";
      banner.textContent = `Verification request failed: ${err.message}`;
    } finally {
      btn.disabled = false;
      btn.textContent = "Run Verification Suite";
    }
  });

  // Viva & K Calculator Tab
  const vivaInput = document.getElementById("viva-k-input");
  vivaInput.addEventListener("input", () => {
    const kVal = Math.max(0, Math.min(235, Number(vivaInput.value || 0)));
    updateParameterDisplays(kVal);
  });

  async function applyKToSimulator(kVal) {
    const btn = document.getElementById("btn-apply-k");
    btn.disabled = true;
    try {
      let data;
      try {
        const resp = await fetch("/api/generate-box", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ k: kVal }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        data = await resp.json();
      } catch (_) {
        data = window.HackStaticEngine.generateBox(kVal);
      }
      if (data.ok && data.assembled) {
        updateParameterDisplays(kVal);
        document.getElementById("asm-editor").value = data.asm;
        document.getElementById("asm-k-input").value = String(kVal);
        renderAssemblerOutput(data.assembled);
        state.cpu.reset(data.assembled.romWords);
        setActiveTab("simulator");
      }
    } finally {
      btn.disabled = false;
    }
  }

  document.getElementById("btn-apply-k").addEventListener("click", () => {
    const kVal = Math.max(0, Math.min(235, Number(vivaInput.value || 51)));
    applyKToSimulator(kVal);
  });

  document.getElementById("btn-viva-shift").addEventListener("click", () => {
    const current = Number(vivaInput.value || 51);
    const shifted = Math.min(235, current + 10);
    vivaInput.value = String(shifted);
    applyKToSimulator(shifted);
  });

  document.getElementById("btn-sim-shift").addEventListener("click", () => {
    const shifted = Math.min(235, state.k + 10);
    vivaInput.value = String(shifted);
    applyKToSimulator(shifted);
  });

  document.getElementById("btn-sim-reset-k").addEventListener("click", () => {
    vivaInput.value = "51";
    applyKToSimulator(51);
  });

  // Checklist counter
  const checkboxes = Array.from(document.querySelectorAll("#submission-checklist input[type='checkbox']"));
  function updateChecklistCount() {
    const done = checkboxes.filter((c) => c.checked).length;
    document.getElementById("checklist-count").textContent = `${done} / ${checkboxes.length} Ready`;
  }
  checkboxes.forEach((c) => c.addEventListener("change", updateChecklistCount));
  updateChecklistCount();

  // Export live canvas PNG
  document.getElementById("btn-export-png").addEventListener("click", () => {
    const link = document.createElement("a");
    link.download = `hack_screen_K${state.k}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  });

  // Boot: load real project files from Python backend (or static project_data.json on GitHub Pages)
  async function loadProject() {
    let proj;
    let isStaticMode = false;
    try {
      const resp = await fetch("/api/project-data");
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      proj = await resp.json();
    } catch (_) {
      isStaticMode = true;
      const resp = await fetch("./project_data.json");
      proj = await resp.json();
    }
    state.project = proj;

    document.getElementById("asm-editor").value = proj.programs.boxAsm;
    document.getElementById("hdl-source-view").textContent = proj.hdl["Memory.hdl"] || "";

    // Populate downloads table
    document.getElementById("files-tbody").innerHTML = proj.files.map((f) => {
      const kb = f.exists ? `${f.sizeBytes.toLocaleString()} B` : "Missing";
      const dlName = f.name.split("/").pop();
      const href = "./" + f.name.split("/").map(encodeURIComponent).join("/");
      const action = f.exists
        ? `<a class="btn" href="${href}" download="${dlName}">Download</a>`
        : "Unavailable";
      return `<tr><td><code>${f.name}</code></td><td class="num">${kb}</td><td>${action}</td></tr>`;
    }).join("");

    // Initial assemble + boot CPU with Box.hack
    let asmData;
    if (isStaticMode) {
      asmData = window.HackStaticEngine.assemble(proj.programs.boxAsm, 51);
    } else {
      try {
        const initialAsm = await fetch("/api/assemble", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ asm: proj.programs.boxAsm, k: 51 }),
        });
        if (!initialAsm.ok) throw new Error(`HTTP ${initialAsm.status}`);
        asmData = await initialAsm.json();
      } catch (_) {
        asmData = window.HackStaticEngine.assemble(proj.programs.boxAsm, 51);
      }
    }
    renderAssemblerOutput(asmData);

    updateParameterDisplays(51);
    state.cpu.reset(proj.programs.boxRomWords);
    window.requestAnimationFrame(frameLoop);
  }

  loadProject();
})();
