import dataclasses

import numpy as np

from .constants import (
    BITRANGE,
    CLOCKS_PER_FRAME,
    #FIRST_COLUMN,
    FIRST_LINE,
    #LAST_COLUMN,
    LAST_LINE,
    SCAN_AREA_H,
    SCAN_AREA_V,
    VIDEO_SIZE,
    VIDEO_SIZE_H,
    VIDEO_SIZE_V,
)


@dataclasses.dataclass(slots=True)
class Sprite:
    x: int = 0
    y: int = 0
    msb_x: bool = False  # Most significant bit of x coordinate
    enable: bool = False
    expand_x: bool = False
    expand_y: bool = False
    priority: bool = False
    multicolor: bool = False
    color: int = 0

    @property
    def coordinates(self):
        return (self.x + (256 if self.msb_x else 0), self.y)

    @property
    def X(self):
        return self.coordinates[0]

    @property
    def Y(self):
        return self.y


class VIC_II:
    """
    Abstraction of VIC-II and its registers
    """

    __slots__ = [
        "memory",
        "irq_raster_line_lsb",
        "irq_raster_line_msb",
        "irq_raster_enabled",
        "irq_sprite_background_collision_enabled",
        "irq_sprite_sprite_collision_enabled",
        "irq_lightpen_enabled",
        "irq_status_register",
        "irq_raster_occured",
        "irq_sprite_background_collision_occured",
        "irq_sprite_sprite_collision_occured",
        "irq_lightpen_occured",
        "any_irq_enabled",
        "raster_y",
        "extended_background",
        "bitmap_mode",
        "DEN",
        "RSEL",
        "Y_SCROLL",
        "multicolor_mode",
        "CSEL",
        "X_SCROLL",
        "video_matrix_base_address",
        "character_generator_base_address",
        "border_color",
        "background_color",
        "background_color_1",
        "background_color_2",
        "background_color_3",
        "sprite_multicolor_1",
        "sprite_multicolor_2",
        "sprites",
        "_register_cache",
    ]

    def __init__(self, memory):
        self.memory = memory

        # Registers
        self.irq_raster_line_lsb = 0
        self.irq_raster_line_msb = 0
        self.irq_raster_enabled: bool = False
        self.irq_sprite_background_collision_enabled: bool = False
        self.irq_sprite_sprite_collision_enabled: bool = False
        self.irq_lightpen_enabled: bool = False
        self.irq_status_register: int = 0
        self.irq_raster_occured: bool = False
        self.irq_sprite_background_collision_occured: bool = False
        self.irq_sprite_sprite_collision_occured: bool = False
        self.irq_lightpen_occured: bool = False

        self.any_irq_enabled: bool = False
        self.raster_y: int = 0

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
        self.sprite_multicolor_1 = 0x05
        self.sprite_multicolor_2 = 0x05

        self.sprites = [Sprite() for _ in range(8)]

        self.memory.write_watchers.append((0xD000, 0xD3FF, self.write_registers))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.read_registers))

        self._register_cache = bytearray(0x40)

        # self.memory[0x0400:0x0800] = [1] * 1024
        # self.memory[0xD800:0xDC00] = [0xE] * 1024

    @property
    def irq_raster_line(self):
        return self.irq_raster_line_lsb + (0x100 if self.irq_raster_line_msb else 0)

    @property
    def any_irq_occured(self) -> bool:
        return any(
            (
                self.irq_raster_occured,
                self.irq_sprite_background_collision_occured,
                self.irq_sprite_sprite_collision_occured,
                self.irq_lightpen_occured,
            )
        )

    def clock(self, clock_counter: int):
        pass

    def write_registers(self, address: int, value: int):
        # The VIC registers are repeated each 64 bytes in the area $d000-$d3ff
        address &= 0x3F
        # Store value for quick retrival
        self._register_cache[address] = value

        match address:
            case sprite if sprite in {0, 2, 4, 6, 8, 10, 12, 14}:
                self.sprites[sprite // 2].x = value
            case sprite if sprite in {1, 3, 5, 7, 9, 11, 13, 15}:
                self.sprites[sprite // 2].y = value
            case 0x10:
                for i in range(8):
                    self.sprites[i].msb_x = bool(value & BITRANGE[i][1])
            case 0x11:
                self.irq_raster_line_msb = bool(value & 0b10000000)
                self.extended_background = bool(value & 0b01000000)
                self.bitmap_mode = bool(value & 0b00100000)
                self.DEN = bool(value & 0b00010000)
                self.RSEL = bool(value & 0b00001000)
                self.Y_SCROLL = value & 0b00000111
            case 0x12:
                self.irq_raster_line_lsb = value
            case 0x15:
                for i in range(8):
                    self.sprites[i].enable = bool(value & BITRANGE[i][1])
            case 0x16:
                self.multicolor_mode = bool(value & 0b10000)
                self.CSEL = bool(value & 0b1000)
                self.X_SCROLL = value & 0xB111
            case 0x17:
                for i in range(8):
                    self.sprites[i].expand_y = bool(value & BITRANGE[i][1])
            case 0x18:
                self.video_matrix_base_address = (value & 0b11110000) << 6
                self.character_generator_base_address = (value & 0b00001110) << 10
            case 0x19:
                # Ack irqs
                if value & 0b0001:
                    self.irq_raster_occured = False
                if value & 0b0010:
                    self.irq_sprite_background_collision_occured = False
                if value & 0b0100:
                    self.irq_sprite_sprite_collision_occured = False
                if value & 0b1000:
                    self.irq_lightpen_occured = False
            case 0x1A:
                self.irq_raster_enabled = bool(value & 0b0001)
                self.irq_sprite_background_collision_enabled = bool(value & 0b0010)
                self.irq_sprite_sprite_collision_enabled = bool(value & 0b0100)
                self.irq_lightpen_enabled = bool(value & 0b1000)

                self.any_irq_enabled = bool(value & 0b1111)
            case 0x1B:
                for i in range(8):
                    self.sprites[i].priority = bool(value & BITRANGE[i][1])
            case 0x1C:
                for i in range(8):
                    self.sprites[i].multicolor = bool(value & BITRANGE[i][1])
            case 0x1D:
                for i in range(8):
                    self.sprites[i].expand_x = bool(value & BITRANGE[i][1])
            case 0x20:
                self.border_color = value & 0x0F
            case 0x21:
                self.background_color = value & 0x0F
            case 0x22:
                self.background_color_1 = value & 0x0F
            case 0x23:
                self.background_color_2 = value & 0x0F
            case 0x24:
                self.background_color_3 = value & 0x0F
            case 0x25:
                self.sprite_multicolor_1 = value & 0x0F
            case 0x26:
                self.sprite_multicolor_2 = value & 0x0F
            case sprite if 0x27 <= sprite <= 0x2E:
                self.sprites[sprite - 0x27].color = value & 0x0F

    def read_registers(self, address: int, _: int) -> int:
        address &= 0x3F
        match address:
            # Dynamic registers
            case 0x11:
                # Dynamically set bit #7 = bit raster_y bit #8
                # Other bits are cached
                return ((self.raster_y & 0x0100) >> 1) | (
                    self._register_cache[0x11] & 0x7F
                )
            case 0x12:
                return self.raster_y & 0xFF
            case 0x13:
                # Light pen X (MSB only, 2 pixel resolution)
                return 0
            case 0x14:
                # Light pen Y
                return 0
            case 0x19:
                # Interrupts
                interrupts_status = 0
                if self.irq_raster_occured:
                    interrupts_status |= 0b0001
                if self.irq_sprite_background_collision_occured:
                    interrupts_status |= 0b0010
                if self.irq_sprite_sprite_collision_occured:
                    interrupts_status |= 0b0100
                if self.irq_lightpen_occured:
                    interrupts_status |= 0b1000
                if interrupts_status:
                    interrupts_status |= 0b10000000  # Any interrupt occured
                return (
                    interrupts_status | 0b01110000
                )  # (disconnected bits are 1 on read)
            case 0x1E:
                # Sprite sprite collision
                return 0
            case 0x1F:
                # Sprite background collision
                return 0
            # Static register (disconnected bits are 1 on read)
            case 0x16:
                return self._register_cache[0x16] | 0b11000000
            case 0x18:
                return self._register_cache[0x18] | 0b00000001
            case 0x1A:
                return self._register_cache[0x1A] | 0b11110000
            case color if 0x20 <= color <= 0x2E:
                return self._register_cache[color] | 0b11110000
            case other:
                return self._register_cache[other]


class RasterScreen(VIC_II):
    __slots__ = [
        "raster_x",
        "char_buffer",
        "color_buffer",
        "frame",
        "dataframe",
        "_frame_on",
    ]

    def __init__(self, memory):
        super().__init__(memory)

        self.raster_y = 0
        self.raster_x: int = 0
        self.char_buffer = bytearray([1] * 40)
        self.color_buffer = bytearray([0] * 40)

        self._frame_on = self.DEN

        self.frame = np.zeros(VIDEO_SIZE, dtype="uint8")
        self.dataframe = np.empty(
            shape=(VIDEO_SIZE_H // 8 + 1, VIDEO_SIZE_V, 3), dtype="uint8"
        )  # +1 cause partial byte @ 403

    def clock(self, clock_counter: int):
        if self.raster_x < VIDEO_SIZE_H and self.raster_y < VIDEO_SIZE_V:
            # Raster is in the visible area
            raster_x__8 = self.raster_x // 8
            if 24 <= self.raster_x <= 343 and 51 <= self.raster_y <= 250:
                if self._frame_on:
                    # Raster is in the display area
                    # Bad lines
                    if self.raster_x == 24 and ((self.raster_y - 51) % 8 == 0):
                        char_pointer = (
                            self.video_matrix_base_address
                            + (self.raster_y - 51) // 8 * 40
                        )
                        color_pointer = 0xD800 + (self.raster_y - 51) // 8 * 40

                        # TODO: optimize these reads
                        self.char_buffer = bytearray(
                            self.memory.vic_read(i)
                            for i in range(char_pointer, char_pointer + 40)
                        )
                        self.color_buffer = bytearray(
                            self.memory[i]  # Direct read from fixed color ram
                            for i in range(color_pointer, color_pointer + 40)
                        )

                    char = self.char_buffer[(self.raster_x - 24) // 8]
                    color = self.color_buffer[raster_x__8 - 24 // 8]
                    pixels = self.memory.vic_read(
                        self.character_generator_base_address
                        + char * 8
                        + (self.raster_y - 51) % 8
                    )

                    # TODO: XY SCROLL
                    self.dataframe[raster_x__8, self.raster_y] = (
                        pixels,
                        self.background_color,
                        color,
                    )

                    # Narrow border
                    # TODO: use flip-flop
                    if (
                        self.raster_y < FIRST_LINE[self.RSEL]
                        or self.raster_y > LAST_LINE[self.RSEL]
                    ):
                        # TODO: draw partial horizontal border
                        self.dataframe[raster_x__8, self.raster_y] = (
                            0,
                            self.border_color,
                            0,
                        )
                else:
                    # Blank frame
                    self.dataframe[raster_x__8, self.raster_y] = 0, self.border_color, 0
            else:
                # Border
                self.dataframe[raster_x__8, self.raster_y] = 0, self.border_color, 0

        self.raster_x += 8
        if self.raster_x > SCAN_AREA_H:
            self.raster_x = 0
            self.raster_y += 1
            # FIXME; very rough raster irq
            self.irq_raster_occured = self.irq_raster_line == self.raster_y
            if self.raster_y >= SCAN_AREA_V:
                self.raster_y = 0
                self._frame_on = self.DEN
                return (
                    np.where(
                        # For each bit == pixel
                        np.unpackbits(self.dataframe[:, :, 0], axis=0) == 0,
                        # If zero its background color
                        np.repeat(self.dataframe[:, :, 1], 8, axis=0),
                        # If one its foreground color
                        np.repeat(self.dataframe[:, :, 2], 8, axis=0),
                    ),
                    self.any_irq_enabled and self.irq_raster_occured,
                )
        return (None, self.any_irq_enabled and self.irq_raster_occured)


class VirtualScreen(VIC_II):
    """
    No display
    """

    __slots__ = []

    def clock(self, clock_counter: int):
        pass


class FastScreen(VIC_II):
    """
    Screen driver using numpy
    Text only, fast
    """

    __slots__ = ["font_cache"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font_cache = self.cache_fonts()

    def cache_fonts(self):
        cache = []
        chargen = self.memory.roms["chargen"]
        for i in range(512):
            matrix = chargen[i * 8 : (i + 1) * 8]
            font_array = np.array(matrix, dtype="uint8")
            font = np.unpackbits(font_array).reshape(8, 8).T
            cache.append(font)
        return cache

    def clock(self, clock_counter: int) -> np.array:
        if clock_counter % CLOCKS_PER_FRAME == 0:
            frame = np.ones(VIDEO_SIZE, dtype="uint8") * self.border_color

            if self.DEN:
                char_base = self.video_matrix_base_address
                charcodes = np.array(
                    [
                        self.memory.vic_read(i)
                        for i in range(char_base, char_base + 1000)
                    ]
                )
                colors = np.array(self.memory[0xD800 : 0xD800 + 1000])
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
            self.memory[0xD012] = 0  # This lets the system boot (see $FF5E)
            return frame, False
        return None, False
