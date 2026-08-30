>>SOURCE FORMAT FREE
*> Exception / reject record (76 bytes)
*> Offset  Len  Field
*>      1   10  EXC-ACCT-ID
*>     11    4  EXC-CODE
*>     15   50  EXC-MESSAGE
*>     65   12  EXC-AMOUNT     S9(09)V99 leading separate
01 EXCEPTION-RECORD.
    05 EXC-ACCT-ID          PIC X(10).
    05 EXC-CODE             PIC X(04).
        88 EXC-NOT-FOUND    VALUE "NFND".
        88 EXC-CLOSED        VALUE "CLSD".
        88 EXC-NSF          VALUE "NSF ".
        88 EXC-BAD-TYPE     VALUE "ITYP".
        88 EXC-BAD-AMT      VALUE "IAMT".
    05 EXC-MESSAGE          PIC X(50).
    05 EXC-AMOUNT           PIC S9(09)V99 SIGN IS LEADING SEPARATE.
