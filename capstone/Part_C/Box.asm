// ==================================================================
// Capstone Project: Box.asm
// Course: Nand to Tetris - I (ETCNTC301)
// School of Engineering & Technology, K.R. Mangalam University
//
// Student Name            : Priyanshu Pandey
// Roll Number             : 2501730051
// Personal Number K       : 51
// Starting Row            : 51 (rows 51 to 70)
// Box Height              : 20 rows
// Box Width               : 64 pixels (4 16-bit words/row)
// Screen Base Address     : SCREEN + 32 * 51 = 16384 + 1632 = 18016
// ==================================================================

// Main polling loop and box setup in Box.asm (K = 51)
(MAIN_LOOP)
    @KBD
    D=M
    @DRAW_BOX
    D;JNE       // Draw box if any key is pressed
    @CLEAR_BOX
    0;JMP       // Clear box if no key is pressed

(DRAW_BOX)
    @18016
    D=A
    @rowAddr
    M=D         // Start at row 51 (16384 + 32 * 51)
    @20
    D=A
    @rowCount
    M=D         // Repeat for 20 rows

(DRAW_ROW_LOOP)
    @rowCount
    D=M
    @MAIN_LOOP
    D;JEQ       // Return to polling once all rows are drawn

    @rowAddr
    D=M
    @wordAddr
    M=D         // Reset wordAddr = rowAddr at the start of every row

    @4
    D=A
    @wordCount
    M=D         // 4 word(s) across (64 pixels)

(DRAW_WORD_LOOP)
    @wordCount
    D=M
    @DRAW_NEXT_ROW
    D;JEQ

    @wordAddr
    A=M
    M=-1        // Turn 16 pixels black (-1)

    @wordAddr
    M=M+1       // Advance to next word in row
    @wordCount
    M=M-1
    @DRAW_WORD_LOOP
    0;JMP

(DRAW_NEXT_ROW)
    @32
    D=A
    @rowAddr
    M=D+M       // Next row starts 32 words further down
    @rowCount
    M=M-1
    @DRAW_ROW_LOOP
    0;JMP

(CLEAR_BOX)
    @18016
    D=A
    @rowAddr
    M=D         // Start at row 51 (16384 + 32 * 51)
    @20
    D=A
    @rowCount
    M=D         // Repeat for 20 rows

(CLEAR_ROW_LOOP)
    @rowCount
    D=M
    @MAIN_LOOP
    D;JEQ       // Return to polling once all rows are cleared

    @rowAddr
    D=M
    @wordAddr
    M=D         // Reset wordAddr = rowAddr at the start of every row

    @4
    D=A
    @wordCount
    M=D         // 4 word(s) across (64 pixels)

(CLEAR_WORD_LOOP)
    @wordCount
    D=M
    @CLEAR_NEXT_ROW
    D;JEQ

    @wordAddr
    A=M
    M=0         // Clear 16 pixels back to white (0)

    @wordAddr
    M=M+1       // Advance to next word in row
    @wordCount
    M=M-1
    @CLEAR_WORD_LOOP
    0;JMP

(CLEAR_NEXT_ROW)
    @32
    D=A
    @rowAddr
    M=D+M       // Next row starts 32 words further down
    @rowCount
    M=M-1
    @CLEAR_ROW_LOOP
    0;JMP
