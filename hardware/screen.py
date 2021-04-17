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

        self.palette = [[c >> 16, (c >> 8) & 0xFF, c & 0xFF] for c in COLORS]
        self.buffer_pos = (41,  42)
        self.buffer_size = (320, 200)
        self.display_size = (403, 284)

        # Registers
        self.pointer_character_memory = 0x0000
        self.pointer_bitmap_memory = 0x0000
        self.pointer_screen_memory = 0x0000

        self.horizontal_raster_scroll = 0
        self.vertical_raster_scroll = 3
        self.full_screen_width = 1
        self.full_screen_height = 1
        self.screen_on = 0
        self.bitmap_mode = 0
        self.multicolor_mode = 0
        self.extended_background_mode = 0

        self.irq_raster_line = 0
        self.irq_raster_enabled = 1
        self.irq_sprite_background_collision_enabled = 1
        self.irq_sprite_sprite_collision_enabled = 1
        self.irq_status_register = 0

        self.border_color = 14
        self.background_color = 6
        self.extra_background_color_1 = 0
        self.extra_background_color_2 = 0
        self.extra_background_color_3 = 0


        pygame.init()
        pygame.display.set_caption("Commodore 64")

        # Listen for keyboard events enly
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([pygame.KEYDOWN, pygame.KEYUP, pygame.QUIT])

        self.display = pygame.display.set_mode(self.display_size)#, flags=pygame.SCALED)
        self.buffer = pygame.Surface(self.buffer_size)

        self.display.fill(PALETTE[self.border_color])

        self.buffer.fill(PALETTE[self.background_color])
        self.display.blit(self.buffer, self.buffer_pos)
        pygame.display.flip()

        self.font_cache = []
        self.cache_fonts()

        # Prepare empty screen
        default_char = 32 # Space
        self.memory.set_slice(0x0400, [default_char] * 1000)
        default_color = 15 # System default
        self.memory.set_slice(0xD800, [default_color] * 1000)

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
        self.set_char(address, value, color=self.memory[address - 0x0400 + 0xD800] & 0x0F)

    def char_color(self, address, value):
        self.set_char(address - 0xD800 + 0x400, self.memory[address - 0xD800 + 0x400], color=value & 0x0F)

    def set_char(self, address, value, color, screen_update=True):
        char = self.font_cache[value][color & 0x0F]
        coords = ((address - 0x400) % 40) * 8, int((address - 0x400) / 40) * 8

        # pygame.draw.rect(self.buffer, PALETTE[self.background_color], pygame.rect.Rect(coords, (8, 8)))
        char_rect = char.get_rect().move(coords)
        self.buffer.fill(PALETTE[self.background_color], char_rect)
        self.buffer.blit(char, coords)
        self.display.blit(self.buffer, self.buffer_pos)
        if screen_update:
            pygame.display.update(char_rect.move(self.buffer_pos))
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
        if address == 0xD011:
            self.vertical_raster_scroll = value & 0b00000111
            self.full_screen_heigth = value & 0b00001000
            self.screen_on = value & 0b00010000
            self.bitmap_mode = value & 0b00100000
            self.extended_background = value & 0b01000000
            # Set bit 8 of irq_raster_line
            self.irq_raster_line = (value & 0b10000000) << 1 | self.irq_raster_line & 0xFF

        elif address == 0xD016:
            self.horizontal_raster_scroll = value & 0b00000111
            self.full_screen_width = value & 0b00001000
            self.multicolor_mode = value & 0b00010000

        elif address == 0xD01A:
            self.irq_raster_enabled = value & 0b0001
            self.irq_sprite_background_collision_enabled = value & 0b0010
            self.irq_sprite_sprite_collision_enabled = value & 0b0100

        elif address == 0xD020:
            self.border_color = value & 0x0F
            self.display.fill(PALETTE[self.border_color])
            self.display.blit(self.buffer, self.buffer_pos)
            pygame.display.flip()

        elif address == 0xD021:
            self.background_color = value & 0x0F
            self.buffer.fill(PALETTE[self.background_color])
            for i in range(0x0400,0x07E8):
                self.set_char(i, self.memory[i], self.memory[i + 0xD800 - 0x400], screen_update=False)
            self.display.blit(self.buffer, self.buffer_pos)
            pygame.display.flip()
            return

            pygame.draw.rect(self.display, PALETTE[self.background_color],
                             pygame.rect.Rect(self.buffer_pos, self.buffer_size))
            self.display.blit(self.buffer, self.buffer_pos)
            pygame.display.update(self.buffer.get_rect())


if __name__ == '__main__':
    s = Screen()
    pass

