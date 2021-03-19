from multiprocessing import Process, Pipe, Value
import pickle
import asyncio

class Machine:
    def __init__(self, memory, cpu, screen, roms, ciaA):

        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.roms = roms
        self.ciaA = ciaA

        self.cpu.memory = self.memory

        self.memory.roms = self.roms.contents

        self.screen.memory = self.memory
        self.screen.init()

        self.ciaA.memory = self.memory
        self.ciaA.init()

        self.memory[1] = 0x07

    def run(self, address):
        loop = asyncio.get_event_loop()
        event_queue = asyncio.Queue()
        ciaA_IRQ = asyncio.ensure_future(self.ciaA.loop(event_queue))

        self.cpu.PC = address
        cpu_loop = loop.create_task(self.cpu.run(event_queue))

        loop.run_until_complete(cpu_loop)

        ciaA_IRQ.cancel()
        cpu_loop.cancel()

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            machine = cls()
            machine.cpu.A = pickle.load(f)
            machine.cpu.X = pickle.load(f)
            machine.cpu.Y = pickle.load(f)
            machine.cpu.PC = pickle.load(f)
            machine.cpu.SP = pickle.load(f)
            machine.cpu.F = pickle.load(f)
            machine.cpu.memory = pickle.load(f)
        return machine

    def restore(self, filename):
        with open(filename, 'rb') as f:
            self.cpu.A = pickle.load(f)
            self.cpu.X = pickle.load(f)
            self.cpu.Y = pickle.load(f)
            self.cpu.PC = pickle.load(f)
            self.cpu.SP = pickle.load(f)
            self.cpu.F = pickle.load(f)
            self.cpu.memory = pickle.load(f)


    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.cpu.A, f)
            pickle.dump(self.cpu.X, f)
            pickle.dump(self.cpu.Y, f)
            pickle.dump(self.cpu.PC, f)
            pickle.dump(self.cpu.SP, f)
            pickle.dump(self.cpu.F, f)
            pickle.dump(self.memory, f)

    def load(self, filename, base, format_cbm=False):
        with open(filename, 'rb') as f:
            if format_cbm:
                # First two bytes are base address for loading into memory (cbm file format, little endian)
                l, h = f.read(2)
                base = h << 8 | l
            data = f.read()
        for i, b in enumerate(data):
            self.memory[base + i] = b
        print(f"Loaded {len(data)} bytes starting at ${base:04X}")
        return base
