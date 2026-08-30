"""Parse COBOL copybooks and convert fixed-width records to/from Python values."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

_FIELD_RE = re.compile(
    r"^\s*05\s+(?P<name>[A-Z0-9-]+)\s+PIC\s+(?P<pic>.+?)\.\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Field:
    name: str
    kind: str
    length: int
    offset: int
    integer_digits: int = 0
    decimal_digits: int = 0
    signed: bool = False
    sign_separate: bool = False

    @property
    def end(self) -> int:
        return self.offset + self.length


@dataclass(frozen=True)
class Copybook:
    name: str
    record_name: str
    fields: tuple[Field, ...]
    record_length: int

    def field(self, name: str) -> Field:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)


def parse_pic(pic: str) -> dict[str, Any]:
    pic = " ".join(pic.upper().split())
    sign_separate = "SIGN IS LEADING SEPARATE" in pic or "SIGN LEADING SEPARATE" in pic
    pic = pic.replace("SIGN IS LEADING SEPARATE", "").replace("SIGN LEADING SEPARATE", "").strip()

    if pic.startswith("X"):
        return {
            "kind": "string",
            "length": _repeat_count(pic),
            "integer_digits": 0,
            "decimal_digits": 0,
            "signed": False,
            "sign_separate": False,
        }

    signed = pic.startswith("S")
    if signed:
        pic = pic[1:]

    match = re.fullmatch(r"9(?:\((\d+)\))?(?:V9\((\d+)\)|V(9+))?", pic)
    if not match:
        raise ValueError(f"Unsupported PIC clause: {pic}")

    integer_digits = int(match.group(1) or 1)
    if match.group(2) is not None:
        decimal_digits = int(match.group(2))
    elif match.group(3) is not None:
        decimal_digits = len(match.group(3))
    else:
        decimal_digits = 0

    length = integer_digits + decimal_digits + (1 if sign_separate else 0)
    kind = "decimal" if decimal_digits else "integer"
    return {
        "kind": kind,
        "length": length,
        "integer_digits": integer_digits,
        "decimal_digits": decimal_digits,
        "signed": signed,
        "sign_separate": sign_separate,
    }


def _repeat_count(pic: str) -> int:
    match = re.fullmatch(r"[X9](?:\((\d+)\))?", pic)
    if not match:
        raise ValueError(f"Unsupported PIC clause: {pic}")
    return int(match.group(1) or 1)


def load_copybook(path: Path) -> Copybook:
    record_name = path.stem
    fields: list[Field] = []
    offset = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("*>", 1)[0].rstrip()
        if "01 " in line and "PIC" not in line.upper():
            match = re.search(r"01\s+([A-Z0-9-]+)", line, re.IGNORECASE)
            if match:
                record_name = match.group(1).upper()
        match = _FIELD_RE.match(line)
        if not match:
            continue
        spec = parse_pic(match.group("pic"))
        field = Field(name=match.group("name").upper(), offset=offset, **spec)
        fields.append(field)
        offset += field.length
    if not fields:
        raise ValueError(f"No 05 fields found in {path}")
    return Copybook(
        name=path.stem.upper(),
        record_name=record_name,
        fields=tuple(fields),
        record_length=offset,
    )


def money(value: Decimal | int | str | float) -> Decimal:
    quantized = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return quantized


def format_field(field: Field, value: Any) -> str:
    if field.kind == "string":
        return str(value).ljust(field.length)[: field.length]
    if field.kind == "integer":
        number = int(value)
        return str(abs(number)).zfill(field.length)

    decimal_value = money(value) if field.decimal_digits == 2 else Decimal(str(value))
    scale = 10 ** field.decimal_digits
    scaled = int((decimal_value * scale).to_integral_value(rounding=ROUND_HALF_EVEN))
    sign = ""
    if field.sign_separate:
        sign = "+" if scaled >= 0 else "-"
        scaled = abs(scaled)
    width = field.integer_digits + field.decimal_digits
    return f"{sign}{str(scaled).zfill(width)}"


def parse_field(field: Field, raw: str) -> Any:
    raw = raw.ljust(field.length)
    if field.kind == "string":
        return raw.rstrip()
    if field.kind == "integer":
        return int(raw)

    text = raw
    sign = 1
    if field.sign_separate:
        sign = -1 if text[0] == "-" else 1
        text = text[1:]
    scaled = int(text)
    value = Decimal(scaled) / (10 ** field.decimal_digits)
    return sign * value


def format_record(copybook: Copybook, values: dict[str, Any]) -> str:
    chunks: list[str] = []
    for field in copybook.fields:
        key = field.name
        alt = key.lower().replace("-", "_")
        if key not in values and alt not in values:
            raise KeyError(f"Missing field {field.name}")
        value = values.get(key, values.get(alt))
        chunks.append(format_field(field, value))
    record = "".join(chunks)
    if len(record) != copybook.record_length:
        raise ValueError(f"Record length {len(record)} != {copybook.record_length}")
    return record


def parse_record(copybook: Copybook, line: str) -> dict[str, Any]:
    padded = line.rstrip("\n").ljust(copybook.record_length)
    parsed: dict[str, Any] = {}
    for field in copybook.fields:
        parsed[field.name] = parse_field(field, padded[field.offset : field.end])
    return parsed


def read_records(copybook: Copybook, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(parse_record(copybook, line))
    return records


def write_records(copybook: Copybook, path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [format_record(copybook, row) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def pythonize(record: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in record.items():
        py_key = key.lower().replace("-", "_")
        if isinstance(value, Decimal):
            out[py_key] = str(value)
        else:
            out[py_key] = value
    return out
