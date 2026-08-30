>>SOURCE FORMAT FREE
*> Account master record (61 bytes)
*> Offset  Len  Field
*>      1   10  ACCT-ID
*>     11   30  ACCT-NAME
*>     41    1  ACCT-TYPE     C=checking S=savings
*>     42    1  ACCT-STATUS    A=active C=closed
*>     43   14  ACCT-BALANCE   S9(11)V99 leading separate
*>     57    5  ACCT-RATE      9(01)V9(04) annual rate
01 ACCOUNT-RECORD.
    05 ACCT-ID              PIC X(10).
    05 ACCT-NAME            PIC X(30).
    05 ACCT-TYPE            PIC X(01).
        88 ACCT-CHECKING    VALUE "C".
        88 ACCT-SAVINGS     VALUE "S".
    05 ACCT-STATUS          PIC X(01).
        88 ACCT-ACTIVE      VALUE "A".
        88 ACCT-CLOSED      VALUE "C".
    05 ACCT-BALANCE         PIC S9(11)V99 SIGN IS LEADING SEPARATE.
    05 ACCT-RATE            PIC 9(01)V9(04).
