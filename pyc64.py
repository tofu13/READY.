from constants import *
import subprocess

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
class Memory:
    def __getitem__(self, item):
        value = super().__getitem__(item)
        #print(f"Memory read at {item}: {value}")
        return value

    def __setitem__(self, key, value):
        if value < 0 or value > 255:
            raise ValueError(f"Trying to write to memory a value ({value}) out of range (0-255).")
        #print(f"Memory write at {key}: {value}")
        super().__setitem__(key, value)

    def __str__(self, start=0, end=None):
        if end is None:
            end = start + 0x0100
        return "\n".join(
            [f"{i:04X}: {super(__class__, self).__getitem__(slice(i, i+15))}" for i in range(start, end, 16)]
        )


class BytearrayMemory(Memory, bytearray):
    pass


# noinspection PyPep8Naming
class CPU:
    # noinspection PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming
    memory = None

    def __init__(self, A=0, X=0, Y=0, PC=0x0000, SP=0x00):
        self.A = A
        self.X = X
        self.Y = Y
        self.PC = PC
        self.SP = SP
        self.F = {'N': 1, 'V': 1, 'B': 1, 'D': 1, 'I': 1, 'Z': 1, 'C': 1}

        self.opcodes = dict()
        for opcode, specs in OPCODES.items():
            if specs is not None:
                if not hasattr(self, specs[0]):
                    setattr(self, specs[0], NotImplementedError)
                self.opcodes[opcode] = getattr(self, specs[0])
        for addressing in ADDRESSING_METHODS:
            if not hasattr(self, f"addressing_{addressing}"):
                setattr(self, f"addressing_{addressing}", NotImplementedError)
        pass

    def __str__(self):
        return f"A: {self.A:02X} X: {self.X:02X} Y: {self.Y:02X} PC: {self.PC:04X} SP: {self.SP:02X} {self.F}"

    def push(self, value):
        self.memory[self.SP] = value
        self.SP += 1

    def pop(self):
        self.SP -= 1
        return self.memory[self.SP - 1]

    def fetch(self):
        opcode = self.memory[self.PC]
        #print(f"Fetched at {self.PC:04X}: {self.opcodes[opcode]}")
        self.PC += 1
        return opcode

    def step(self):
        opcode = self.fetch()
        instruction, data = OPCODES[opcode]
        print(f"Executing {instruction} {data if data != 'None' else ''}")
        getattr(self, instruction)(*getattr(self, f"addressing_{data}")())
        return instruction != 'BRK'

    def run(self, address=None):
        if address is not None:
            self.PC = address
        while self.step():
            print(self)

    # Addressing methods
    def addressing_None(self):
        return None, None

    def addressing_A(self):
        return self.A, None

    def addressing_IMM(self):
        value = self.memory[self.PC]
        self.PC += 1
        return value, None

    def addressing_REL(self):
        value = self.memory[self.PC]
        self.PC += 1
        return value if value <127 else value - 256, None

    def addressing_ABS(self):
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return None, h << 8 | l

    def addressing_ZP(self):
        l = self.memory[self.PC]
        self.PC += 1
        return None, l

    def addressing_ABS_X(self):
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return None, (h << 8 | l) + self.X

    def addressing_ABS_Y(self):
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return None, (h << 8 | l) + self.Y

    def addressing_ZP_X(self):
        l = self.memory[self.PC]
        self.PC += 1
        return None, (l + self.X) & 0xFF

    def addressing_ZP_Y(self):
        l = self.memory[self.PC]
        self.PC += 1
        return None, (l + self.Y) & 0xFF

    def addressing_IND(self): # Use next word as zero-page addr and the following byte from that zero page as another 8 bits, and combine the two into a 16-bit address
        pass

    def addressing_IND_X(self): # As with the above, but add X to the ZP
        pass

    def addressing_IND_Y(self): # As with the above, but add Y to the
        pass

    def _setNZ(self, value):
        self.F['N'] = value >> 7
        self.F['Z'] = int(value == 0)

    def BRK(self, value, address):
        pass

    def CLC(self, value, address):
        self.F['C'] = 0

    def CLD(self, value, address):
        self.F['D'] = 0

    def CLI(self, value, address):
        self.F['I'] = 0

    def CLV(self, value, address):
        self.F['V'] = 0

    def DEX(self, value, address):
        self.X -= 1 & 0xFF
        self._setNZ(self.X)

    def DEY(self, value, address):
        self.Y -= 1 & 0xFF
        self._setNZ(self.Y)

    def INX(self, value, address):
        self.X += 1 & 0xFF
        self._setNZ(self.X)

    def INY(self, value, address):
        self.Y += 1 & 0xFF
        self._setNZ(self.Y)

    def LDA(self, value, address):
        if value is not None:
            self.A = value
        else:
            self.A = self.memory[address]
        self._setNZ(self.A)

    def LDX(self, value, address):
        if value is not None:
            self.X = value
        else:
            self.X = self.memory[address]
        self._setNZ(self.X)

    def LDY(self, value, address):
        if value is not None:
            self.Y = value
        else:
            self.Y = self.memory[address]
        self._setNZ(self.Y)

    def NOP(self, value, address):
        pass

    def SEC(self, value, address):
        self.F['C'] = 1

    def SED(self, value, address):
        self.F['D'] = 1

    def SEI(self, value, address):
        self.F['I'] = 1

    def TAX(self, value, address):
        self.X = self.A
        self._setNZ(self.A)

    def TAY(self, value, address):
        self.Y = self.A
        self._setNZ(self.A)

    def TXA(self, value, address):
        self.A = self.X
        self._setNZ(self.X)

    def TYA(self, value, address):
        self.A = self.Y
        self._setNZ(self.Y)

class Screen:
    memory = None

    def refresh(self):
        print("\n".join(
            ["".join(map(chr,self.memory[1024 + i*40: 1024 + i*40 + 39])) for i in range(0, 24, 40)])
        )


class Machine:
    def __init__(self, memory, cpu, screen):
        self.memory = memory
        self.cpu = cpu
        self.screen = screen

        self.cpu.memory = self.memory
        self.screen.memory = self.memory

    def load(self, filename):
        with open(filename, 'rb') as f:
            # First two bytes are base address for loading into memory (cbm file format, little endian)
            l, h = f.read(2)
            data = f.read()
        base = h << 8 | l
        for i, b in enumerate(data):
            self.memory[base + i] = b
        print(f"Loaded {len(data)} bytes starting at ${base:04X}")
        return base


if __name__ == '__main__':
    c64 = Machine(BytearrayMemory(65536), CPU(), Screen())
    #c64.memory[0] = 0xe8
    #c64.memory[1] = 0xca
    #c64.memory[1024] = 65
    #print(c64.memory)
    print(c64.cpu)
    #c64.cpu.run()

    #c64.screen.refresh()
    #c64.memory[1024] = 66
    #c64.screen.refresh()

    filename = "test_ABS_XY_ZP"
    subprocess.run(f"programs/acme -f cbm -o programs/{filename} programs/{filename}.asm".split())
    base = c64.load(f"programs/{filename}")
    c64.cpu.run(base)

