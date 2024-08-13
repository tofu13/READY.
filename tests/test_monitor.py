import pytest

from libs.hardware.constants import ASSEMBLER_REGEXES
from libs.hardware.monitor import convert, parse_assembly


@pytest.mark.parametrize(("argument", "addressing", "value"), [
    ("#$10", "IMM", "$10"),
    ("#$FF", "IMM", "$FF"),
    ("#FF", "IMM", "FF"),
    ("#+250", "IMM", "+250"),
    ("#&7654", "IMM", "&7654"),
    ("#%10101010", "IMM", "%10101010"),
    ("#$2b", "IMM", "$2b"),
    ("#$A", "IMM", "$A"),
    ("$#10", None, None),
    ("#$1T", None, None),

    ("($1234)", "IND", "$1234"),
    ("($aBcD)", "IND", "$aBcD"),
    ("($4)", None, None),
    ("($42)", None, None),
    ("($42C)", None, None),

    ("$1234", "ABS", "$1234"),
    ("$aBcD", "ABS", "$aBcD"),
    ("$4", None, None),
    ("$4T", None, None),
    ("$423", None, None),

    ("$1234,X", "ABS_X", "$1234"),
    ("$1234,x", "ABS_X", "$1234"),
    ("$aBcD,X", "ABS_X", "$aBcD"),
    ("$123K,X", None, None),

    ("$1234,Y", "ABS_Y", "$1234"),
    ("$1234,y", "ABS_Y", "$1234"),
    ("$aBcD,Y", "ABS_Y", "$aBcD"),
    ("$$234,Y", None, None),

    ("$12", "ZP", "$12"),
    ("$aB", "ZP", "$aB"),

    ("$12,X", "ZP_X", "$12"),
    ("$aB,x", "ZP_X", "$aB"),
    ("$GB,x", None, None),

    ("$12,Y", "ZP_Y", "$12"),
    ("$aB,y", "ZP_Y", "$aB"),
    ("$aBC,y", None, None),

    ("($12,X)", "X_IND", "$12"),
    ("($aB,x)", "X_IND", "$aB"),
    ("$(aB,x)", None, None),

    ("($12),Y", "IND_Y", "$12"),
    ("($aB),y", "IND_Y", "$aB"),
    ("(aB),y", None, None),

])
def test_assembler_regexes(argument, addressing, value):
    for regex, my_addressing in ASSEMBLER_REGEXES.items():
        if (match := regex.match(argument)) is not None:
            assert addressing == my_addressing
            assert match.groups()[0] == value
            break
    else:
        assert addressing is None


@pytest.mark.parametrize(("value", "expected"), [
    ("$1A", 26),
    ("2c", 44),
    ("&112", 74),
    ("+235", 235),
    ("%10101010", 170),
    ("", None),
    ("rcgx", None),
    ("$ABCZ", None),
    ("%10101012", None),
    ("&9", None),
    ("+OOOO", None),
])
def test_convert(value, expected):
    assert convert(value) == expected


@pytest.mark.parametrize(("line", "expected"), [
    ("ADC #$1A", [0x69, 0x1A]),
    ("ADC $1A", [0x65, 0x1A]),
    ("ADC $1A,X", [0x75, 0x1A]),
    ("ADC $D020", [0x6D, 0x20, 0xD0]),
    ("ADC $E021,X", [0x7D, 0x21, 0xE0]),
    ("ADC $F022,Y", [0x79, 0x22, 0xF0]),
    ("ADC ($F2,X)", [0x61, 0xF2]),
    ("ADC ($DE),Y", [0x71, 0xDE]),
    ("AND #$1A", [0x29, 0x1A]),
    ("AND $1A", [0x25, 0x1A]),
    ("AND $1A,X", [0x35, 0x1A]),
    ("AND $D020", [0x2D, 0x20, 0xD0]),
    ("AND $E021,X", [0x3D, 0x21, 0xE0]),
    ("AND $F022,Y", [0x39, 0x22, 0xF0]),
    ("AND ($F2,X)", [0x21, 0xF2]),
    ("AND ($DE),Y", [0x31, 0xDE]),
    ("ASL", [0x0A]),
    ("ASL $1A", [0x06, 0x1A]),
    ("ASL $1A,X", [0x16, 0x1A]),
    ("ASL $D020", [0x0E, 0x20, 0xD0]),
    ("ASL $E021,X", [0x1E, 0x21, 0xE0]),
    ("BCC $C810", [0x90, 0x0E]),
    ("BCC $C7E0", [0x90, 0xDE]),
    ("BCS $C810", [0xB0, 0x0E]),
    ("BCS $C7E0", [0xB0, 0xDE]),
    ("BEQ $C810", [0xF0, 0x0E]),
    ("BEQ $C7E0", [0xF0, 0xDE]),
    ("BIT $AB", [0x24, 0xAB]),
    ("BIT $ABCD", [0x2C, 0xCD, 0xAB]),
    ("BMI $C810", [0x30, 0x0E]),
    ("BMI $C7E0", [0x30, 0xDE]),
    ("BPL $C810", [0x10, 0x0E]),
    ("BPL $C7E0", [0x10, 0xDE]),
    ("BRK", [0x00]),
    ("BVC $C7E0", [0x50, 0xDE]),
    ("BVS $C7E0", [0x70, 0xDE]),
    ("CLC", [0x18]),
    ("CLD", [0xD8]),
    ("CLI", [0x58]),
    ("CLV", [0xB8]),
    ("CMP #$1A", [0xC9, 0x1A]),
    ("CMP $1A", [0xC5, 0x1A]),
    ("CMP $1A,X", [0xD5, 0x1A]),
    ("CMP $D020", [0xCD, 0x20, 0xD0]),
    ("CMP $E021,X", [0xDD, 0x21, 0xE0]),
    ("CMP $F022,Y", [0xD9, 0x22, 0xF0]),
    ("CMP ($F2,X)", [0xC1, 0xF2]),
    ("CMP ($DE),Y", [0xD1, 0xDE]),
    ("CPX #$1A", [0xE0, 0x1A]),
    ("CPX $1A", [0xE4, 0x1A]),
    ("CPX $D020", [0xEC, 0x20, 0xD0]),
    ("CPY #$1A", [0xC0, 0x1A]),
    ("CPY $1A", [0xC4, 0x1A]),
    ("CPY $D020", [0xCC, 0x20, 0xD0]),
    ("DEC $1A", [0xC6, 0x1A]),
    ("DEC $1A,X", [0xD6, 0x1A]),
    ("DEC $D020", [0xCE, 0x20, 0xD0]),
    ("DEC $E021,X", [0xDE, 0x21, 0xE0]),
    ("DEX", [0xCA]),
    ("DEY", [0x88]),
    ("EOR #$1A", [0x49, 0x1A]),
    ("EOR $1A", [0x45, 0x1A]),
    ("EOR $1A,X", [0x55, 0x1A]),
    ("EOR $D020", [0x4D, 0x20, 0xD0]),
    ("EOR $E021,X", [0x5D, 0x21, 0xE0]),
    ("EOR $F022,Y", [0x59, 0x22, 0xF0]),
    ("EOR ($F2,X)", [0x41, 0xF2]),
    ("EOR ($DE),Y", [0x51, 0xDE]),
    ("INC $1A", [0xE6, 0x1A]),
    ("INC $1A,X", [0xF6, 0x1A]),
    ("INC $D020", [0xEE, 0x20, 0xD0]),
    ("INC $E021,X", [0xFE, 0x21, 0xE0]),
    ("INX", [0xE8]),
    ("INY", [0xC8]),
    ("JMP $FEDC", [0x4C, 0xDC, 0xFE]),
    ("JMP ($C1A0)", [0x6C, 0xA0, 0xC1]),
    ("JSR $F00C", [0x20, 0x0C, 0xF0]),
    ("LDA #$1A", [0xA9, 0x1A]),
    ("LDA $1A", [0xA5, 0x1A]),
    ("LDA $1A,X", [0xB5, 0x1A]),
    ("LDA $D020", [0xAD, 0x20, 0xD0]),
    ("LDA $E021,X", [0xBD, 0x21, 0xE0]),
    ("LDA $F022,Y", [0xB9, 0x22, 0xF0]),
    ("LDA ($F2,X)", [0xA1, 0xF2]),
    ("LDA ($DE),Y", [0xB1, 0xDE]),
    ("LDX #$1A", [0xA2, 0x1A]),
    ("LDX $1A", [0xA6, 0x1A]),
    ("LDX $1A,Y", [0xB6, 0x1A]),
    ("LDX $D020", [0xAE, 0x20, 0xD0]),
    ("LDX $F022,Y", [0xBE, 0x22, 0xF0]),
    ("LDY #$1A", [0xA0, 0x1A]),
    ("LDY $1A", [0xA4, 0x1A]),
    ("LDY $1A,X", [0xB4, 0x1A]),
    ("LDY $D020", [0xAC, 0x20, 0xD0]),
    ("LDY $F022,X", [0xBC, 0x22, 0xF0]),
    ("LSR", [0x4A]),
    ("LSR $1A", [0x46, 0x1A]),
    ("LSR $1A,X", [0x56, 0x1A]),
    ("LSR $D020", [0x4E, 0x20, 0xD0]),
    ("LSR $E021,X", [0x5E, 0x21, 0xE0]),
    ("NOP", [0xEA]),
    ("ORA #$1A", [0x09, 0x1A]),
    ("ORA $1A", [0x05, 0x1A]),
    ("ORA $1A,X", [0x15, 0x1A]),
    ("ORA $D020", [0x0D, 0x20, 0xD0]),
    ("ORA $E021,X", [0x1D, 0x21, 0xE0]),
    ("ORA $F022,Y", [0x19, 0x22, 0xF0]),
    ("ORA ($F2,X)", [0x01, 0xF2]),
    ("ORA ($DE),Y", [0x11, 0xDE]),
    ("PHA", [0x48]),
    ("PHP", [0x08]),
    ("PLA", [0x68]),
    ("PLP", [0x28]),
    ("ROL", [0x2A]),
    ("ROL $1A", [0x26, 0x1A]),
    ("ROL $1A,X", [0x36, 0x1A]),
    ("ROL $D020", [0x2E, 0x20, 0xD0]),
    ("ROL $E021,X", [0x3E, 0x21, 0xE0]),
    ("ROR", [0x6A]),
    ("ROR $1A", [0x66, 0x1A]),
    ("ROR $1A,X", [0x76, 0x1A]),
    ("ROR $D020", [0x6E, 0x20, 0xD0]),
    ("ROR $E021,X", [0x7E, 0x21, 0xE0]),
    ("RTI", [0x40]),
    ("RTS", [0x60]),
    ("SBC #$1A", [0xE9, 0x1A]),
    ("SBC $1A", [0xE5, 0x1A]),
    ("SBC $1A,X", [0xF5, 0x1A]),
    ("SBC $D020", [0xED, 0x20, 0xD0]),
    ("SBC $E021,X", [0xFD, 0x21, 0xE0]),
    ("SBC $F022,Y", [0xF9, 0x22, 0xF0]),
    ("SBC ($F2,X)", [0xE1, 0xF2]),
    ("SBC ($DE),Y", [0xF1, 0xDE]),
    ("SEC", [0x38]),
    ("SED", [0xF8]),
    ("SEI", [0x78]),
    ("STA $1A", [0x85, 0x1A]),
    ("STA $1A,X", [0x95, 0x1A]),
    ("STA $D020", [0x8D, 0x20, 0xD0]),
    ("STA $E021,X", [0x9D, 0x21, 0xE0]),
    ("STA $F022,Y", [0x99, 0x22, 0xF0]),
    ("STA ($F2,X)", [0x81, 0xF2]),
    ("STA ($DE),Y", [0x91, 0xDE]),
    ("STX $1A", [0x86, 0x1A]),
    ("STX $1A,Y", [0x96, 0x1A]),
    ("STX $D020", [0x8E, 0x20, 0xD0]),
    ("STY $1A", [0x84, 0x1A]),
    ("STY $1A,X", [0x94, 0x1A]),
    ("STY $D020", [0x8C, 0x20, 0xD0]),
    ("TAX", [0XAA]),
    ("TAY", [0XA8]),
    ("TSX", [0XBA]),
    ("TXA", [0X8A]),
    ("TXS", [0X9A]),
    ("TYA", [0X98]),
])
def test_parse_assembly(line, expected):
    assert parse_assembly(line.split(), 0xC800) == expected
