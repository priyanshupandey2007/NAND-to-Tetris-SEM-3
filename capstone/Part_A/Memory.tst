// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/05/Memory.tst

load Memory.hdl,
output-file Memory.out,
compare-to Memory.cmp,
output-list time%S0.4.1 in%D1.7.1 load%B2.1.2 address%D1.5.1 out%D1.7.1;

// RAM[0] = 333
set in 333,
set load 1,
set address 0,
tick, tock, output;

// Read RAM[0]
set in 0,
set load 0,
set address 0,
tick, tock, output;

// Screen[0] = 444
set in 444,
set load 1,
set address 16384,
tick, tock, output;

// Read Screen[0]
set in 0,
set load 0,
set address 16384,
tick, tock, output;

// Keyboard test (address 24576)
set address 24576,
tick, tock, output;
