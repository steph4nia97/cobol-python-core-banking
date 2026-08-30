>>SOURCE FORMAT FREE
*> Transaction record (71 bytes)
*> Offset  Len  Field
*>      1   10  TXN-ACCT-ID
*>     11    8  TXN-DATE       YYYYMMDD
*>     19    1  TXN-TYPE       C=credit D=debit
*>     20   12  TXN-AMOUNT     S9(09)V99 leading separate
*>     32   40  TXN-DESC
01 TRANSACTION-RECORD.
    05 TXN-ACCT-ID          PIC X(10).
    05 TXN-DATE             PIC 9(08).
    05 TXN-TYPE             PIC X(01).
        88 TXN-CREDIT        VALUE "C".
        88 TXN-DEBIT        VALUE "D".
    05 TXN-AMOUNT           PIC S9(09)V99 SIGN IS LEADING SEPARATE.
    05 TXN-DESC             PIC X(40).
