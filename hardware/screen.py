from datetime import datetime

from .constants import BITRANGE, COLORS, PALETTE, VIDEO_SIZE

from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame  # noqa -- weird pygame

TRANSPARENT_COLOR = pygame.color.Color(1, 254, 0)


# noinspection PyUnresolvedReferences

class VIC_II:
    """
    Abstraction of VIC-II and its registers
    """

    def __init__(self, memory):
        self.memory = memory
        self.memory[0xD020] = 0x0E  # Default border color

        # Watchers
        self.memory.write_watchers.append((0xD000, 0xD3FF, self.set_registers))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.get_registers))

        # Registers
        self.pointer_character_memory = 0x0000
        self.pointer_bitmap_memory = 0x0000
        self.pointer_screen_memory = 0x0000

        self.irq_raster_enabled = 0
        self.irq_sprite_background_collision_enabled = 0
        self.irq_sprite_sprite_collision_enabled = 0

        self.irq_raster_line = 0
        self.irq_raster_enabled = 1
        self.irq_sprite_background_collision_enabled = 1
        self.irq_sprite_sprite_collision_enabled = 1
        self.irq_status_register = 0

    def step(self):
        pass

    def get_registers(self, address, value):
        if address == 0xD011:
            """
            Bits #0-#2: Vertical raster scroll.
            Bit #3: Screen height; 0 = 24 rows; 1 = 25 rows.
            Bit #4: 0 = Screen off, complete screen is covered by border; 
                    1 = Screen on, normal screen contents are visible.
            Bit #5: 0 = Text mode; 1 = Bitmap mode.
            Bit #6: 1 = Extended background mode on.
            Bit #7: Read: Current raster line (bit #8).

            Write: Raster line to generate interrupt at (bit #8).

            Default: $1B, %00011011.
            """
            return self.memory.read(0XD011) & 0b0111111 + ((self.raster_y > 0xFF) << 7)

        elif address == 0xD012:
            return self.raster_y & 0xFF

        elif address == 0xD019:
            return 1  # Temporary, to be completed
        return value

    def set_registers(self, address, value):
        if address == 0xD011 and False:
            # Set bit 8 of irq_raster_line
            self.irq_raster_line = (value & 0b10000000) << 1 | (self.irq_raster_line & 0xFF)

        elif address == 0xD018:
            # self.video_matrix_base_address = (value & 0b11110000) >> 4
            self.font_data_base_address = (value & 0b00001110) >> 1
            self.VMCSN_unused = value & 1

        elif address == 0xD01A:
            self.irq_raster_enabled = value & 0b0001
            self.irq_sprite_background_collision_enabled = value & 0b0010
            self.irq_sprite_sprite_collision_enabled = value & 0b0100

    @property
    def memory_bank(self):
        # Bits in the VIC bank register are inverted
        return (3 - self.memory[0xDD00] & 0b11) << 6

    @property
    def video_matrix_base_address(self):
        return self.memory_bank + (self.memory[0xD018] & 0b11110000) << 6

    @property
    def character_generator_base_address(self):
        return self.memory_bank + (self.memory[0xD018] & 0b00001110) << 10

    @property
    def Y_SCROLL(self):
        # 0XD011 bits #0-2
        return self.memory[0xD011] & 0x07

    @property
    def RSEL(self):
        # 0XD011 bit #3
        return bool(self.memory[0xD011] & 0xb1000)

    @property
    def DEN(self):
        # 0XD011 bit #4
        return bool(self.memory[0xD011] & 0b00010000)

    @property
    def bitmap_mode(self):
        # 0XD011 bit #5
        return bool(self.memory[0XD011] & 0b10000)

    @property
    def extended_background(self):
        # 0XD011 bit #6
        return bool(self.memory[0XD011] & 0b100000)

    @property
    def X_SCROLL(self):
        # 0XD016 bits #0-2
        return self.memory[0xD016] & 0x07

    @property
    def CSEL(self):
        # 0XD016 bit #3
        return bool(self.memory[0xD016] & 0b1000)

    @property
    def multicolor_mode(self):
        # 0XD016 bit #3
        return bool(self.memory[0xD016] & 0b10000)

    @property
    def border_color(self):
        return self.memory[0xD020] & 0x0F

    @property
    def background_color(self):
        return self.memory[0xD021] & 0x0F

    @property
    def background_color_1(self):
        return self.memory[0xD022] & 0x0F

    @property
    def background_color_2(self):
        return self.memory[0xD023] & 0x0F

    @property
    def background_color_3(self):
        return self.memory[0xD024] & 0x0F


class RasterScreen(VIC_II):
    CAPTION = "Commodore 64 (Raster) {:.1f} FPS"

    DISPLAY_START = 0x30
    DISPLAY_END = 0xF7

    H_VISIBLE_START = 0
    FIRST_COLUMN = [31, 24]
    LAST_COLUMN = [334, 343]
    H_VISIBLE_END = 414
    H_LAST = VIDEO_SIZE[0]

    V_VISIBLE_START = 15
    FIRST_LINE = [55, 51]
    LAST_LINE = [246, 250]
    V_VISIBLE_END = 299
    V_LAST = VIDEO_SIZE[1]

    def __init__(self, memory):
        super().__init__(memory)

        self.raster_x = 0
        self.raster_y = 0
        self.char_buffer = bytearray([32] * 40)
        self.color_buffer = bytearray([0] * 40)

        self._frame_on = True

        self.frame = pygame.Surface(VIDEO_SIZE)

    def step(self):
        if self.raster_x == 0 and self.DISPLAY_START <= self.raster_y <= self.DISPLAY_END and self._frame_on:
            if self.raster_y % 8 == self.Y_SCROLL:
                # Fetch chars and colors from memory
                # (the infamous bad line)
                # TODO: make base pointer parametric (char only, color is fixed)
                char_pointer = 0X0400 + (self.raster_y - self.DISPLAY_START) // 8 * 40
                color_pointer = 0XD800 + (self.raster_y - self.DISPLAY_START) // 8 * 40

                self.char_buffer = self.memory.get_slice(char_pointer, char_pointer + 40)
                self.color_buffer = self.memory.get_slice(color_pointer, color_pointer + 40)

        if (self.FIRST_LINE[self.RSEL] <= self.raster_y <= self.LAST_LINE[self.RSEL]
                and
                self.FIRST_COLUMN[self.CSEL] <= self.raster_x <= self.LAST_COLUMN[self.CSEL]
                and self._frame_on):
            # Raster is in the pixelated area
            # Get pixel data
            char_col = (self.raster_x - self.FIRST_COLUMN[1]) // 8  # 24 is always the first column for char data
            if self.raster_y <= self.DISPLAY_END + self.Y_SCROLL:  # Note: counting 200 lines would be better
                chargen = self.memory.get_chargen()
                vertical_scroll_pointer = (self.raster_y - self.Y_SCROLL) % 8

                # Get pixel data for two characters
                if char_col > 0:
                    byte_left = chargen[self.char_buffer[char_col - 1] * 8 + vertical_scroll_pointer]
                else:
                    # Left column empty
                    byte_left = 0

                byte_right = chargen[self.char_buffer[char_col] * 8 + vertical_scroll_pointer]

                # Combine 2 byte of pixel data into 1 scrolled byte
                pixels = (byte_left << (8 - self.X_SCROLL) | byte_right >> self.X_SCROLL)
            else:
                # Empty bottom partial row
                pixels = 0

            # Draw pixels
            for i, bit in BITRANGE:
                self.frame.set_at((self.raster_x + i, self.raster_y),
                                  COLORS[self.color_buffer[char_col] & 0x0F] if pixels & bit
                                  else COLORS[self.background_color])

        elif (self.H_VISIBLE_START <= self.raster_x <= self.H_VISIBLE_END and
              self.V_VISIBLE_START <= self.raster_y <= self.V_VISIBLE_END):
            # Raster is in the visible border
            self.frame.fill(PALETTE[self.border_color], (self.raster_x, self.raster_y, 8, 1))
            # TODO: use pixel-perfect borders with fine column check (and flip-flop), not raw byte advance

        # else:
        # Raster is in the invisible area
        # Do nothing
        # self.display.fill((0,0,0), rect)

        if self.raster_x >= self.H_LAST:
            # Line is complete
            self.raster_x = 0
            if self.raster_y >= self.V_LAST:
                # Frame is complete
                self.raster_y = 0
                # Check if the next frame is blank
                # This is checked once a frame
                self._frame_on = self.DEN
                # Clear line buffers
                self.char_buffer = bytearray([32] * 40)
                self.color_buffer = bytearray([0] * 40)
                return_frame = self.frame
                self.frame = pygame.Surface(VIDEO_SIZE)
                return return_frame
            else:
                # Advance next scanline
                self.raster_y += 1

        else:
            # Advance next pixel pack
            self.raster_x += 8


class LazyScreen(VIC_II):
    """
    Screen Q&D meta-emulator
    Just draws chars and their colors, background and borders
    No raster, sprites or other fancy features
    """
    CAPTION = "Commodore 64 (Simple screen)"

    def __init__(self, memory):
        super().__init__(memory)

        # Watchers
        self.memory.write_watchers.append((0x0400, 0x07E7, self.char_code))
        self.memory.write_watchers.append((0xD800, 0xDBE7, self.char_color))

        self.transparent_color = pygame.color.Color(1, 254, 0)

        self.background_pos_full = [41, 42]
        self.background_pos_small = [46, 47]
        self.extra_borders = (7, 4)

        self.buffer_size = (320, 200)
        self.display_size = (403, 284)

        # pygame.init()
        pygame.display.set_caption(self.CAPTION)

        # Display is the entire window drawn - visible area
        self.display = pygame.display.set_mode(self.display_size, flags=pygame.DOUBLEBUF)

        # Buffer is the actual memory buffer
        self.buffer = pygame.Surface(self.buffer_size)
        self.buffer.set_colorkey(self.transparent_color)

        self.font_cache = []
        self.cache_fonts()

        self.refresh()

    @property
    def raster_y(self):
        return int((datetime.now().microsecond % 20000) / 20000 * 312)

    def refresh(self, area: pygame.Rect = None):
        # Refresh entire display. Relatively slow unless update area is specified

        # Clear display
        self.display.fill(PALETTE[self.border_color])

        # Draw centered background (with video buffer) centered on display
        self.display.blit(self.buffer, self.background_pos_full, (0, 0, 320, 200))

        # Update
        if area:
            area.move_ip(self.background_pos_full)
            # pygame.draw.rect(self.display, (255, 0, 0), area, width=1)
            pygame.display.update(area)  # Updates full screen????
        else:
            pygame.display.flip()

    def dump(self):
        for attr in dir(self):
            if hasattr(self, attr):
                print("obj.%s = %s" % (attr, getattr(self, attr)))

    def cache_fonts(self):
        chargen = self.memory.get_chargen()  # Dirty trick to speed up things
        for i in range(512):
            matrix = chargen[i * 8:(i + 1) * 8]

            char_colors = []
            for color in PALETTE:
                font = pygame.Surface((8, 8))
                for r, row in enumerate(matrix):
                    for c, bit in enumerate(f"{row:08b}"):
                        font.set_at((c, r), color if bit == "1" else self.transparent_color)
                char_colors.append(font)
                font.set_colorkey(self.transparent_color)

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
        if screen_update:
            self.refresh(char_rect)

    def refresh_buffer(self):
        self.buffer.fill(PALETTE[self.background_color])
        for i in range(0x0400, 0x7E8):
            self.set_char(i, self.memory[i], self.memory[i - 0x400 + 0xD800], screen_update=False)
        self.refresh()

    def set_registers(self, address, value):
        super().set_registers(address, value)
        if address == 0xD011:
            self.refresh()

        elif address == 0xD016:
            self.refresh()

        elif address == 0xD020:
            self.refresh()

        elif address == 0xD021:
            self.buffer.fill(PALETTE[self.background_color])
            self.refresh_buffer()


class TextScreen(VIC_II):
    """
    Text only screen driver, just text
    """
    VIDEO_SIZE = (504, 312)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visible_rect = pygame.rect.Rect(2, 15, 403, 299)
        self.window_rect = pygame.rect.Rect(24, 51, 320, 200)

        self.clock_counter = 0
        self.font_cache = self.cache_fonts()

    @property
    def raster_y(self):
        return int((datetime.now().microsecond % 20000) / 20000 * 312)

    def cache_fonts(self):
        cache = []
        chargen = self.memory.get_chargen()
        for i in range(512):
            matrix = chargen[i * 8:(i + 1) * 8]

            char_colors = []
            for color in PALETTE:
                font = pygame.Surface((8, 8))
                for r, row in enumerate(matrix):
                    for c, bit in enumerate(f"{row:08b}"):
                        font.set_at((c, r), color if bit == "1" else TRANSPARENT_COLOR)
                char_colors.append(font)
                font.set_colorkey(TRANSPARENT_COLOR)

            cache.append(char_colors)
        return cache

    def step(self) -> pygame.Surface:
        if self.clock_counter > 18656:  # Screen on - no sprites
            self.clock_counter = 0
            char_base = self.video_matrix_base_address
            frame = pygame.Surface(self.VIDEO_SIZE, )
            # self.display.fill((0, 0, 0))
            pygame.draw.rect(frame, PALETTE[self.border_color], self.visible_rect)
            if self.DEN:
                # Display is enabled
                pygame.draw.rect(frame, PALETTE[self.background_color], self.window_rect)
                for col in range(40):
                    for row in range(25):
                        pos = row * 40 + col
                        charcode = self.memory[char_base + pos]
                        color = self.memory[0xD800 + pos]
                        frame.blit(self.font_cache[charcode][color], (col * 8 + 24, row * 8 + 51))

            return frame
        self.clock_counter += 1
