import pickle
import datetime

class Machine:
    def __init__(self, memory, cpu, screen, roms, ciaA):

        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.ciaA = ciaA

        # Default processor port (HIRAM, LORAM, CHARGEN = 1)
        self.memory[1] = 7

    def run(self, address):
        """
        Main process loop
        :param address: address to run from
        """

        # Setup
        self.cpu.F['B'] = 0
        self.cpu.PC = address
        running = True

        while running:
            try:
                # Execute current instruction
                running = self.cpu.step()

                # Run CIA A, save interrupts and special signals
                irq, nmi, reset, quit = self.ciaA.step()

                if reset:
                    self.cpu.PC = 0xFCE2
                if quit:
                    raise KeyboardInterrupt()

                # Handle CPU lines IRQ and NMI
                if irq:
                    self.cpu.irq()
                if nmi:
                    self.cpu.nmi()

            # Handle exit
            except KeyboardInterrupt:
                running = False

        print(f"BRK encountered at ${self.cpu.PC:04X}")


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
            memory = pickle.load(f)
            self.cpu.memory = memory
            self.screen.memory = memory
            self.ciaA.memory = memory

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
