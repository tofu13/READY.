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
    def __init__(self, memory, A=0, X=0, Y=0, PC=0x0000, SP=0xFF):
        self.memory = memory
        self.A = A
        self.X = X
        self.Y = Y
        self.PC = PC
        self.SP = SP

    def push(self, value):
        self.memory[self.SP] = value
        self.SP -= 1

    def pop(self):
        self.SP += 1
        return self.memory[self.SP - 1]

    def fetch(self):
        opcode = self.memory[self.PC]
        print(f"Fetched at {self.PC}: {opcode:02X}")
        self.PC += 1
        return opcode

    def __str__(self):
        return f"A: {self.A:02X} X: {self.X:02X} Y: {self.Y:02X} PC: {self.PC:04X} SP: {self.SP:02X}"

class Screen:
    def __init__(self, memory):
        self.memory = memory

    def refresh(self):
        print("\n".join(
            ["".join(map(chr,self.memory[1024 + i*40: 1024 + i*40 + 39])) for i in range(0, 24, 40)])
        )


class Machine:
    def __init__(self, cpu, screen):
        self.cpu = cpu
        self.memory = cpu.memory
        self.screen = screen(self.memory)

if __name__ == '__main__':
    c64 = Machine(CPU(BytearrayMemory(65536)), Screen)
    c64.memory[0] = 42
    c64.memory[1024] = 65
    c64.cpu.fetch()
    print(c64.memory)
    print(c64.cpu)
    c64.screen.refresh()
    c64.memory[1024] = 66
    c64.screen.refresh()

