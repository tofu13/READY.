class Machine:
    def __init__(self, memory, cpu, screen, roms):
        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.roms = roms

        self.cpu.memory = self.memory

        self.memory.roms = self.roms.contents

        self.screen.memory = self.memory
        self.screen.init()

        self.memory[1] = 0x07

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
