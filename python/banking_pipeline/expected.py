"""Documented sample figures. Tests fail if README, seed, or oracle drift apart."""

from decimal import Decimal

# Mental-math trap: 5% of 100_000 is not Lucia's coupon.
FIVE_PERCENT_ON_100K = Decimal("416.67")

MARIA_ID = "1000000001"
MARIA_RATE = Decimal("0.0500")
MARIA_POSTED = Decimal("15300.00")
MARIA_INTEREST = Decimal("63.75")
MARIA_FINAL = Decimal("15363.75")

LUCIA_ID = "1000000005"
LUCIA_RATE = Decimal("0.0425")
LUCIA_POSTED = Decimal("100000.00")
LUCIA_INTEREST = Decimal("354.17")
LUCIA_FINAL = Decimal("100354.17")

README_MARKERS = (
    "5.00%",
    "4.25%",
    "416.67",
    "354.17",
    "15,363.75",
    "100,354.17",
)
