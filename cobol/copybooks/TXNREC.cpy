>>SOURCE FORMAT FREE
*> Transaction record (91 bytes)
*> Offset  Len  Field
*>      1   20  TXN-ID         TXN-YYYYMMDD-NNNNNN
*>     21   10  TXN-ACCT-ID
*>     31    8  TXN-DATE       YYYYMMDD
*>     39    1  TXN-TYPE       C=credit D=debit
*>     40   12  TXN-AMOUNT
*>     52   40  TXN-DESC
01 TRANSACTION-RECORD.
    05 TXN-ID               PIC X(20).
    05 TXN-ACCT-ID          PIC X(10).
    05 TXN-DATE             PIC 9(08).
    05 TXN-TYPE             PIC X(01).
        88 TXN-CREDIT        VALUE "C".
        88 TXN-DEBIT        VALUE "D".
    05 TXN-AMOUNT           PIC S9(09)V99 SIGN IS LEADING SEPARATE.
    05 TXN-DESC             PIC X(40).
