>>SOURCE FORMAT FREE
*> Monthly statement extract (76 bytes)
*> Offset  Len  Field
*>      1   10  STMT-ACCT-ID
*>     11   30  STMT-NAME
*>     41    1  STMT-TYPE
*>     42    1  STMT-STATUS
*>     43   14  STMT-BALANCE
*>     57   12  STMT-INTEREST
*>     69    8  STMT-DATE      YYYYMMDD
01 STATEMENT-RECORD.
    05 STMT-ACCT-ID         PIC X(10).
    05 STMT-NAME            PIC X(30).
    05 STMT-TYPE            PIC X(01).
    05 STMT-STATUS          PIC X(01).
    05 STMT-BALANCE         PIC S9(11)V99 SIGN IS LEADING SEPARATE.
    05 STMT-INTEREST        PIC S9(09)V99 SIGN IS LEADING SEPARATE.
    05 STMT-DATE            PIC 9(08).
