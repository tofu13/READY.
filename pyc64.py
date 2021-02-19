from constants import *

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
class Memory:
    def __getitem__(self, item):
        value = super().__getitem__(item)
        #print(f"Memory read at {item}: {value}")
        return value

    def __setitem__(self, key, value):
        if value < 0 or value > 255:
            raise ValueError(f"Trying to write to memory a value ({value}) out of range (0-255).")
        print(f"Memory write at {key}: {value}")
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
        return f"A: {self.A:02X} X: {self.X:02X} Y: {self.Y:02X} PC: {self.PC:04X} SP: {self.SP:02X} "\
            f"{self.F}"

    def _not_implemented(self, *args):
        raise NotImplementedError()

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
        print(f"Executing {instruction} {data if data != '_' else ''}")
        getattr(self, instruction)(getattr(self,data))
        if instruction == 'BRK':
            return False
        return True

    def run(self):
        while self.step():
            print(self)

    def _(self):
        return None

    def BRK(self, *value):
        pass

    def DEX(self, *value):
        self.X -= 1

    def DEY(self, *value):
        self.X -= 1

    def INX(self, *value):
        self.X += 1

    def INY(self, *value):
        self.X += 1

    def NOP(self, *value):
        pass

    def TAX(self, *value):
        self.X = self.A

    def TAY(self, *value):
        self.X = self.A

    def TXA(self, *value):
        self.A = self.X

    def TYA(self, *value):
        self.A = self.X



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


if __name__ == '__main__':
    c64 = Machine(BytearrayMemory(65536), CPU(), Screen())
    c64.memory[0] = 0xe8
    c64.memory[1] = 0xca
    c64.memory[1024] = 65
    #print(c64.memory)
    print(c64.cpu)
    c64.cpu.run()

    #c64.screen.refresh()
    #c64.memory[1024] = 66
    #c64.screen.refresh()
