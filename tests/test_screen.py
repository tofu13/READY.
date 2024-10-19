import pytest
from mock import mock

import config
from libs.hardware import roms
from libs.hardware.bus import Bus
from libs.hardware.constants import PIXELATOR_BITMAP, VIDEO_SIZE
from libs.hardware.memory import Memory
from libs.hardware.screen import VIC_II, RasterScreen


@pytest.fixture()
def memory():
    memory = Memory(roms=roms.ROMS(config.TESTING_ROMS_FOLDER))
    memory.cpu_write(0x00, 0x07)
    memory.cpu_write(0x01, 0x07)
    return memory


@pytest.fixture()
def bus():
    return Bus()


@pytest.fixture()
def vic_ii(memory, bus):
    return VIC_II(memory, bus)


@pytest.fixture()
def vic_ii_raster(memory, bus):
    return RasterScreen(memory, bus)


def test_vic_ii(vic_ii):
    assert vic_ii
    assert len(vic_ii.sprites) == 8


def test_VIC_II_registers(vic_ii):
    vic_ii.write_registers(0xD011, 0)
    assert vic_ii.irq_raster_line_msb is False
    assert vic_ii.extended_background is False
    assert vic_ii.bitmap_mode is False
    assert vic_ii.DEN is False
    assert vic_ii.RSEL is False
    assert vic_ii.Y_SCROLL == 0

    vic_ii.write_registers(0xD011, 255)
    assert vic_ii.irq_raster_line_msb is True
    assert vic_ii.extended_background is True
    assert vic_ii.bitmap_mode is True
    assert vic_ii.DEN is True
    assert vic_ii.RSEL is True
    assert vic_ii.Y_SCROLL == 7

    vic_ii.write_registers(0xD016, 0)
    assert vic_ii.multicolor_mode is False
    assert vic_ii.CSEL is False
    assert vic_ii.X_SCROLL == 0

    vic_ii.write_registers(0xD016, 255)
    assert vic_ii.multicolor_mode is True
    assert vic_ii.CSEL is True
    assert vic_ii.X_SCROLL == 7


def test_VIC_II_registers_disconnected(vic_ii):
    for i in range(0xD030, 0xD040):
        assert vic_ii.read_registers(i) == 0xFF


def test_VIC_II_light_pen(vic_ii):
    assert vic_ii.read_registers(0xD013) == 0
    assert vic_ii.read_registers(0xD014) == 0


def test_VIC_II_colors(memory, vic_ii):
    vic_ii.write_registers(0xD020, 1)
    assert vic_ii.border_color == 1

    vic_ii.write_registers(0xD060, 10)  # Repeated registry
    assert vic_ii.border_color == 10

    vic_ii.write_registers(0xD021, 2)
    assert vic_ii.background_color == 2

    vic_ii.write_registers(0xD022, 3)
    assert vic_ii.background_color_1 == 3

    vic_ii.write_registers(0xD023, 4)
    assert vic_ii.background_color_2 == 4

    vic_ii.write_registers(0xD024, 5)
    assert vic_ii.background_color_3 == 5

    vic_ii.write_registers(0xD025, 5)
    assert vic_ii.sprite_multicolor_1 == 5

    vic_ii.write_registers(0xD026, 255)  # Also check out of palette
    assert vic_ii.sprite_multicolor_2 == 15


@pytest.mark.parametrize(
    (
        "value",
        "video_matrix_base_address",
        "character_generator_base_address",
        "bitmap_base_address",
    ),
    [
        (0b00000000, 0x0000, 0x0000, 0x0000),
        (0b00010101, 0x0400, 0x1000, 0x0000),
        (0b11110000, 0x3C00, 0x0000, 0x0000),
        (0b00000100, 0x0000, 0x1000, 0x0000),
        (0b00000101, 0x0000, 0x1000, 0x0000),
        (0b00001010, 0x0000, 0x2800, 0x2000),
        (0b00001111, 0x0000, 0x3800, 0x2000),
    ],
)
def test_VIC_II_addressing(
    memory,
    vic_ii,
    value,
    video_matrix_base_address,
    character_generator_base_address,
    bitmap_base_address,
):
    vic_ii.write_registers(0xD018, value)
    assert vic_ii.video_matrix_base_address == video_matrix_base_address
    assert vic_ii.character_generator_base_address == character_generator_base_address
    assert vic_ii.bitmap_base_address == bitmap_base_address


def test_VIC_II_sprites(memory, vic_ii):
    # Coordinates
    vic_ii.write_registers(0xD000, 0xFF)
    assert vic_ii.sprites[0].x == 0xFF
    vic_ii.write_registers(0xD00F, 0x42)
    assert vic_ii.sprites[7].Y == 0x42

    vic_ii.write_registers(0xD002, 0xAB)
    # Move sprite x > 256
    vic_ii.write_registers(0xD010, 0b10)
    assert vic_ii.sprites[1].X == 0x1AB

    # And back
    vic_ii.write_registers(0xD010, 0b0)
    assert vic_ii.sprites[1].X == 0xAB

    # Enable
    vic_ii.write_registers(0xD015, 0b10)
    assert vic_ii.sprites[0].enable is False
    assert vic_ii.sprites[1].enable is True

    # Expand
    vic_ii.write_registers(0xD017, 0b01)
    assert vic_ii.sprites[0].expand_y is True
    assert vic_ii.sprites[1].expand_y is False

    vic_ii.write_registers(0xD01D, 0b100)
    assert vic_ii.sprites[0].expand_x is False
    assert vic_ii.sprites[1].expand_x is False
    assert vic_ii.sprites[2].expand_x is True

    # Multicolor
    vic_ii.write_registers(0xD01C, 0b101)
    assert vic_ii.sprites[0].multicolor is True
    assert vic_ii.sprites[1].multicolor is False
    assert vic_ii.sprites[2].multicolor is True

    # Priority
    vic_ii.write_registers(0xD01B, 0b110)
    assert vic_ii.sprites[0].priority is False
    assert vic_ii.sprites[1].priority is True
    assert vic_ii.sprites[2].priority is True

    # Color
    vic_ii.write_registers(0xD02A, 0x0F)
    assert vic_ii.sprites[3].color == 0x0F


def test_VIC_II_irq(memory, vic_ii):
    vic_ii.write_registers(0xD012, 0x42)
    assert vic_ii.irq_raster_line == 0x42

    vic_ii.write_registers(0xD011, 0b10000000)
    assert vic_ii.irq_raster_line == 0x142

    vic_ii.write_registers(0xD011, 0b01111111)
    assert vic_ii.irq_raster_line == 0x42

    vic_ii.write_registers(0xD01A, 0b1111)
    assert vic_ii.irq_raster_enabled is True
    assert vic_ii.irq_sprite_background_collision_enabled is True
    assert vic_ii.irq_sprite_sprite_collision_enabled is True
    assert vic_ii.irq_lightpen_enabled is True

    vic_ii.write_registers(0xD01A, 0b0000)
    assert vic_ii.irq_raster_enabled is False
    assert vic_ii.irq_sprite_background_collision_enabled is False
    assert vic_ii.irq_sprite_sprite_collision_enabled is False
    assert vic_ii.irq_lightpen_enabled is False

    assert memory.cpu_read(0xD019) == 0b01110000
    assert vic_ii.any_irq_occured is False
    # Directly set irqs
    vic_ii.irq_raster_occured = True
    assert vic_ii.any_irq_occured is True
    assert memory.cpu_read(0xD019) == 0b11110001
    vic_ii.irq_sprite_background_collision_occured = True
    assert memory.cpu_read(0xD019) == 0b11110011
    vic_ii.irq_sprite_sprite_collision_occured = True
    assert memory.cpu_read(0xD019) == 0b11110111
    vic_ii.irq_lightpen_occured = True
    assert memory.cpu_read(0xD019) == 0b11111111

    # Clear irqs
    vic_ii.write_registers(0xD019, 0b0001)
    assert memory.cpu_read(0xD019) == 0b11111110
    assert vic_ii.any_irq_occured is True
    vic_ii.write_registers(0xD019, 0b1111)
    assert memory.cpu_read(0xD019) == 0b01110000
    assert vic_ii.any_irq_occured is False


def test_VIC_II_raster_irq_occurs(vic_ii_raster):
    # Set raster line
    vic_ii_raster.write_registers(0xD012, 0x002)
    assert vic_ii_raster.irq_raster_line == 0x002

    vic_ii_raster.write_registers(0xD011, 0x80)
    assert vic_ii_raster.irq_raster_line == 0x102

    vic_ii_raster.write_registers(0xD011, 0x00)
    assert vic_ii_raster.irq_raster_line == 0x002

    # Enable raster interrupts
    vic_ii_raster.write_registers(0xD01A, 0b1111)

    with mock.patch("libs.hardware.bus.Bus") as irq_mock:
        vic_ii_raster.bus = irq_mock
        irq_mock.irq_set.assert_not_called()

        for i in range(63 * 2 - 1):  # 1 clock before IRQ
            vic_ii_raster.clock(0)
        irq_mock.irq_set.assert_not_called()
        vic_ii_raster.clock(0)  # IRQ here
        irq_mock.irq_set.assert_called()

        # Ack irq
        irq_mock.irq_clear.assert_not_called()
        vic_ii_raster.write_registers(0xD019, 0b0001)
        irq_mock.irq_clear.assert_called()


def test_VIC_II_raster_clock(vic_ii_raster):
    frame = vic_ii_raster.clock(0)
    assert frame is None
    assert vic_ii_raster.raster_x == 8
    assert vic_ii_raster.raster_y == 0

    # To the next line
    for _ in range(62):
        vic_ii_raster.clock(0)

    assert vic_ii_raster.raster_x == 0
    assert vic_ii_raster.raster_y == 1

    # To the end of frame (311 lines missing, 1 clock remaining)
    for _ in range(63 * 311 - 1):
        vic_ii_raster.clock(0)
    # End of frame now
    frame = vic_ii_raster.clock(0)

    assert vic_ii_raster.raster_x == 0
    assert vic_ii_raster.raster_y == 0
    assert frame is not None


def test_VIC_II_raster_text_mode(vic_ii_raster):
    vic_ii_raster._frame_on = True
    frame = None
    while frame is None:
        frame = vic_ii_raster.clock(0)
    assert frame.shape == VIDEO_SIZE


def test_VIC_II_raster_bad_lines_occur(vic_ii_raster):
    # Assert buffers unthouched
    assert vic_ii_raster.char_buffer == bytearray([0x01] * 40)
    assert vic_ii_raster.color_buffer == bytearray([0x00] * 40)

    vic_ii_raster.raster_x = 24
    vic_ii_raster.raster_y = 48
    vic_ii_raster._frame_on = True

    vic_ii_raster.clock(0)

    assert vic_ii_raster.char_buffer == bytearray([0x00] * 40)
    assert vic_ii_raster.color_buffer == bytearray([0x00] * 40)


def test_VIC_II_raster_bad_lines_lock_CPU(vic_ii_raster):
    vic_ii_raster.raster_x = 24
    vic_ii_raster.raster_y = 48
    vic_ii_raster._frame_on = True

    with mock.patch("libs.hardware.bus.Bus") as irq_mock:
        vic_ii_raster.bus = irq_mock
        irq_mock.require_memory_bus.assert_not_called()
        vic_ii_raster.clock(0)
        irq_mock.require_memory_bus.assert_called_with(cycles=40)


@pytest.mark.parametrize(
    ("pixels", "expected"),
    [
        (0b00000000, [0, 0, 0, 0, 0, 0, 0, 0]),
        (0b01010101, [0, 1, 0, 1, 0, 1, 0, 1]),
        (0b10101010, [1, 0, 1, 0, 1, 0, 1, 0]),
        (0b11111111, [1, 1, 1, 1, 1, 1, 1, 1]),
    ],
)
def test_VIC_II_raster_pixelate_bitmap(vic_ii_raster, pixels, expected):
    assert PIXELATOR_BITMAP[pixels * 256 + 1 * 16 + 0] == bytearray(expected)


@pytest.mark.parametrize(
    ("pixels", "expected"),
    [
        (0b00000000, [0, 0, 0, 0, 0, 0, 0, 0]),
        (0b01010101, [1, 1, 1, 1, 1, 1, 1, 1]),
        (0b10101010, [2, 2, 2, 2, 2, 2, 2, 2]),
        (0b11111111, [3, 3, 3, 3, 3, 3, 3, 3]),
    ],
)
def test_VIC_II_raster_pixelate_text_multicolor(vic_ii_raster, pixels, expected):
    vic_ii_raster.write_registers(0xD021, 0)  # Set background colour
    vic_ii_raster.write_registers(0xD022, 1)  # Set background colour # 1
    vic_ii_raster.write_registers(0xD023, 2)  # Set background colour # 2
    assert (
        list(vic_ii_raster.pixelate_text_multicolor(char_color=3, pixels=pixels))
        == expected
    )


@pytest.mark.parametrize(
    ("bg_index", "pixels", "expected"),
    [
        (0b00, 0b00000000, [0, 0, 0, 0, 0, 0, 0, 0]),
        (0b00, 0b01010101, [0, 4, 0, 4, 0, 4, 0, 4]),
        (0b00, 0b10101010, [4, 0, 4, 0, 4, 0, 4, 0]),
        (0b00, 0b11111111, [4, 4, 4, 4, 4, 4, 4, 4]),
        (0b01, 0b00000000, [1, 1, 1, 1, 1, 1, 1, 1]),
        (0b01, 0b01010101, [1, 4, 1, 4, 1, 4, 1, 4]),
        (0b01, 0b10101010, [4, 1, 4, 1, 4, 1, 4, 1]),
        (0b01, 0b11111111, [4, 4, 4, 4, 4, 4, 4, 4]),
        (0b10, 0b00000000, [2, 2, 2, 2, 2, 2, 2, 2]),
        (0b10, 0b01010101, [2, 4, 2, 4, 2, 4, 2, 4]),
        (0b10, 0b10101010, [4, 2, 4, 2, 4, 2, 4, 2]),
        (0b10, 0b11111111, [4, 4, 4, 4, 4, 4, 4, 4]),
        (0b11, 0b00000000, [3, 3, 3, 3, 3, 3, 3, 3]),
        (0b11, 0b01010101, [3, 4, 3, 4, 3, 4, 3, 4]),
        (0b11, 0b10101010, [4, 3, 4, 3, 4, 3, 4, 3]),
        (0b11, 0b11111111, [4, 4, 4, 4, 4, 4, 4, 4]),
    ],
)
def test_VIC_II_raster_pixelate_text_extended_color(
    vic_ii_raster, bg_index, pixels, expected
):
    vic_ii_raster.write_registers(0xD021, 0)  # Set background colour
    vic_ii_raster.write_registers(0xD022, 1)  # Set background colour # 1
    vic_ii_raster.write_registers(0xD023, 2)  # Set background colour # 2
    vic_ii_raster.write_registers(0xD024, 3)  # Set background colour # 3
    assert (
        list(
            vic_ii_raster.pixelate_text_extended_color(
                background_index=bg_index, char_color=4, pixels=pixels
            )
        )
        == expected
    )


@pytest.mark.parametrize(
    ("pixels", "expected"),
    [
        (0b00000000, [0, 0, 0, 0, 0, 0, 0, 0]),
        (0b01010101, [1, 1, 1, 1, 1, 1, 1, 1]),
        (0b10101010, [2, 2, 2, 2, 2, 2, 2, 2]),
        (0b11111111, [3, 3, 3, 3, 3, 3, 3, 3]),
    ],
)
def test_VIC_II_raster_pixelate_bitmap_multicolor(vic_ii_raster, pixels, expected):
    vic_ii_raster.write_registers(0xD021, 0)  # Set background colour

    assert (
        list(
            vic_ii_raster.pixelate_bitmap_multicolor(
                char_color=0x03, colors=0x12, pixels=pixels
            )
        )
        == expected
    )
