import asyncio
from datetime import datetime
from os import system

import pygame
# noinspection PyUnresolvedReferences
import cbmcodecs

class Screen:
    memory = None

    def init(self):
        pass
        self.memory.write_watchers.append((0x0400, 0x07FF, self.refresh))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.get_registers))
        pygame.init()
        self.display = pygame.display.set_mode((320, 200), depth=8)#, flags=pygame.SCALED)
        self.font = pygame.font.Font("PetMe64.ttf", 8)


    def refresh(self, address, value):
        pass
        p = self.font.render(bytes([value]).decode('screencode-c64-uc'), 1, pygame.color.Color("White"))
        coords = ((address - 0x400) % 40)*8, int((address - 0x400) / 40)*8
        self.display.blit(p, coords)
        pygame.display.flip()
        #system("clear")
        screen_memory = self.memory.read(slice(0x400, 0x7FF))
        #print("\n".join(
        #    [screen_memory[i*40: (i+1) * 40].decode('ascii') for i in range(25)])
        #)


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

