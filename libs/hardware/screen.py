import dataclasses

import numpy as np

from .constants import (
    BITRANGE,
    BYTEBOOLEANS,
    BYTEPAIRS,
    CLOCKS_PER_FRAME,
    FIRST_COLUMN,
    FIRST_LINE,
    LAST_COLUMN,
    LAST_LINE,
    PIXELATOR_BITMAP,
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
        "bus",
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
        "bitmap_base_address",
        "border_color",
        "background_color",
        "background_color_1",
        "background_color_2",
        "background_color_3",
        "sprite_multicolor_1",
        "sprite_multicolor_2",
        "sprites",
        "_cached_registers",
        "_cached_border_color_pack",
        "_cached_multicolor_pack",
        "_cached_background_color_pack",
        "_cached_first_line",
        "_cached_last_line",
        "_cached_first_column",
        "_cached_last_column",
    ]

    def __init__(self, memory, bus):
        self.memory = memory
        self.bus = bus

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
        self.bitmap_base_address = 0x0000
        self.border_color = 0x0E
        self.background_color = 0x06
        self.background_color_1 = 0x03
        self.background_color_2 = 0x04
        self.background_color_3 = 0x05
        self.sprite_multicolor_1 = 0x05
        self.sprite_multicolor_2 = 0x05

        self.sprites = [Sprite() for _ in range(8)]

        self._cached_border_color_pack = bytearray((self.border_color,) * 8)
        self._cached_background_color_pack = bytearray((self.background_color,) * 8)
        self._cached_multicolor_pack = bytearray(
            (self.background_color, self.background_color_1, self.background_color_2, 0)
        )

        self._cached_registers = bytearray(0x40)
        self._cached_first_line = FIRST_LINE[self.RSEL]
        self._cached_last_line = LAST_LINE[self.RSEL]
        self._cached_first_column = FIRST_COLUMN[self.CSEL]
        self._cached_last_column = LAST_COLUMN[self.CSEL]

        self.memory.write_watchers.append((0xD000, 0xD3FF, self.write_registers))
        self.memory.read_watchers.append((0xD000, 0xD3FF, self.read_registers))

    def __str__(self):
        return (
            f"VIC-II {self.__class__} - DEN:{self.DEN}\n"
            f"RSEL:{self.RSEL} CSEL:{self.CSEL} "
            f"X_SCROLL:{self.X_SCROLL} Y_SCROLL:{self.Y_SCROLL}\n"
            f"CHAR ADDRESS:{hex(self.video_matrix_base_address)} "
            f"CHARGEN ADDRESS:{hex(self.character_generator_base_address)} "
            f"BITMAP ADDRESS:{hex(self.character_generator_base_address)} "
            f"RASTER: {self.raster_x, self.raster_y}\n"
            + "\n".join(str(sprite) for sprite in self.sprites)
        )

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
        self._cached_registers[address] = value

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
                self._cached_first_line = FIRST_LINE[self.RSEL]
                self._cached_last_line = LAST_LINE[self.RSEL]
            case 0x12:
                self.irq_raster_line_lsb = value
            case 0x15:
                for i in range(8):
                    self.sprites[i].enable = bool(value & BITRANGE[i][1])
            case 0x16:
                self.multicolor_mode = bool(value & 0b10000)
                self.CSEL = bool(value & 0b1000)
                self.X_SCROLL = value & 0b111
                self._cached_first_column = FIRST_COLUMN[self.CSEL]
                self._cached_last_column = LAST_COLUMN[self.CSEL]

            case 0x17:
                for i in range(8):
                    self.sprites[i].expand_y = bool(value & BITRANGE[i][1])
            case 0x18:
                self.video_matrix_base_address = (value & 0b11110000) << 6
                self.character_generator_base_address = (value & 0b00001110) << 10
                self.bitmap_base_address = (value & 0b00001000) << 10
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
                if not self.any_irq_occured:  # and value & 0b1111: ## no need to check
                    self.bus.irq_clear("VIC-II")
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
                # Cache for border pixels
                self._cached_border_color_pack = bytearray((self.border_color,) * 8)
            case 0x21:
                self.background_color = value & 0x0F
                self._cached_multicolor_pack[0] = self.background_color
                self._cached_background_color_pack = bytearray(
                    (self.background_color,) * 8
                )
            case 0x22:
                self.background_color_1 = value & 0x0F
                self._cached_multicolor_pack[1] = self.background_color_1
            case 0x23:
                self.background_color_2 = value & 0x0F
                self._cached_multicolor_pack[2] = self.background_color_2
            case 0x24:
                self.background_color_3 = value & 0x0F
            case 0x25:
                self.sprite_multicolor_1 = value & 0x0F
            case 0x26:
                self.sprite_multicolor_2 = value & 0x0F
            case sprite if 0x27 <= sprite <= 0x2E:
                self.sprites[sprite - 0x27].color = value & 0x0F

    def read_registers(self, address: int) -> int:
        address &= 0x3F
        match address:
            # Dynamic registers
            case 0x11:
                # Dynamically set bit #7 = bit raster_y bit #8
                # Other bits are cached
                return ((self.raster_y & 0x0100) >> 1) | (
                    self._cached_registers[0x11] & 0x7F
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
                return self._cached_registers[0x16] | 0b11000000
            case 0x18:
                return self._cached_registers[0x18] | 0b00000001
            case 0x1A:
                return self._cached_registers[0x1A] | 0b11110000
            case color if 0x20 <= color <= 0x2E:
                return self._cached_registers[color] | 0b11110000
            case disconnected if 0x30 <= disconnected <= 0x3F:
                return 0xFF
            case other:
                return self._cached_registers[other]


class RasterScreen(VIC_II):
    __slots__ = [
        "raster_x",
        "char_buffer",
        "color_buffer",
        "frame",
        "dataframe",
        "_frame_on",
    ]

    def __init__(self, memory, bus):
        super().__init__(memory, bus)

        self.raster_y = 0
        self.raster_x: int = 0
        self.char_buffer = bytearray([1] * 40)
        self.color_buffer = bytearray([0] * 40)

        self._frame_on = self.DEN

        self.frame = bytearray([0] * VIDEO_SIZE_H * VIDEO_SIZE_V)

    def pixelate_text_extended_color(
        self, background_index: int, char_color: int, pixels: int
    ):
        bgcolor = (
            self.background_color,
            self.background_color_1,
            self.background_color_2,
            self.background_color_3,
        )[background_index]
        return (
            # If one its foreground color
            char_color
            # For each bit == pixel
            if px
            # If zero its background color
            else bgcolor
            for px in BYTEBOOLEANS[pixels]
        )

    def pixelate_text_multicolor(self, char_color: int, pixels: int) -> tuple:
        # TIL multicolor char mode can mix
        # hires chars based in their color MSB
        # (which limits their color space)
        p0, p1, p2, p3 = BYTEPAIRS[pixels]
        self._cached_multicolor_pack[3] = char_color & 0x07
        return (
            # Pick 1 color, fill 2 pixels
            self._cached_multicolor_pack[p0],
            self._cached_multicolor_pack[p0],
            self._cached_multicolor_pack[p1],
            self._cached_multicolor_pack[p1],
            self._cached_multicolor_pack[p2],
            self._cached_multicolor_pack[p2],
            self._cached_multicolor_pack[p3],
            self._cached_multicolor_pack[p3],
        )

    def pixelate_bitmap_multicolor(self, char_color: int, colors, pixels):
        color_pack = (
            self.background_color,
            colors >> 4,
            colors & 0x0F,
            char_color,
        )
        p0, p1, p2, p3 = BYTEPAIRS[pixels]
        # Pick 1 color, fill 2 pixels
        return (
            color_pack[p0],
            color_pack[p0],
            color_pack[p1],
            color_pack[p1],
            color_pack[p2],
            color_pack[p2],
            color_pack[p3],
            color_pack[p3],
        )

    def clock(self, clock_counter: int):
        if self.raster_x < VIDEO_SIZE_H and self.raster_y < VIDEO_SIZE_V:
            # Raster is in the visible area
            pixel_pointer = self.raster_y * VIDEO_SIZE_H + self.raster_x
            if (
                24 <= self.raster_x <= 343
                and 48 <= self.raster_y <= 247
                and self._frame_on
            ):
                # Raster is in the display area
                pixel_range = slice(
                    pixel_pointer + self.X_SCROLL + VIDEO_SIZE_H * self.Y_SCROLL,
                    pixel_pointer + self.X_SCROLL + VIDEO_SIZE_H * self.Y_SCROLL + 8,
                )
                matrix_column = (self.raster_x - 24) // 8
                matrix_row = (self.raster_y - 48) // 8
                matrix_row_offset = (self.raster_y - 48) % 8
                # Bad lines
                if self.raster_x == 24 and matrix_row_offset == 0:
                    char_pointer = self.video_matrix_base_address + matrix_row * 40
                    color_pointer = matrix_row * 40

                    self.char_buffer = bytearray(
                        self.memory.vic_read(i)
                        for i in range(char_pointer, char_pointer + 40)
                    )
                    self.color_buffer = self.memory.ram_color[
                        color_pointer : color_pointer + 40
                    ]  # Direct read from fixed color ram
                    # Steal cycles from CPU
                    self.bus.require_memory_bus(cycles=40)

                # Bitmap
                if self.bitmap_mode:
                    pixels = self.memory.vic_read(
                        self.bitmap_base_address
                        + (self.raster_x - 24)
                        + matrix_row * 320
                        + matrix_row_offset
                    )
                    # Fixme: misleading variable name
                    colors = self.char_buffer[matrix_column]
                    if self.multicolor_mode:
                        self.frame[pixel_range] = self.pixelate_bitmap_multicolor(
                            self.color_buffer[matrix_column], colors, pixels
                        )
                    else:
                        self.frame[pixel_range] = PIXELATOR_BITMAP[
                            pixels * 0x100 + colors
                        ]
                # Text
                else:
                    char_color = self.color_buffer[matrix_column] & 0x0F
                    pixels = self.memory.vic_read(
                        self.character_generator_base_address
                        + self.char_buffer[matrix_column] * 8
                        + matrix_row_offset
                    )

                    if self.multicolor_mode and char_color & 0x08:
                        self.frame[pixel_range] = self.pixelate_text_multicolor(
                            char_color, pixels
                        )
                    else:
                        self.frame[pixel_range] = PIXELATOR_BITMAP[
                            pixels * 256 + char_color * 16 + self.background_color
                        ]

                # Empty pixels at left when X_SCROLL
                # TODO: Empty pixels shall be fetched as zeros when scrolled,
                # not set explicitily
                if self.X_SCROLL and self.raster_x == 24:
                    self.frame[pixel_pointer : pixel_pointer + self.X_SCROLL] = (
                        self.background_color,
                    ) * self.X_SCROLL

                # Empty pixels at top
                # Empty pixels at bottom
                elif (
                    51 <= self.raster_y < 48 + self.Y_SCROLL
                    or self.raster_y > 247 + self.Y_SCROLL
                ):
                    self.frame[pixel_pointer : pixel_pointer + 8] = (
                        self._cached_background_color_pack
                    )
            # Border
            # TODO: use border flip-flop
            if any(
                (
                    self.raster_y < self._cached_first_line,
                    self.raster_y > self._cached_last_line,
                    self.raster_x < self._cached_first_column,
                    self.raster_x > self._cached_last_column,
                    not self.DEN,
                )
            ):
                self.frame[pixel_pointer : pixel_pointer + 8] = (
                    self._cached_border_color_pack
                )

        self.raster_x += 8
        if self.raster_x >= SCAN_AREA_H:
            self.raster_x = 0
            self.raster_y += 1
            frame = None
            if self.raster_y >= SCAN_AREA_V:
                self.raster_y = 0
                self._frame_on = self.DEN
                frame = (
                    # Cut frame size to ignore out-of-frame pixels
                    np.array(self.frame, dtype=np.ubyte)
                    .reshape((VIDEO_SIZE_V, VIDEO_SIZE_H))
                    .T
                )
            if self.irq_raster_enabled and self.irq_raster_line == self.raster_y:
                # Raster IRQ
                self.irq_raster_occured = True
                self.bus.irq_set("VIC-II")

            return frame


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
            return frame
