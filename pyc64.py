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
                    setattr(self, specs[0], self._not_implemented)
                self.opcodes[opcode] = getattr(self, specs[0])
        for addressing in ADDRESSING_METHODS:
            if not hasattr(self, f"addressing_{addressing}"):
                setattr(self, f"addressing_{addressing}", self._not_implemented)
        pass

    def __str__(self):
        return f"A: {self.A:02X} X: {self.X:02X} Y: {self.Y:02X} PC: {self.PC:04X} SP: {self.SP:02X} {self.F}"

    def push(self, value):
        """
        Push a value on the stack, update SP
        :param value: The value to push
        :return: None
        """
        self.memory[self.SP] = value
        self.SP = (self.SP + 1) & 0xFF

    def pop(self):
        """
        Pop a value from the stack, update SP
        :return: The popped value
        """
        value = self.memory[self.SP]
        self.SP = (self.SP - 1) & 0xFF
        return value

    def fetch(self):
        """
        Fetch next istruction (memory read at PC, advance PC)
        :return: None
        """
        opcode = self.memory[self.PC]
        #print(f"Fetched at {self.PC:04X}: {self.opcodes[opcode]}")
        self.PC += 1
        return opcode

    def step(self):
        """
        Execute next instruction
        :return: False if instruction is BRK, else True
        """
        opcode = self.fetch()
        instruction, data = OPCODES[opcode]
        print(f"Executing {instruction} {data if data != 'None' else ''}")
        getattr(self, instruction)(*getattr(self, f"addressing_{data}")())
        return instruction != 'BRK'

    def run(self, address=None):
        """
        Run from address (or PC if not specified) until BRK
        :param address: address to start execution
        :return: None
        """
        if address is not None:
            self.PC = address
        while self.step():
            print(self)

    # Utils
    def _setNZ(self, value):
        """
        Set N and Z status flags according to value
        :param value:
        :return: None
        """
        self.F['N'] = value >> 7
        self.F['Z'] = int(value == 0)

    @staticmethod
    def _combine(low, high):
        """
        Returns a 16 bit value by combining low and high bytes LITTLE ENDIAN
        :param low: The low byte
        :param high: The high byte
        :return: 2-byte value
        """
        return high << 8 | low

    def _not_implemented(self, value, address):
        raise NotImplementedError

    # Addressing methods
    @staticmethod
    def addressing_IMP():
        # The data is implied by the operation.
        return None, None

    def addressing_A(self):
        # The operation works on the accumulator. No additional data is required.
        return self.A, None

    def addressing_IMM(self):
        # Data is taken from the byte following the opcode.
        value = self.memory[self.PC]
        self.PC += 1
        return value, None

    def addressing_REL(self):
        # An 8-bit signed offset is provided. This value is added to the program counter (PC) to find the effective address.
        value = self.memory[self.PC]
        self.PC += 1
        return value if value < 127 else value - 256, None

    def addressing_ABS(self):
        # Data is accessed using 16-bit address specified as a constant.
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return None, self._combine(l, h)

    def addressing_ZP(self):
        # An 8-bit address is provided within the zero page.
        l = self.memory[self.PC]
        self.PC += 1
        return None, l

    def addressing_ABS_X(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the X register is added (with carry).
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return None, self._combine(l, h) + self.X

    def addressing_ABS_Y(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the Y register is added (with carry).
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return None, self._combine(l, h) + self.Y

    def addressing_ZP_X(self):
        # An 8-bit address is provided, to which the X register is added (without carry - if the addition overflows, the address wraps around within the zero page).
        l = self.memory[self.PC]
        self.PC += 1
        return None, (l + self.X) & 0xFF

    def addressing_ZP_Y(self):
        # An 8-bit address is provided, to which the Y register is added (without carry - if the addition overflows, the address wraps around within the zero page).
        l = self.memory[self.PC]
        self.PC += 1
        return None, (l + self.Y) & 0xFF

    def addressing_IND(self):
        # Data is accessed using a pointer. The 16-bit address of the pointer is given in the two bytes following the opcode.
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        address = self._combine(l, h)
        return None, self._combine(self.memory[address], self.memory[address + 1])

    def addressing_X_IND(self):
        # An 8-bit zero-page address and the X register are added, without carry (if the addition overflows, the address wraps around within page 0). The resulting address is used as a pointer to the data being accessed.
        l = self.memory[self.PC]
        self.PC += 1
        address = (l + self.X) & 0xFF
        return self.memory[address], None

    def addressing_IND_Y(self):
        # An 8-bit address identifies a pointer. The value of the Y register is added to the address contained in the pointer. Effectively, the pointer is the base address and the Y register is an index past that base address.
        l = self.memory[self.PC]
        self.PC += 1
        return (self.memory[l] + self.Y) & 0xFF, None

    # Instructions
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

    def JMP(self, value, address):
        self.PC = address

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

    filename = "test1"
    subprocess.run(f"programs/acme -f cbm -o programs/{filename} programs/{filename}.asm".split())
    base = c64.load(f"programs/{filename}")
    c64.cpu.run(base)

