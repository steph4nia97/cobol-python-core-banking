>>SOURCE FORMAT FREE
*> Exception / reject record (96 bytes)
01 EXCEPTION-RECORD.
    05 EXC-TXN-ID           PIC X(20).
    05 EXC-ACCT-ID          PIC X(10).
    05 EXC-CODE             PIC X(04).
        88 EXC-NOT-FOUND    VALUE "NFND".
        88 EXC-CLOSED        VALUE "CLSD".
        88 EXC-NSF          VALUE "NSF ".
        88 EXC-BAD-TYPE     VALUE "ITYP".
        88 EXC-BAD-AMT      VALUE "IAMT".
        88 EXC-DUPLICATE    VALUE "DUP ".
    05 EXC-MESSAGE          PIC X(50).
    05 EXC-AMOUNT           PIC S9(09)V99 SIGN IS LEADING SEPARATE.
