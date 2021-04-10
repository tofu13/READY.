from datetime import datetime

from .constants import *

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
# noinspection PyUnresolvedReferences


class Screen:
    def __init__(self, memory):
        self.memory = memory

        self.memory.write_watchers.append((0x0400, 0x07E7, self.char_code))
        self.memory.write_watchers.append((0xD800, 0xDBE7, self.char_color))
        self.memory.write_watchers.append((0xD000, 0xD3FF, self.set_registers))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.get_registers))

        self.border_color = 14
        self.background_color = 6
        self.palette = [[c >> 16, (c >> 8) & 0xFF, c & 0xFF] for c in COLORS]
        self.buffer_pos = (80, 56)
        self.buffer_size = (320, 200)

        pygame.init()

        # Listen for keyboard events enly
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([pygame.KEYDOWN, pygame.KEYUP, pygame.QUIT])

        self.display = pygame.display.set_mode((480, 312))  # , flags=pygame.SCALED)
        self.buffer = pygame.Surface(self.buffer_size)

        self.display.fill(PALETTE[self.border_color])

        self.buffer.fill(PALETTE[self.background_color])
        self.display.blit(self.buffer, self.buffer_pos)
        pygame.display.flip()

        self.font_cache = []
        self.cache_fonts()

    def cache_fonts(self):
        chargen = self.memory.get_chargen()  # Dirty trick to speed up things
        for i in range(512):
            matrix = chargen[i * 8:(i + 1) * 8]

            char_colors = []
            for color in PALETTE:
                font = pygame.Surface((8, 8)).convert_alpha()
                for r, row in enumerate(matrix):
                    for c, bit in enumerate(f"{row:08b}"):
                        font.set_at((c, r), (*color, 255) if bit == "1" else (*color, 0))
                char_colors.append(font)
            self.font_cache.append(char_colors)

    def char_code(self, address, value):
        self.refresh(address, value, color=self.memory[address - 0x0400 + 0xD800] & 0x0F)

    def char_color(self, address, value):
        self.refresh(address - 0xD800 + 0x400, self.memory[address - 0xD800 + 0x400], color=value & 0x0F)

    def refresh(self, address, value, color):
        char = self.font_cache[value][color]
        coords = ((address - 0x400) % 40) * 8, int((address - 0x400) / 40) * 8

        # pygame.draw.rect(self.buffer, PALETTE[self.background_color], pygame.rect.Rect(coords, (8, 8)))
        self.buffer.fill(PALETTE[self.background_color], char.get_rect().move(coords))
        self.buffer.blit(char, coords)
        self.display.blit(self.buffer, self.buffer_pos)
        pygame.display.update(char.get_rect().move(coords).move(self.buffer_pos))
        # pygame.display.flip()

    def get_registers(self, address, value):
        if address == 0xD012:
            t = int((datetime.now().microsecond % 20000) / 20000 * 312)
            return t & 0xFF
        elif address == 0xD011:
            return int(int((datetime.now().microsecond % 20000) / 20000 * 312) > 0xFF)

        if address == 0xD019:
            return 1  # Temporary, to be completed
        return value

    def set_registers(self, address, value):
        if address == 0xD020:
            self.border_color = value & 0x0F
            self.display.fill(PALETTE[self.border_color])
            self.display.blit(self.buffer, self.buffer_pos)
            pygame.display.flip()

        elif address == 0xD021:
            self.background_color = value & 0x0F
            return

            pygame.draw.rect(self.display, PALETTE[self.background_color],
                             pygame.rect.Rect(self.buffer_pos, self.buffer_size))
            self.display.blit(self.buffer, self.buffer_pos)
            pygame.display.update(self.buffer.get_rect())


if __name__ == '__main__':
    s = Screen()
    s.memory = bytearray(65536)
    s.init()
    pass
