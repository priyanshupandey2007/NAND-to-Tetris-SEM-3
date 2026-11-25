// ComputerAdd.tst
load Computer.hdl,
output-file ComputerAdd.out,
compare-to ComputerAdd.cmp,
output-list time%S0.4.1 reset%B2.1.2 ARegister[]%D1.7.1 DRegister[]%D1.7.1;

// Load Add.hack into ROM32K
ROM32K load Add.hack,

// Reset execution
set reset 1,
tick, tock, output;

set reset 0,
repeat 6 {
    tick, tock, output;
}
