import enum
import re

import pygame

DEFAULT_LOAD_ADDRESS = 0x0801

SYMBOLS = {
    'D6510': 0x0000,
    'R6510': 0x0001,
}

CLOCKS_PER_EVENT_SERVING = 25000  # Clock cycles between system event serving (keyboard scan, ...)
CLOCKS_PER_CONSOLE_REFRESH = 50000  # Clock cycles between console screen (when enabled) updates
CLOCKS_PER_FRAME = 18656  # Clock cycles between frame update (non-raster screen drivers)
CLOCKS_PER_PERFORMANCE_REFRESH = 250000  # CLocks cycles between refresh of FPS/perf values

ROMSLIST = [
    # (File)Name, begin address, end address, bit of bank switch register (R6510)
    ("basic", 0xA000, 0xBFFF, 0),
    ("chargen", 0xD000, 0xDFFF, 1),
    ("kernal", 0xE000, 0xFFFF, 2),
]

VIDEO_SIZE = (403, 284)

COLORS = [0x000000,
          0xFFFFFF,
          0x93493E,
          0x85C6CD,
          0x9450B7,
          0x73B34A,
          0x4637AC,
          0xD6E07D,
          0x9A6929,
          0x675100,
          0xC28279,
          0x606060,
          0x8B8B8B,
          0xB4ED92,
          0x877BDF,
          0xB5B5B5
          ]

PALETTE = [[q >> 16, (q >> 8) & 0xFF, q & 0xFF] for q in COLORS]

BITVALUES = [k ** 2 for k in range(8)]
BITRANGE = [(7 - k, 2 ** k) for k in range(8)]

OPCODES = {
    0x00: ("BRK", "addressing_IMP", 7),
    0x01: ("ORA", "addressing_X_IND", 6),
    0x02: (None, "", 0),
    0x03: (None, "", 0),
    0x04: (None, "", 0),
    0x05: ("ORA", "addressing_ZP", 3),
    0x06: ("ASL", "addressing_ZP", 5),
    0x07: (None, "", 0),
    0x08: ("PHP", "addressing_IMP", 3),
    0x09: ("ORA", "addressing_IMM", 2),
    0x0a: ("ASL", "addressing_IMP", 2),
    0x0b: (None, "", 0),
    0x0c: (None, "", 0),
    0x0d: ("ORA", "addressing_ABS", 4),
    0x0e: ("ASL", "addressing_ABS", 6),
    0x0f: (None, "", 0),

    0x10: ("BPL", "addressing_REL", 2),
    0x11: ("ORA", "addressing_IND_Y", 5),
    0x12: (None, "", 0),
    0x13: (None, "", 0),
    0x14: (None, "", 0),
    0x15: ("ORA", "addressing_ZP_X", 4),
    0x16: ("ASL", "addressing_ZP_X", 6),
    0x17: (None, "", 0),
    0x18: ("CLC", "addressing_IMP", 2),
    0x19: ("ORA", "addressing_ABS_Y", 4),
    0x1a: (None, "", 0),
    0x1b: (None, "", 0),
    0x1c: (None, "", 0),
    0x1d: ("ORA", "addressing_ABS_X", 4),
    0x1e: ("ASL", "addressing_ABS_X", 7),
    0x1f: (None, "", 0),

    0x20: ("JSR", "addressing_ABS", 6),
    0x21: ("AND", "addressing_X_IND", 6),
    0x22: (None, "", 0),
    0x23: (None, "", 0),
    0x24: ("BIT", "addressing_ZP", 3),
    0x25: ("AND", "addressing_ZP", 3),
    0x26: ("ROL", "addressing_ZP", 5),
    0x27: (None, "", 0),
    0x28: ("PLP", "addressing_IMP", 4),
    0x29: ("AND", "addressing_IMM", 2),
    0x2a: ("ROL", "addressing_IMP", 2),
    0x2b: (None, "", 0),
    0x2c: ("BIT", "addressing_ABS", 4),
    0x2d: ("AND", "addressing_ABS", 4),
    0x2e: ("ROL", "addressing_ABS", 6),
    0x2f: (None, "", 0),

    0x30: ("BMI", "addressing_REL", 2),
    0x31: ("AND", "addressing_IND_Y", 5),
    0x32: (None, "", 0),
    0x33: (None, "", 0),
    0x34: (None, "", 0),
    0x35: ("AND", "addressing_ZP_X", 4),
    0x36: ("ROL", "addressing_ZP_X", 6),
    0x37: (None, "", 0),
    0x38: ("SEC", "addressing_IMP", 2),
    0x39: ("AND", "addressing_ABS_Y", 4),
    0x3a: (None, "", 0),
    0x3b: (None, "", 0),
    0x3c: (None, "", 0),
    0x3d: ("AND", "addressing_ABS_X", 4),
    0x3e: ("ROL", "addressing_ABS_X", 7),
    0x3f: (None, "", 0),

    0x40: ("RTI", "addressing_IMP", 6),
    0x41: ("EOR", "addressing_X_IND", 6),
    0x42: (None, "", 0),
    0x43: (None, "", 0),
    0x44: (None, "", 0),
    0x45: ("EOR", "addressing_ZP", 3),
    0x46: ("LSR", "addressing_ZP", 5),
    0x47: (None, "", 0),
    0x48: ("PHA", "addressing_IMP", 3),
    0x49: ("EOR", "addressing_IMM", 2),
    0x4a: ("LSR", "addressing_IMP", 2),
    0x4b: (None, "", 0),
    0x4c: ("JMP", "addressing_ABS", 3),
    0x4d: ("EOR", "addressing_ABS", 4),
    0x4e: ("LSR", "addressing_ABS", 6),
    0x4f: (None, "", 0),

    0x50: ("BVC", "addressing_REL", 2),
    0x51: ("EOR", "addressing_IND_Y", 5),
    0x52: (None, "", 0),
    0x53: (None, "", 0),
    0x54: (None, "", 0),
    0x55: ("EOR", "addressing_ZP_X", 4),
    0x56: ("LSR", "addressing_ZP_X", 6),
    0x57: (None, "", 0),
    0x58: ("CLI", "addressing_IMP", 2),
    0x59: ("EOR", "addressing_ABS_Y", 4),
    0x5a: (None, "", 0),
    0x5b: (None, "", 0),
    0x5c: (None, "", 0),
    0x5d: ("EOR", "addressing_ABS_X", 4),
    0x5e: ("LSR", "addressing_ABS_X", 7),
    0x5f: (None, "", 0),

    0x60: ("RTS", "addressing_IMP", 6),
    0x61: ("ADC", "addressing_X_IND", 6),
    0x62: (None, "", 0),
    0x63: (None, "", 0),
    0x64: (None, "", 0),
    0x65: ("ADC", "addressing_ZP", 3),
    0x66: ("ROR", "addressing_ZP", 5),
    0x67: (None, "", 0),
    0x68: ("PLA", "addressing_IMP", 4),
    0x69: ("ADC", "addressing_IMM", 2),
    0x6a: ("ROR", "addressing_IMP", 2),
    0x6b: (None, "", 0),
    0x6c: ("JMP", "addressing_IND", 5),
    0x6d: ("ADC", "addressing_ABS", 4),
    0x6e: ("ROR", "addressing_ABS", 6),
    0x6f: (None, "", 0),

    0x70: ("BVS", "addressing_REL", 2),
    0x71: ("ADC", "addressing_IND_Y", 5),
    0x72: (None, "", 0),
    0x73: (None, "", 0),
    0x74: (None, "", 0),
    0x75: ("ADC", "addressing_ZP_X", 4),
    0x76: ("ROR", "addressing_ZP_X", 6),
    0x77: (None, "", 0),
    0x78: ("SEI", "addressing_IMP", 2),
    0x79: ("ADC", "addressing_ABS_Y", 4),
    0x7a: (None, "", 0),
    0x7b: (None, "", 0),
    0x7c: (None, "", 0),
    0x7d: ("ADC", "addressing_ABS_X", 4),
    0x7e: ("ROR", "addressing_ABS_X", 7),
    0x7f: (None, "", 0),

    0x80: (None, "", 0),
    0x81: ("STA", "addressing_X_IND", 6),
    0x82: (None, "", 0),
    0x83: (None, "", 0),
    0x84: ("STY", "addressing_ZP", 3),
    0x85: ("STA", "addressing_ZP", 4),
    0x86: ("STX", "addressing_ZP", 3),
    0x87: (None, "", 0),
    0x88: ("DEY", "addressing_IMP", 2),
    0x89: (None, "", 0),
    0x8a: ("TXA", "addressing_IMP", 2),
    0x8b: (None, "", 0),
    0x8c: ("STY", "addressing_ABS", 4),
    0x8d: ("STA", "addressing_ABS", 4),
    0x8e: ("STX", "addressing_ABS", 4),
    0x8f: (None, "", 0),

    0x90: ("BCC", "addressing_REL", 2),
    0x91: ("STA", "addressing_IND_Y", 6),
    0x92: (None, "", 0),
    0x93: (None, "", 0),
    0x94: ("STY", "addressing_ZP_X", 4),
    0x95: ("STA", "addressing_ZP_X", 4),
    0x96: ("STX", "addressing_ZP_Y", 4),
    0x97: (None, "", 0),
    0x98: ("TYA", "addressing_IMP", 2),
    0x99: ("STA", "addressing_ABS_Y", 5),
    0x9a: ("TXS", "addressing_IMP", 2),
    0x9b: (None, "", 0),
    0x9c: (None, "", 0),
    0x9d: ("STA", "addressing_ABS_X", 5),
    0x9e: (None, "", 0),
    0x9f: (None, "", 0),

    0xa0: ("LDY", "addressing_IMM", 2),
    0xa1: ("LDA", "addressing_X_IND", 6),
    0xa2: ("LDX", "addressing_IMM", 2),
    0xa3: (None, "", 0),
    0xa4: ("LDY", "addressing_ZP", 3),
    0xa5: ("LDA", "addressing_ZP", 3),
    0xa6: ("LDX", "addressing_ZP", 3),
    0xa7: (None, "", 0),
    0xa8: ("TAY", "addressing_IMP", 2),
    0xa9: ("LDA", "addressing_IMM", 2),
    0xaa: ("TAX", "addressing_IMP", 2),
    0xab: (None, "", 0),
    0xac: ("LDY", "addressing_ABS", 4),
    0xad: ("LDA", "addressing_ABS", 4),
    0xae: ("LDX", "addressing_ABS", 4),
    0xaf: (None, "", 0),

    0xb0: ("BCS", "addressing_REL", 2),
    0xb1: ("LDA", "addressing_IND_Y", 5),
    0xb2: (None, "", 0),
    0xb3: (None, "", 0),
    0xb4: ("LDY", "addressing_ZP_X", 4),
    0xb5: ("LDA", "addressing_ZP_X", 4),
    0xb6: ("LDX", "addressing_ZP_Y", 4),
    0xb7: (None, "", 0),
    0xb8: ("CLV", "addressing_IMP", 2),
    0xb9: ("LDA", "addressing_ABS_Y", 4),
    0xba: ("TSX", "addressing_IMP", 2),
    0xbb: (None, "", 0),
    0xbc: ("LDY", "addressing_ABS_X", 4),
    0xbd: ("LDA", "addressing_ABS_X", 4),
    0xbe: ("LDX", "addressing_ABS_Y", 4),
    0xbf: (None, "", 0),

    0xc0: ("CPY", "addressing_IMM", 2),
    0xc1: ("CMP", "addressing_X_IND", 6),
    0xc2: (None, "", 0),
    0xc3: (None, "", 0),
    0xc4: ("CPY", "addressing_ZP", 3),
    0xc5: ("CMP", "addressing_ZP", 3),
    0xc6: ("DEC", "addressing_ZP", 5),
    0xc7: (None, "", 0),
    0xc8: ("INY", "addressing_IMP", 2),
    0xc9: ("CMP", "addressing_IMM", 2),
    0xca: ("DEX", "addressing_IMP", 2),
    0xcb: (None, "", 0),
    0xcc: ("CPY", "addressing_ABS", 4),
    0xcd: ("CMP", "addressing_ABS", 5),
    0xce: ("DEC", "addressing_ABS", 6),
    0xcf: (None, "", 0),

    0xd0: ("BNE", "addressing_REL", 2),
    0xd1: ("CMP", "addressing_IND_Y", 5),
    0xd2: (None, "", 0),
    0xd3: (None, "", 0),
    0xd4: (None, "", 0),
    0xd5: ("CMP", "addressing_ZP_X", 4),
    0xd6: ("DEC", "addressing_ZP_X", 6),
    0xd7: (None, "", 0),
    0xd8: ("CLD", "addressing_IMP", 2),
    0xd9: ("CMP", "addressing_ABS_Y", 4),
    0xda: (None, "", 0),
    0xdb: (None, "", 0),
    0xdc: (None, "", 0),
    0xdd: ("CMP", "addressing_ABS_X", 4),
    0xde: ("DEC", "addressing_ABS_X", 7),
    0xdf: (None, "", 0),

    0xe0: ("CPX", "addressing_IMM", 2),
    0xe1: ("SBC", "addressing_X_IND", 6),
    0xe2: (None, "", 0),
    0xe3: (None, "", 0),
    0xe4: ("CPX", "addressing_ZP", 3),
    0xe5: ("SBC", "addressing_ZP", 3),
    0xe6: ("INC", "addressing_ZP", 5),
    0xe7: (None, "", 0),
    0xe8: ("INX", "addressing_IMP", 2),
    0xe9: ("SBC", "addressing_IMM", 2),
    0xea: ("NOP", "addressing_IMP", 2),
    0xeb: (None, "", 0),
    0xec: ("CPX", "addressing_ABS", 4),
    0xed: ("SBC", "addressing_ABS", 4),
    0xee: ("INC", "addressing_ABS", 6),
    0xef: (None, "", 0),

    0xf0: ("BEQ", "addressing_REL", 2),
    0xf1: ("SBC", "addressing_IND_Y", 5),
    0xf2: (None, "", 0),
    0xf3: (None, "", 0),
    0xf4: (None, "", 0),
    0xf5: ("SBC", "addressing_ZP_X", 4),
    0xf6: ("INC", "addressing_ZP_X", 6),
    0xf7: (None, "", 0),
    0xf8: ("SED", "addressing_IMP", 2),
    0xf9: ("SBC", "addressing_ABS_Y", 4),
    0xfa: (None, "", 0),
    0xfb: (None, "", 0),
    0xfc: (None, "", 0),
    0xfd: ("SBC", "addressing_ABS_X", 4),
    0xfe: ("INC", "addressing_ABS_X", 7),
    0xff: (None, "", 0),
}

INVERSE_OPCODES = {(mnemonic, addressing): opcode for opcode, (mnemonic, addressing, _) in OPCODES.items()}

ASSEMBLER_REGEXES = {
    re.compile(r"^#([$&+%]?[0123456789ABCDEF]{1,8})$", re.I): "IMM",
    re.compile(r"^\((\$[0123456789ABCDEF]{4})\)$", re.I): "IND",
    re.compile(r"^(\$[0123456789ABCDEF]{4})$", re.I): "ABS",
    re.compile(r"^(\$[0123456789ABCDEF]{4}),X$", re.I): "ABS_X",
    re.compile(r"^(\$[0123456789ABCDEF]{4}),Y$", re.I): "ABS_Y",
    re.compile(r"^(\$[0123456789ABCDEF]{2})$", re.I): "ZP",
    re.compile(r"^(\$[0123456789ABCDEF]{2}),X$", re.I): "ZP_X",
    re.compile(r"^(\$[0123456789ABCDEF]{2}),Y$", re.I): "ZP_Y",
    re.compile(r"^\((\$[0123456789ABCDEF]{2}),X\)$", re.I): "X_IND",
    re.compile(r"^\((\$[0123456789ABCDEF]{2})\),Y$", re.I): "IND_Y",
    # REL addressing not detected here: ambiguous with IMM
}

PETSCII = {
    "\n": 13,
    " ": 32,
    "!": 33,
    "\"": 34,
    "#": 35,
    "$": 36,
    "%": 37,
    "&": 38,
    "'": 39,
    "(": 40,
    ")": 41,
    "*": 42,
    "+": 43,
    ",": 44,
    "-": 45,
    ".": 46,
    "/": 47,
    "0": 48,
    "1": 49,
    "2": 50,
    "3": 51,
    "4": 52,
    "5": 53,
    "6": 54,
    "7": 55,
    "8": 56,
    "9": 57,
    ":": 58,
    ";": 59,
    "<": 60,
    "=": 61,
    ">": 62,
    "?": 63,
    "@": 64,
    "a": 65,
    "b": 66,
    "c": 67,
    "d": 68,
    "e": 69,
    "f": 70,
    "g": 71,
    "h": 72,
    "i": 73,
    "j": 74,
    "k": 75,
    "l": 76,
    "m": 77,
    "n": 78,
    "o": 79,
    "p": 80,
    "q": 81,
    "r": 82,
    "s": 83,
    "t": 84,
    "u": 85,
    "v": 86,
    "w": 87,
    "x": 88,
    "y": 89,
    "z": 90,
    "[": 91,
    "£": 92,
    "]": 93,
}

SCREEN_CHARCODE = {
    0: "@",
    1: "A",
    2: "B",
    3: "C",
    4: "D",
    5: "E",
    6: "F",
    7: "G",
    8: "H",
    9: "I",
    10: "J",
    11: "K",
    12: "L",
    13: "M",
    14: "N",
    15: "O",
    16: "P",
    17: "Q",
    18: "R",
    19: "S",
    20: "T",
    21: "U",
    22: "V",
    23: "W",
    24: "X",
    25: "Y",
    26: "Z",
    27: "[",
    28: "£",
    29: "]",
    32: " ",
    33: "!",
    34: "\"",
    35: "#",
    36: "$",
    37: "%",
    38: "&",
    39: "'",
    40: "(",
    41: ")",
    42: "*",
    43: "+",
    44: ",",
    45: "-",
    46: ".",
    47: "/",
    48: "0",
    49: "1",
    50: "2",
    51: "3",
    52: "4",
    53: "5",
    54: "6",
    55: "7",
    56: "8",
    57: "9",
    58: ":",
    59: ";",
    60: "<",
    61: "=",
    62: ">",
    63: "?",
}


class C64_KEYS(enum.Enum):
    INS_DEL = (0x01, 0x01)
    RETURN = (0x01, 0x02)
    CRSR_LR = (0x01, 0x04)
    F7_F8 = (0x01, 0x08)
    F1_F2 = (0x01, 0x10)
    F3_F4 = (0x01, 0x20)
    F5_F6 = (0x01, 0x40)
    CRSR_UD = (0x01, 0x80)
    NUMBER_3 = (0x02, 0x01)
    W = (0x02, 0x02)
    A = (0x02, 0x04)
    NUMBER_4 = (0x02, 0x08)
    Z = (0x02, 0x10)
    S = (0x02, 0x20)
    E = (0x02, 0x40)
    LEFT_SHIFT = (0x02, 0x80)
    NUMBER_5 = (0x04, 0x01)
    R = (0x04, 0x02)
    D = (0x04, 0x04)
    NUMBER_6 = (0x04, 0x08)
    C = (0x04, 0x10)
    F = (0x04, 0x20)
    T = (0x04, 0x40)
    X = (0x04, 0x80)
    NUMBER_7 = (0x08, 0x01)
    Y = (0x08, 0x02)
    G = (0x08, 0x04)
    NUMBER_8 = (0x08, 0x08)
    B = (0x08, 0x10)
    H = (0x08, 0x20)
    U = (0x08, 0x40)
    V = (0x08, 0x80)
    NUMBER_9 = (0x10, 0x01)
    I = (0x10, 0x02)  # noqa
    J = (0x10, 0x04)
    NUMBER_0 = (0x10, 0x08)
    M = (0x10, 0x10)
    K = (0x10, 0x20)
    O = (0x10, 0x40)  # noqa
    N = (0x10, 0x80)
    PLUS = (0x20, 0x01)
    P = (0x20, 0x02)
    L = (0x20, 0x04)
    MINUS = (0x20, 0x08)
    PERIOD = (0x20, 0x10)
    COLON = (0x20, 0x20)
    AT = (0x20, 0x40)
    COMMA = (0x20, 0x80)
    POUND = (0x40, 0x01)
    ASTERISK = (0x40, 0x02)
    SEMICOLON = (0x40, 0x04)
    CLEAR_HOME = (0x40, 0x08)
    RIGHT_SHIFT = (0x40, 0x10)
    EQUAL = (0x40, 0x20)
    UP_ARROW = (0x40, 0x40)
    SLASH = (0x40, 0x80)
    NUMBER_1 = (0x80, 0x01)
    LEFT_ARROW = (0x80, 0x02)
    CONTROL = (0x80, 0x04)
    NUMBER_2 = (0x80, 0x08)
    SPACE = (0x80, 0x10)
    COMMODORE = (0x80, 0x20)
    Q = (0x80, 0x40)
    RUN_STOP = (0x80, 0x80)


KEYBOARD = {
    # IT keymap
    frozenset((pygame.K_LSHIFT, pygame.K_PLUS)): {C64_KEYS.ASTERISK},  # *
    frozenset((pygame.K_LSHIFT, pygame.K_0)): {C64_KEYS.EQUAL},  # =
    frozenset((pygame.K_LSHIFT, pygame.K_7)): {C64_KEYS.SLASH},  # /
    frozenset((pygame.K_LSHIFT, pygame.K_QUOTE)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.SLASH},  # ?
    frozenset((pygame.K_LSHIFT, pygame.K_PERIOD)): {C64_KEYS.COLON},  # :
    frozenset((pygame.K_LSHIFT, pygame.K_COMMA)): {C64_KEYS.SEMICOLON},  # ;
    frozenset((pygame.K_LSHIFT, pygame.K_3)): {C64_KEYS.POUND},  # £
    frozenset((pygame.K_LSHIFT, pygame.K_LESS)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.PERIOD},  # >
    frozenset((pygame.K_RSHIFT, pygame.K_PLUS)): {C64_KEYS.ASTERISK},  # *
    frozenset((pygame.K_RSHIFT, pygame.K_0)): {C64_KEYS.EQUAL},  # =
    frozenset((pygame.K_RSHIFT, pygame.K_7)): {C64_KEYS.SLASH},  # /
    frozenset((pygame.K_RSHIFT, pygame.K_QUOTE)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.SLASH},  # ?
    frozenset((pygame.K_RSHIFT, pygame.K_PERIOD)): {C64_KEYS.COLON},  # :
    frozenset((pygame.K_RSHIFT, pygame.K_COMMA)): {C64_KEYS.SEMICOLON},  # ;
    frozenset((pygame.K_RSHIFT, pygame.K_3)): {C64_KEYS.POUND},  # £
    frozenset((pygame.K_RSHIFT, pygame.K_LESS)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.PERIOD},  # >
    frozenset((pygame.K_RALT, 224)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.NUMBER_3},  # #
    frozenset((pygame.K_RALT, 242)): {C64_KEYS.AT},  # @
    frozenset((pygame.K_RALT, 232)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.COLON},  # [
    frozenset((pygame.K_RALT, pygame.K_PLUS)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.SEMICOLON},  # ]
    frozenset((pygame.K_LESS,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.COMMA},  # <
    frozenset((pygame.K_PAGEUP,)): {C64_KEYS.UP_ARROW},  #
    frozenset((pygame.K_BACKSLASH,)): {C64_KEYS.LEFT_ARROW},
    frozenset((pygame.K_PLUS,)): {C64_KEYS.PLUS},
    frozenset((pygame.K_MINUS,)): {C64_KEYS.MINUS},
    frozenset((pygame.K_QUOTE,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.NUMBER_7},
    frozenset((pygame.K_PERIOD,)): {C64_KEYS.PERIOD},
    frozenset((pygame.K_COMMA,)): {C64_KEYS.COMMA},

    # Common keys
    frozenset((pygame.K_LEFT,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.CRSR_LR},
    frozenset((pygame.K_UP,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.CRSR_UD},
    frozenset((pygame.K_RIGHT,)): {C64_KEYS.CRSR_LR},
    frozenset((pygame.K_DOWN,)): {C64_KEYS.CRSR_UD},

    frozenset((pygame.K_SPACE,)): {C64_KEYS.SPACE},
    frozenset((pygame.K_DELETE,)): {C64_KEYS.INS_DEL},
    frozenset((pygame.K_BACKSPACE,)): {C64_KEYS.INS_DEL},
    frozenset((pygame.K_INSERT,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.INS_DEL},
    frozenset((pygame.K_RETURN,)): {C64_KEYS.RETURN},
    frozenset((pygame.K_HOME,)): {C64_KEYS.CLEAR_HOME},
    frozenset((pygame.K_ESCAPE,)): {C64_KEYS.RUN_STOP},

    frozenset((pygame.K_LSHIFT,)): {C64_KEYS.LEFT_SHIFT},
    frozenset((pygame.K_RSHIFT,)): {C64_KEYS.RIGHT_SHIFT},
    frozenset((pygame.K_LCTRL,)): {C64_KEYS.CONTROL},
    frozenset((pygame.K_LALT,)): {C64_KEYS.COMMODORE},

    frozenset((pygame.K_0,)): {C64_KEYS.NUMBER_0},
    frozenset((pygame.K_1,)): {C64_KEYS.NUMBER_1},
    frozenset((pygame.K_2,)): {C64_KEYS.NUMBER_2},
    frozenset((pygame.K_3,)): {C64_KEYS.NUMBER_3},
    frozenset((pygame.K_4,)): {C64_KEYS.NUMBER_4},
    frozenset((pygame.K_5,)): {C64_KEYS.NUMBER_5},
    frozenset((pygame.K_6,)): {C64_KEYS.NUMBER_6},
    frozenset((pygame.K_7,)): {C64_KEYS.NUMBER_7},
    frozenset((pygame.K_8,)): {C64_KEYS.NUMBER_8},
    frozenset((pygame.K_9,)): {C64_KEYS.NUMBER_9},

    frozenset((pygame.K_KP0,)): {C64_KEYS.NUMBER_0},
    frozenset((pygame.K_KP1,)): {C64_KEYS.NUMBER_1},
    frozenset((pygame.K_KP2,)): {C64_KEYS.NUMBER_2},
    frozenset((pygame.K_KP3,)): {C64_KEYS.NUMBER_3},
    frozenset((pygame.K_KP4,)): {C64_KEYS.NUMBER_4},
    frozenset((pygame.K_KP5,)): {C64_KEYS.NUMBER_5},
    frozenset((pygame.K_KP6,)): {C64_KEYS.NUMBER_6},
    frozenset((pygame.K_KP7,)): {C64_KEYS.NUMBER_7},
    frozenset((pygame.K_KP8,)): {C64_KEYS.NUMBER_8},
    frozenset((pygame.K_KP9,)): {C64_KEYS.NUMBER_9},

    frozenset((pygame.K_KP_ENTER,)): {C64_KEYS.RETURN},
    frozenset((pygame.K_KP_PLUS,)): {C64_KEYS.PLUS},
    frozenset((pygame.K_KP_MINUS,)): {C64_KEYS.MINUS},
    frozenset((pygame.K_KP_MULTIPLY,)): {C64_KEYS.ASTERISK},
    frozenset((pygame.K_KP_DIVIDE,)): {C64_KEYS.SLASH},
    frozenset((pygame.K_KP_PERIOD,)): {C64_KEYS.PERIOD},

    frozenset((pygame.K_a,)): {C64_KEYS.A},
    frozenset((pygame.K_b,)): {C64_KEYS.B},
    frozenset((pygame.K_c,)): {C64_KEYS.C},
    frozenset((pygame.K_d,)): {C64_KEYS.D},
    frozenset((pygame.K_e,)): {C64_KEYS.E},
    frozenset((pygame.K_f,)): {C64_KEYS.F},
    frozenset((pygame.K_g,)): {C64_KEYS.G},
    frozenset((pygame.K_h,)): {C64_KEYS.H},
    frozenset((pygame.K_i,)): {C64_KEYS.I},
    frozenset((pygame.K_j,)): {C64_KEYS.J},
    frozenset((pygame.K_k,)): {C64_KEYS.K},
    frozenset((pygame.K_l,)): {C64_KEYS.L},
    frozenset((pygame.K_m,)): {C64_KEYS.M},
    frozenset((pygame.K_n,)): {C64_KEYS.N},
    frozenset((pygame.K_o,)): {C64_KEYS.O},
    frozenset((pygame.K_p,)): {C64_KEYS.P},
    frozenset((pygame.K_q,)): {C64_KEYS.Q},
    frozenset((pygame.K_r,)): {C64_KEYS.R},
    frozenset((pygame.K_s,)): {C64_KEYS.S},
    frozenset((pygame.K_t,)): {C64_KEYS.T},
    frozenset((pygame.K_u,)): {C64_KEYS.U},
    frozenset((pygame.K_v,)): {C64_KEYS.V},
    frozenset((pygame.K_w,)): {C64_KEYS.W},
    frozenset((pygame.K_x,)): {C64_KEYS.X},
    frozenset((pygame.K_y,)): {C64_KEYS.Y},
    frozenset((pygame.K_z,)): {C64_KEYS.Z},

    frozenset((pygame.K_F1,)): {C64_KEYS.F1_F2},
    frozenset((pygame.K_F2,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.F1_F2},
    frozenset((pygame.K_F3,)): {C64_KEYS.F3_F4},
    frozenset((pygame.K_F4,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.F3_F4},
    frozenset((pygame.K_F5,)): {C64_KEYS.F5_F6},
    frozenset((pygame.K_F6,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.F5_F6},
    frozenset((pygame.K_F7,)): {C64_KEYS.F7_F8},
    frozenset((pygame.K_F8,)): {C64_KEYS.LEFT_SHIFT, C64_KEYS.F7_F8},
}
