>>SOURCE FORMAT FREE
*> Posting journal (119 bytes) — one row per successful credit/debit
01 JOURNAL-RECORD.
    05 JRN-TXN-ID           PIC X(20).
    05 JRN-ACCT-ID          PIC X(10).
    05 JRN-DATE             PIC 9(08).
    05 JRN-TYPE             PIC X(01).
        88 JRN-CREDIT        VALUE "C".
        88 JRN-DEBIT        VALUE "D".
    05 JRN-AMOUNT           PIC S9(09)V99 SIGN IS LEADING SEPARATE.
    05 JRN-BAL-BEFORE        PIC S9(11)V99 SIGN IS LEADING SEPARATE.
    05 JRN-BAL-AFTER         PIC S9(11)V99 SIGN IS LEADING SEPARATE.
    05 JRN-DESC             PIC X(40).
