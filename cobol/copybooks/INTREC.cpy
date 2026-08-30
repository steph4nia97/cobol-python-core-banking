>>SOURCE FORMAT FREE
*> Interest applied this cycle (22 bytes)
*> Offset  Len  Field
*>      1   10  INT-ACCT-ID
*>     11   12  INT-AMOUNT     S9(09)V99 leading separate
01 INTEREST-RECORD.
    05 INT-ACCT-ID          PIC X(10).
    05 INT-AMOUNT           PIC S9(09)V99 SIGN IS LEADING SEPARATE.
