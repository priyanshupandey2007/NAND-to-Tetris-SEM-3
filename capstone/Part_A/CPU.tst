// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/05/CPU.tst

load CPU.hdl,
output-file CPU.out,
compare-to CPU.cmp,
output-list time%S0.4.1 inM%B1.16.1 instruction%B1.16.1 reset%B2.1.2 outM%B1.16.1 writeM%B2.1.2 addressM%D1.15.1 pc%D1.15.1;

// Load A with 12345
set inM 0,
set instruction %B0011000000111001,
set reset 0,
tick, tock, output;

// D = A
set instruction %B1110110000010000,
tick, tock, output;

// Load A with 23456
set instruction %B0101101110100000,
tick, tock, output;

// D = D - A
set instruction %B1110010011010000,
tick, tock, output;

// If D < 0 jump to 12345
set instruction %B0011000000111001,
tick, tock, output;

set instruction %B1110001100000100,
tick, tock, output;

// Jump
tick, tock, output;

// Reset
set reset 1,
tick, tock, output;
