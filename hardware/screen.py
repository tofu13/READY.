import numpy as np

from .constants import CLOCKS_PER_FRAME, VIDEO_SIZE


class VIC_II:
    """
    Abstraction of VIC-II and its registers
    """
    def __init__(self, memory):
        self.memory = memory

        # Registers

        self.irq_raster_enabled = 0
        self.irq_sprite_background_collision_enabled = 0
        self.irq_sprite_sprite_collision_enabled = 0

        self.irq_raster_line = 0
        self.irq_raster_enabled = 1
        self.irq_sprite_background_collision_enabled = 1
        self.irq_sprite_sprite_collision_enabled = 1
        self.irq_status_register = 0

        self.extended_background = False
        self.bitmap_mode = False
        self.DEN = False
        self.RSEL = False
        self.Y_SCROLL = 3
        self.multicolor_mode = False
        self.CSEL = True
        self.X_SCROLL = 0
        self.video_matrix_base_address = 0x0400
        self.character_generator_base_address = 0xC000
        self.border_color = 0x0E
        self.background_color = 0x06
        self.background_color_1 = 0x03
        self.background_color_2 = 0x04
        self.background_color_3 = 0x05

        self.memory.write_watchers.append((0xD000, 0XD3FF, self.write_registers))
        self.memory[0x0400:0x0800] = [1] * 1024
        self.memory[0xD800:0xDC00] = [0xE] * 1024

    def clock(self, clock_counter: int):
        pass

    def write_registers(self, address: int, value: int):
        # The VIC registers are repeated each 64 bytes in the area $d000-$d3ff
        address &= 0x3F
        match address:
            case 0x11:
                self.extended_background = bool(value & 0b01000000)
                self.bitmap_mode = bool(value & 0b00100000)
                self.DEN = bool(value & 0b00010000)
                self.RSEL = bool(value & 0b00001000)
                self.Y_SCROLL = value & 0b00000111
            case 0x16:
                self.multicolor_mode = bool(value & 0b10000)
                self.CSEL = bool(value & 0b1000)
                self.X_SCROLL = value & 0xb111
            case 0x18:
                self.video_matrix_base_address = (value & 0b11110000) << 6
                self.character_generator_base_address = (value & 0b00001110) << 10
            case 0x20:
                self.border_color = value
            case 0x21:
                self.background_color = value
            case 0x22:
                self.background_color_1 = value
            case 0x23:
                self.background_color_2 = value
            case 0x24:
                self.background_color_3 = value


class RasterScreen(VIC_II):
    CAPTION = "Commodore 64 (Raster) {:.1f} FPS"

    SCAN_AREA = [504, 312]

    FIRST_COLUMN = [31, 24]
    LAST_COLUMN = [334, 343]

    FIRST_LINE = [55, 51]
    LAST_LINE = [246, 250]

    def __init__(self, memory):
        super().__init__(memory)

        self.raster_x = 0
        self.raster_y = 0
        self.char_buffer = bytearray([1] * 40)
        self.color_buffer = bytearray([0] * 40)

        self._frame_on = self.DEN

        self.frame = np.zeros(VIDEO_SIZE, dtype="uint8")
        self.dataframe = np.empty(shape=(VIDEO_SIZE[0] // 8 + 1, VIDEO_SIZE[1], 3),
                                  dtype="uint8")  # +1 cause partial byte @ 403

    def clock(self, clock_counter: int):
        if self.raster_x < VIDEO_SIZE[0] and self.raster_y < VIDEO_SIZE[1]:
            # Raster is in the visible area
            raster_x__8 = self.raster_x // 8
            if self._frame_on:
                # Display
                if (24 <= self.raster_x <= 343 and
                        51 <= self.raster_y <= 250):
                    # Raster is in the display area
                    # Bad lines
                    if self.raster_x == 24 and ((self.raster_y - 51) % 8 == 0):
                        char_pointer = self.video_matrix_base_address + (self.raster_y - 51) // 8 * 40
                        color_pointer = 0XD800 + (self.raster_y - 51) // 8 * 40

                        # TODO: optimize these reads
                        self.char_buffer = bytearray(
                            self.memory.vic_read(i) for i in range(char_pointer, char_pointer + 40))
                        self.color_buffer = bytearray(
                            self.memory.vic_read(i) for i in range(color_pointer, color_pointer + 40))

                    char = self.char_buffer[(self.raster_x - 24) // 8]
                    color = self.color_buffer[raster_x__8 - 24 // 8]
                    pixels = self.memory.roms["chargen"][char * 8 + (self.raster_y - 51) % 8]

                    # TODO: XY SCROLL
                    self.dataframe[raster_x__8, self.raster_y] = [pixels, self.background_color, color]

                    # Narrow border
                    # TODO: use flip-flop
                    if self.raster_y < self.FIRST_LINE[self.RSEL] or self.raster_y > self.LAST_LINE[self.RSEL]:
                        # TODO: draw partial horizontal border
                        self.dataframe[raster_x__8, self.raster_y] = [0, self.border_color, 0]
            else:
                # Border
                self.dataframe[raster_x__8, self.raster_y] = [0, self.border_color, 0]

        self.raster_x += 8
        if self.raster_x > self.SCAN_AREA[0]:
            self.raster_x = 0
            # TODO: move into read_registers
            self.memory[0xD012] = self.raster_y & 0xFF
            self.raster_y += 1
            if self.raster_y >= self.SCAN_AREA[1]:
                self.raster_y = 0
                self._frame_on = self.DEN
                return (np.where(
                    # For each bit == pixel
                    np.unpackbits(self.dataframe[:, :, 0], axis=0) == 0,
                    # If zero its background color
                    np.repeat(self.dataframe[:, :, 1], 8, axis=0),
                    # If one its foreground color
                    np.repeat(self.dataframe[:, :, 2], 8, axis=0)))


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
