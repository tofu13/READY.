import asyncio
from datetime import datetime

class Screen:
    memory = None

    def init(self):
        pass
    #   self.memory.write_watchers.append([0x0100, 0x07FF, self.refresh])
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.get_registers))

    def refresh(self, address, value):
        print("\n".join(
            ["".join(map(chr,self.memory[1024 + i*40: 1024 + i*40 + 39])) for i in range(0, 24, 40)])
        )
        return value

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

