import pickle

from hardware.constants import *
from hardware import monitor


class Machine:
    def __init__(self, memory, cpu, screen, ciaA):

        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.ciaA = ciaA

        self.monitor = monitor.Monitor(self)
        self.monitor_active = False

        # Default processor port (HIRAM, LORAM, CHARGEN = 1)
        self.memory[0] = 47
        self.memory[1] = 55

        self.input_buffer = ""

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
            # Activate monitor on events

            self.monitor_active |= self.cpu.PC in self.cpu.breakpoints

            try:
                self.screen.step()

                # Execute current instruction
                running = self.cpu.step()

                # Run CIA A, save interrupts and special events
                irq, nmi, event = self.ciaA.step()

                if event == "RESET":
                    self.cpu.reset(PC=0xFCE2)
                elif event == "MONITOR":
                    self.monitor_active = True
                    irq = False  # Clear IRQ when opening monitor
                elif event == "QUIT":
                    raise KeyboardInterrupt()

                # Handle CPU lines IRQ and NMI
                if irq:
                    self.cpu.irq()
                if nmi:
                    self.cpu.nmi()

                if self.input_buffer:
                    if self.memory[0xC6] == 0:
                        char = self.input_buffer[0]
                        self.memory[0x0277] = PETSCII.get(char.lower(), 64)  # Temporary (64=@ for unknown char)
                        self.memory[0xC6] = 1
                        self.input_buffer = self.input_buffer[1:]
                # self.screen.refresh # Tentative raster
            # Handle exit
            except KeyboardInterrupt:
                running = False

            if self.monitor_active:
                self.monitor_active = self.monitor.run()

        # BRK encountered, exit

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

            # Memory can not be loaded directly as it is referenced
            self.memory.set_slice(0, pickle.load(f))

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
            # First two bytes are base address for loading into memory (little endian)
            l, h = f.read(2)
            if format_cbm:
                base = h << 8 | l
            data = f.read()
        for i, b in enumerate(data):
            self.memory[base + i] = b
        print(f"Loaded {len(data)} bytes starting at ${base:04X}")
        return base


def DefaultMachine() -> Machine:
    import hardware
    from config import ROMS_FOLDER
    roms = hardware.roms.ROMS(ROMS_FOLDER)
    memory = hardware.memory.BytearrayMemory(65536, roms)
    return Machine(
        memory,
        hardware.cpu.CPU(memory),
        hardware.screen.RasterScreen(memory),
        hardware.cia.CIA_A(memory)
    )
