from datetime import datetime

from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
# noinspection PyUnresolvedReferences
from .constants import *


class Screen:
    memory = None
    display = None
    buffer = None
    font_cache = None

    def init(self):
        pass
        self.memory.write_watchers.append((0x0400, 0x07FF, self.refresh))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.get_registers))

        pygame.init()
        self.display = pygame.display.set_mode((480, 312))  # , flags=pygame.SCALED)
        self.buffer = pygame.Surface((320, 200), depth=8)
        self.buffer.set_palette([[q >> 16, (q >> 8) & 0xFF, q & 0xFF, 0xFF] for q in COLORS])

        self.display.fill("0x877BDFFF")

        self.buffer.fill(6)
        self.display.blit(self.buffer, (80, 56))
        pygame.display.flip()

        self.font_cache = []
        self.cache_fonts()

    def cache_fonts(self):
        chargen = [self.memory[a] for a in range(0xD000, 0xE000)]  # Slow read... fix in memory.py
        for i in range(512):
            matrix = chargen[i * 8:(i + 1) * 8]
            font = pygame.Surface((8, 8))
            for r, row in enumerate(matrix):
                for c, bit in enumerate(f"{row:08b}"):
                    font.set_at((c, r), (255, 255, 255, 255) if bit == "1" else (0, 0, 0, 0))
            font.set_colorkey((0, 0, 0))
            self.font_cache.append(font)
        pass

    def refresh(self, address, value):
        # Out of screen: skip (but mapped anyway)
        if address > 0x07e7:
            return

        char = self.font_cache[value + 256]
        coords = ((address - 0x400) % 40) * 8 + 80, int((address - 0x400) / 40) * 8 + 56

        pygame.draw.rect(self.display, pygame.Color("0x000000FF"), pygame.rect.Rect(coords, (8, 8)))
        self.display.blit(char, coords)  # Center screen
        pygame.display.flip()

    def get_registers(self, address, value):
        if address == 0xD012:
            t = int((datetime.now().microsecond % 20000) / 20000 * 312)
            return t & 0xFF
        elif address == 0xD011:
            return int(int((datetime.now().microsecond % 20000) / 20000 * 312) > 0xFF)

        if address == 0xD019:
            return 1  # Temporary, to be completed


if __name__ == '__main__':
    s = Screen()
    s.memory = bytearray(65536)
    s.init()
    pass
