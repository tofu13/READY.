import numpy as np

from .constants import CLOCKS_PER_FRAME, VIDEO_SIZE


class VIC_II:
    """
    Abstraction of VIC-II and its registers
    """

    def __init__(self, memory):
        self.memory = memory
        self.memory[0xD020] = 0x0E  # Default border color

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

    def clock(self, clock_counter: int):
        pass

    @property
    def memory_bank(self):
        # Bits in the VIC bank register are inverted
        return (3 - self.memory.read(0xDD00) & 0b11) << 6

    @property
    def video_matrix_base_address(self):
        return self.memory_bank + (self.memory.read(0xD018) & 0b11110000) << 6

    @property
    def character_generator_base_address(self):
        return self.memory_bank + (self.memory[0xD018] & 0b00001110) << 10

    @property
    def Y_SCROLL(self):
        # 0XD011 bits #0-2
        return self.memory.read(0xD011) & 0x07

    @property
    def RSEL(self):
        # 0XD011 bit #3
        return bool(self.memory[0xD011] & 0xb1000)

    @property
    def DEN(self):
        # 0XD011 bit #4
        return bool(self.memory.read(0xD011) & 0b00010000)

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
        return self.memory.read(0xD016) & 0x07

    @property
    def CSEL(self):
        # 0XD016 bit #3
        return bool(self.memory.read(0xD016) & 0b1000)

    @property
    def multicolor_mode(self):
        # 0XD016 bit #3
        return bool(self.memory[0xD016] & 0b10000)

    @property
    def border_color(self):
        return self.memory.read(0xD020) & 0x0F

    @property
    def background_color(self):
        return self.memory.read(0xD021) & 0x0F

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

        self._frame_on = self.DEN

        self.frame = np.zeros(VIDEO_SIZE, dtype="uint8")

    def clock(self, clock_counter: int):
        if self.raster_x == 0 and self.DISPLAY_START <= self.raster_y <= self.DISPLAY_END and self._frame_on:
            if self.raster_y % 8 == self.Y_SCROLL:
                # Fetch chars and colors from memory
                # (the infamous bad line)
                char_pointer = self.video_matrix_base_address + (self.raster_y - self.DISPLAY_START) // 8 * 40
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
            pixel_data = np.unpackbits(np.array(pixels, dtype="uint8")) * self.color_buffer[char_col]
            self.frame[self.raster_x:self.raster_x + 8, self.raster_y] = np.where(pixel_data == 0,
                                                                                  self.background_color, pixel_data)

        elif (self.H_VISIBLE_START <= self.raster_x <= self.H_VISIBLE_END and
              self.V_VISIBLE_START <= self.raster_y <= self.V_VISIBLE_END):
            # Raster is in the visible border
            self.frame[self.raster_x:self.raster_x + 8, self.raster_y] = self.border_color
            # TODO: use pixel-perfect borders with fine column check (and flip-flop), not raw byte advance

        # else:
        # Raster is in the invisible area
        # Do nothing
        # self.display.fill((0,0,0), rect)

        if self.raster_x >= self.H_LAST:
            # Line is complete
            self.raster_x = 0
            if self.raster_y >= self.V_LAST - 1:  # TODO: wrong
                # Frame is complete
                self.raster_y = 0
                # Check if the next frame is blank
                # This is checked once a frame
                self._frame_on = self.DEN
                # Clear line buffers
                self.char_buffer = bytearray([32] * 40)
                self.color_buffer = bytearray([0] * 40)
                return self.frame
            else:
                # Advance next scanline
                self.raster_y += 1
                self.memory.write(0xD012, self.raster_y & 0xFF)

        else:
            # Advance next pixel pack
            self.raster_x += 8


class VirtualScreen(VIC_II):
    """
    No display
    """

    def clock(self, clock_counter: int):
        pass

    @property
    def raster_y(self):
        return 0


class FastScreen(VIC_II):
    """
    Screen driver using numpy
    Text only, fast
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font_cache = self.cache_fonts()

    def cache_fonts(self):
        cache = []
        chargen = self.memory.get_chargen()
        for i in range(512):
            matrix = chargen[i * 8: (i + 1) * 8]
            font_array = np.array(matrix, dtype="uint8")
            font = np.unpackbits(font_array).reshape(8, 8).T
            cache.append(font)
        return cache

    def clock(self, clock_counter: int) -> np.array:
        if clock_counter % CLOCKS_PER_FRAME == 0:
            frame = np.ones(VIDEO_SIZE, dtype="uint8") * self.border_color

            if self.DEN:
                char_base = self.video_matrix_base_address
                charcodes = np.array(self.memory.get_slice(char_base, char_base + 1000))
                colors = np.array(self.memory.get_slice(0xD800, 0xD800 + 1000))
                chars = (
                    # Compose frame pixels
                    np.hstack(
                        [
                            # From chargen, with color applied
                            self.font_cache[code].T * colors[i]
                            # From screen codes
                            for i, code in np.ndenumerate(charcodes)
                        ]
                    )
                    # reorganize as 320 columns
                    .reshape(8, -1, 320)
                    .swapaxes(0, 1)
                    .reshape(-1, 320)
                    .T
                )
                chars = np.where(chars == 0, self.background_color, chars)
                frame[24:344, 51:251] = chars
            self.memory.write(0xD012, 0)  # This lets the system boot (see $FF5E)
            return frame

    @property
    def raster_y(self):
        return 0
