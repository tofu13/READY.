from .constants import *
import time

class CIAA:
    memory = None
    def init(self):
        self.memory.read_watchers.append((0xDC00, 0xDCFF, self.get_registers))
        self.memory.write_watchers.append((0xDC00, 0xDCFF, self.set_registers))

    def loop(self, memory):
        while True:
            print(memory[1034])
            time.sleep(1)


    def get_registers(self, address, value):
        print("read ciaA", address)
        return value
    def set_registers(self, address, value):
        print("write ciaA", address, value)

class CIAB:
    memory = None
    def init(self):
        self.memory.read_watchers.append((0xDD00, 0xDDFF, self.get_registers))
        self.memory.write_watchers.append((0xDD00, 0xDDFF, self.set_registers))

    def loop(self, memory):
        while True:
            memory[0] = 255
            time.sleep(1)


    def get_registers(self, address, value):
        print("read ciaA", address)
        return value
    def set_registers(self, address, value):
        print("write ciaA", address, value)
