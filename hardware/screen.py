import asyncio
from datetime import datetime
from os import system

class Screen:
    memory = None

    def init(self):
        pass
        self.memory.write_watchers.append((0x0400, 0x07FF, self.refresh))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.get_registers))

    def refresh(self, address, value):
        system("clear")
        screen_memory = self.memory.read(slice(0x400, 0x7FF))
        print("\n".join(
            [screen_memory[i*40: (i+1) * 40].decode('ascii') for i in range(25)])
        )

    def get_registers(self, address, value):
        if address == 0xD012:
            t = int((datetime.now().microsecond % 20000) /20000 * 312)
            return t & 0xFF
        elif address == 0xD011:
            return int(int((datetime.now().microsecond % 20000) /20000 * 312) > 0xFF)

        if address == 0xD019:
            return 1 # Temporary, to be completed


if __name__ == '__main__':
    s =Screen()
    s.memory = bytearray(65536)
    s.init()
    pass

