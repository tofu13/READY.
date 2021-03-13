from datetime import datetime
import time

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
    border_color = 14
    background_color = 6
    palette = [[q >> 16, (q >> 8) & 0xFF, q & 0xFF] for q in COLORS]
    buffer_pos = (80, 56)
    buffer_size = (320,200)

    def init(self):
        self.memory.write_watchers.append((0x0400, 0x07FF, self.refresh))
        self.memory.write_watchers.append((0xD000, 0xD3FF, self.set_registers))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.get_registers))

        pygame.init()
        self.display = pygame.display.set_mode((480, 312))  # , flags=pygame.SCALED)
        self.buffer = pygame.Surface(self.buffer_size)

        self.display.fill(PALETTE[self.border_color])

        self.buffer.fill(PALETTE[self.background_color])
        self.display.blit(self.buffer, self.buffer_pos)
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
                    font.set_at((c, r), (255, 255, 255) if bit == "1" else (0, 0, 0))
            font.set_colorkey((0, 0, 0))
            self.font_cache.append(font)
        pass

    def refresh(self, address, value):
        # Out of screen: skip (but mapped anyway)
        if address > 0x07e7:
            return

        char = self.font_cache[value]
        coords = ((address - 0x400) % 40) * 8, int((address - 0x400) / 40) * 8

        pygame.draw.rect(self.buffer, PALETTE[self.background_color], pygame.rect.Rect(coords, (8, 8)))
        #self.buffer.fill(PALETTE[self.background_color], char.get_rect().move(coords))
        self.buffer.blit(char, coords)
        self.display.blit(self.buffer, self.buffer_pos)
        pygame.display.update(char.get_rect().move(coords).move(self.buffer_pos))
        #pygame.display.flip()

    def get_registers(self, address, value):
        if address == 0xD012:
            t = int((datetime.now().microsecond % 20000) / 20000 * 312)
            return t & 0xFF
        elif address == 0xD011:
            return int(int((datetime.now().microsecond % 20000) / 20000 * 312) > 0xFF)

        if address == 0xD019:
            return 1  # Temporary, to be completed

    def set_registers(self, address, value):
        if address == 0xD020:
            self.border_color = value & 0x0F
            self.display.fill(PALETTE[self.border_color])
            self.display.blit(self.buffer, self.buffer_pos)
            pygame.display.flip()


        elif address == 0xD021:
            self.background_color = value & 0x0F
            return

            pygame.draw.rect(self.display, PALETTE[self.background_color], pygame.rect.Rect(self.buffer_pos, self.buffer_size))
            self.display.blit(self.buffer, self.buffer_pos)
            pygame.display.update(self.buffer.get_rect())


if __name__ == '__main__':
    s = Screen()
    s.memory = bytearray(65536)
    s.init()
    pass
