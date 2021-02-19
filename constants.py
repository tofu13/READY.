from enum import Enum, auto


class ADDRESSING_MODE(Enum):
    _ = auto()
    A = auto()
    IMM = auto() # next word as literal
    REL = auto() # next word as signed integer
    ABS = auto()  # get next 16 bits as address
    ZP = auto() # get next 8 bits as address for zeroth memory page
    ABS_X = auto() # as with ABS but add X to address
    ABS_Y = auto() # as with ABS but add Y to address
    ZP_X = auto() # as with ZP but add X to address
    ZP_Y = auto() # as with ZP but add Y to address
    IND = auto() # Use next word as zero-page addr and the following byte from that zero page
    # as another 8 bits, and combine the two into a 16-bit address
    IND_X = auto() # As with the above, but add X to the ZP
    IND_Y = auto() # As with the above, but add Y to the


ADDRESSING_METHODS = [
    "None",
    "A",
    "IMM",
    "REL",
    "ABS",
    "ZP",
    "ABS_X",
    "ABS_Y",
    "ZP_X",
    "ZP_Y",
    "IND",
    "IND_X"
    "IND_Y"
]

OPCODES = {
    0x00: ("BRK", None),
    0x01: ("ORA", "IND_X"),
    0x02: None,
    0x03: None,  # ("SLO", "IND_X"),
    0x04: ("NOP", "ZP"),
    0x05: ("ORA", "ZP"),
    0x06: ("ASL", "ZP"),
    0x07: None,  # ("SLO", "ZP"),
    0x08: ("PHP", None),
    0x09: ("ORA", "IMM"),
    0x0a: ("ASL", None),
    0x0b: None,  # ("ANC", "IMM"),
    0x0c: ("NOP", "ABS"),
    0x0d: ("ORA", "ABS"),
    0x0e: ("ASL", "ABS"),
    0x0f: None,  # ("SLO", "ABS"),

    0x10: ("BPL", "REL"),
    0x11: ("ORA", "IND_Y"),
    0x12: None,
    0x13: None,  # ("SLO", "IND_Y"),
    0x14: ("NOP", "ZP_X"),
    0x15: ("ORA", "ZP_X"),
    0x16: ("ASL", "ZP_X"),
    0x17: None,  # ("SLO", "ZP_X"),
    0x18: ("CLC", None),
    0x19: ("ORA", "ABS_Y"),
    0x1a: ("NOP", None),
    0x1b: None,  # ("SLO", "ABS_Y"),
    0x1c: ("NOP", "ABS_X"),
    0x1d: ("ORA", "ABS_X"),
    0x1e: ("ASL", "ABS_X"),
    0x1f: None,  # ("SLO", "ABS_X"),

    0x20: ("JSR", "ABS"),
    0x21: ("AND", "IND_X"),
    0x22: None,
    0x23: ("RLA", "IND_X"),
    0x24: ("BIT", "ZP"),
    0x25: ("AND", "ZP"),
    0x26: ("ROL", "ZP"),
    0x27: ("RLA", "ZP"),
    0x28: ("PLP", None),
    0x29: ("AND", "IMM"),
    0x2a: ("ROL", None),
    0x2b: ("ANC", "IMM"),
    0x2c: ("BIT", "ABS"),
    0x2d: ("AND", "ABS"),
    0x2e: ("ROL", "ABS"),
    0x2f: ("RLA", "ABS"),

    0x30: ("BMI", "REL"),
    0x31: ("AND", "IND_Y"),
    0x32: None,
    0x33: ("RLA", "IND_Y"),
    0x34: ("NOP", "ZP_X"),
    0x35: ("AND", "ZP_X"),
    0x36: ("ROL", "ZP_X"),
    0x37: ("RLA", "ZP_X"),
    0x38: ("SEC", None),
    0x39: ("AND", "ABS_Y"),
    0x3a: ("NOP", None),
    0x3b: ("RLA", "ABS_Y"),
    0x3c: ("NOP", "ABS_X"),
    0x3d: ("AND", "ABS_X"),
    0x3e: ("ROL", "ABS_X"),
    0x3f: ("RLA", "ABS_X"),

    0x40: ("RTI", None),
    0x41: ("EOR", "IND_X"),
    0x42: None,
    0x43: ("SRE", "IND_X"),
    0x44: ("NOP", "ZP"),
    0x45: ("EOR", "ZP"),
    0x46: ("LSR", "ZP"),
    0x47: ("SRE", "ZP"),
    0x48: ("PHA", None),
    0x49: ("EOR", "IMM"),
    0x4a: ("LSR", None),
    0x4b: ("ALR", "IMM"),
    0x4c: ("JMP", "ABS"),
    0x4d: ("EOR", "ABS"),
    0x4e: ("LSR", "ABS"),
    0x4f: ("SRE", "ABS"),

    0x50: ("BVC", "REL"),
    0x51: ("EOR", "IND_Y"),
    0x52: None,
    0x53: ("SRE", "IND_Y"),
    0x54: ("NOP", "ZP_X"),
    0x55: ("EOR", "ZP_X"),
    0x56: ("LSR", "ZP_X"),
    0x57: ("SRE", "ZP_X"),
    0x58: ("CLI", None),
    0x59: ("EOR", "ABS_Y"),
    0x5a: ("NOP", None),
    0x5b: ("SRE", "ABS_Y"),
    0x5c: ("NOP", "ABS_X"),
    0x5d: ("EOR", "ABS_X"),
    0x5e: ("LSR", "ABS_X"),
    0x5f: ("SRE", "ABS_X"),

    0x60: ("RTS", None),
    0x61: ("ADC", "IND_X"),
    0x62: None,
    0x63: ("RRA", "IND_X"),
    0x64: ("NOP", "ZP"),
    0x65: ("ADC", "ZP"),
    0x66: ("ROR", "ZP"),
    0x67: ("RRA", "ZP"),
    0x68: ("PLA", None),
    0x69: ("ADC", "IMM"),
    0x6a: ("ROR", None),
    0x6b: ("ARR", "IMM"),
    0x6c: ("JMP", "IND"),
    0x6d: ("ADC", "ABS"),
    0x6e: ("ROR", "ABS"),
    0x6f: ("RRA", "ABS"),

    0x70: ("BVS", "REL"),
    0x71: ("ADC", "IND_Y"),
    0x72: None,
    0x73: ("RRA", "IND_Y"),
    0x74: ("NOP", "ZP_X"),
    0x75: ("ADC", "ZP_X"),
    0x76: ("ROR", "ZP_X"),
    0x77: ("RRA", "ZP_X"),
    0x78: ("SEI", None),
    0x79: ("ADC", "ABS_Y"),
    0x7a: ("NOP", None),
    0x7b: ("RRA", "ABS_Y"),
    0x7c: ("NOP", "ABS_X"),
    0x7d: ("ADC", "ABS_X"),
    0x7e: ("ROR", "ABS_X"),
    0x7f: ("RRA", "ABS_X"),

    0x80: ("NOP", "IMM"),
    0x81: ("STA", "IND_X"),
    0x82: ("NOP", "IMM"),
    0x83: ("SAX", "IND_X"),
    0x84: ("STY", "ZP"),
    0x85: ("STA", "ZP"),
    0x86: ("STX", "ZP"),
    0x87: ("SAX", "ZP"),
    0x88: ("DEY", None),
    0x89: ("NOP", "IMM"),
    0x8a: ("TXA", None),
    0x8b: ("XAA", "IMM"),
    0x8c: ("STY", "ABS"),
    0x8d: ("STA", "ABS"),
    0x8e: ("STX", "ABS"),
    0x8f: ("SAX", "ABS"),

    0x90: ("BCC", "REL"),
    0x91: ("STA", "IND_Y"),
    0x92: None,
    0x93: ("AHX", "IND_Y"),
    0x94: ("STY", "ZP_X"),
    0x95: ("STA", "ZP_X"),
    0x96: ("STX", "ZP_Y"),
    0x97: ("SAX", "ZP_Y"),
    0x98: ("TYA", None),
    0x99: ("STA", "ABS_Y"),
    0x9a: ("TXS", None),
    0x9b: ("TAS", "ABS_Y"),
    0x9c: ("SHY", "ABS_X"),
    0x9d: ("STA", "ABS_X"),
    0x9e: ("SHX", "ABS_X"),
    0x9f: ("AHX", "ABS_X"),

    0xa0: ("LDY", "IMM"),
    0xa1: ("LDA", "IND_X"),
    0xa2: ("LDX", "IMM"),
    0xa3: ("LAX", "IND_X"),
    0xa4: ("LDY", "ZP"),
    0xa5: ("LDA", "ZP"),
    0xa6: ("LDX", "ZP"),
    0xa7: ("LAX", "ZP"),
    0xa8: ("TAY", None),
    0xa9: ("LDA", "IMM"),
    0xaa: ("TAX", None),
    0xab: ("LAX", "IMM"),
    0xac: ("LDY", "ABS"),
    0xad: ("LDA", "ABS"),
    0xae: ("LDX", "ABS"),
    0xaf: ("LAX", "ABS"),

    0xb0: ("BCS", "REL"),
    0xb1: ("LDA", "IND_Y"),
    0xb2: None,
    0xb3: ("LAX", "IND_Y"),
    0xb4: ("LDY", "ZP_X"),
    0xb5: ("LDA", "ZP_X"),
    0xb6: ("LDX", "ZP_X"),
    0xb7: ("LAX", "ZP_X"),
    0xb8: ("CLV", None),
    0xb9: ("LDA", "ABS_Y"),
    0xba: ("TSX", None),
    0xbb: ("LAS", "ABS_Y"),
    0xbc: ("LDY", "ABS_X"),
    0xbd: ("LDA", "ABS_X"),
    0xbe: ("LDX", "ABS_X"),
    0xbf: ("LAX", "ABS_X"),

    0xc0: ("CPY", "IMM"),
    0xc1: ("CMP", "IND_X"),
    0xc2: ("NOP", "IMM"),
    0xc3: ("DCP", "IND_X"),
    0xc4: ("CPY", "ZP"),
    0xc5: ("CMP", "ZP"),
    0xc6: ("DEC", "ZP"),
    0xc7: ("DCP", "ZP"),
    0xc8: ("INY", None),
    0xc9: ("CMP", "IMM"),
    0xca: ("DEX", None),
    0xcb: ("AXS", "IMM"),
    0xcc: ("CPY", "ABS"),
    0xcd: ("CMP", "ABS"),
    0xce: ("DEC", "ABS"),
    0xcf: ("DCP", "ABS"),

    0xd0: ("BNE", "REL"),
    0xd1: ("CMP", "IND_Y"),
    0xd2: None,
    0xd3: ("DCP", "IND_Y"),
    0xd4: ("NOP", "ZP_X"),
    0xd5: ("CMP", "ZP_X"),
    0xd6: ("DEC", "ZP_X"),
    0xd7: ("DCP", "ZP_X"),
    0xd8: ("CLD", None),
    0xd9: ("CMP", "ABS_Y"),
    0xda: ("NOP", None),
    0xdb: ("DCP", "ABS_Y"),
    0xdc: ("NOP", "ANS_X"),
    0xdd: ("CMP", "ANS_X"),
    0xde: ("DEC", "ANS_X"),
    0xdf: ("DCP", "ANS_X"),

    0xe0: ("CPX", "IMM"),
    0xe1: ("SBC", "IND_X"),
    0xe2: ("NOP", "IMM"),
    0xe3: ("ISC", "IND_X"),
    0xe4: ("CPX", "ZP"),
    0xe5: ("SBC", "ZP"),
    0xe6: ("INC", "ZP"),
    0xe7: ("ISC", "ZP"),
    0xe8: ("INX", None),
    0xe9: ("SBC", "IMM"),
    0xea: ("NOP", None),
    0xeb: ("SBC", "IMM"),
    0xec: ("CPX", "ABS"),
    0xed: ("SBC", "ABS"),
    0xee: ("INC", "ABS"),
    0xef: ("ISC", "ABS"),

    0xf0: ("BEQ", "REL"),
    0xf1: ("SBC", "IND_Y"),
    0xf2: None,
    0xf3: ("ISC", "IND_Y"),
    0xf4: ("NOP", "ZP_X"),
    0xf5: ("SBC", "ZP_X"),
    0xf6: ("INC", "ZP_X"),
    0xf7: ("ISC", "ZP_X"),
    0xf8: ("SED", None),
    0xf9: ("SBC", "ABS_Y"),
    0xfa: ("NOP", None),
    0xfb: ("ISC", "ABS_Y"),
    0xfc: ("NOP", "ABS_X"),
    0xfd: ("SBC", "ABS_X"),
    0xfe: ("INC", "ABS_X"),
    0xff: ("ISC", "ABS_X"),
}
