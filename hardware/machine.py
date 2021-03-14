from multiprocessing import Process, Pipe

class Machine:
    def __init__(self, memory, cpu, screen, roms, ciaA):
        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.roms = roms
        self.ciaA = ciaA

        pipeA, pipeB =  Pipe()
        self.cpu.memory = self.memory
        self.cpu.pipe = pipeA

        self.memory.roms = self.roms.contents

        self.screen.memory = self.memory
        self.screen.init()
        self.screen.pipe = pipeB
        #Process(target=screen.loop, args=(self.memory,)).start()

        self.ciaA.memory = self.memory
        self.ciaA.init()
        self.ciaA.pipe = pipeB
        Process(target=ciaA.loop, args=(self.memory,)).start()

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
