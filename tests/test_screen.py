import pytest

import config
from libs.hardware import roms
from libs.hardware.constants import VIDEO_SIZE
from libs.hardware.memory import Memory
from libs.hardware.screen import VIC_II, RasterScreen


@pytest.fixture()
def memory():
    memory = Memory(roms=roms.ROMS(config.TESTING_ROMS_FOLDER))
    memory.cpu_write(0x00, 0x07)
    memory.cpu_write(0x01, 0x07)
    return memory


@pytest.fixture()
def vic_ii(memory):
    return VIC_II(memory)


@pytest.fixture()
def vic_ii_raster(memory):
    return RasterScreen(memory)


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


def test_VIC_II_addressing(memory, vic_ii):
    vic_ii.write_registers(0xD018, 0x10)
    assert vic_ii.video_matrix_base_address == 0x0400

    vic_ii.write_registers(0xD018, 0xF0)
    assert vic_ii.video_matrix_base_address == 0x3C00

    vic_ii.write_registers(0xD018, 0x04)
    assert vic_ii.character_generator_base_address == 0x1000

    vic_ii.write_registers(0xD018, 0x05)
    assert vic_ii.character_generator_base_address == 0x1000

    vic_ii.write_registers(0xD018, 0x0A)
    assert vic_ii.character_generator_base_address == 0x2800


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
    vic_ii_raster.write_registers(0xD012, 0x10)
    assert vic_ii_raster.irq_raster_line == 0x010

    vic_ii_raster.write_registers(0xD011, 0x80)
    assert vic_ii_raster.irq_raster_line == 0x110

    vic_ii_raster.write_registers(0xD011, 0x00)
    assert vic_ii_raster.irq_raster_line == 0x010

    assert vic_ii_raster.irq_raster_occured is False
    while not vic_ii_raster.irq_raster_occured:
        _, irq_line = vic_ii_raster.clock(0)

    # Irq disabled -> irq signal is false
    assert irq_line is False
    assert vic_ii_raster.read_registers(0xD019) & 0b0001
    assert vic_ii_raster.any_irq_occured

    # Ack irq
    vic_ii_raster.write_registers(0xD019, 0b0001)
    assert vic_ii_raster.irq_raster_occured is False
    assert vic_ii_raster.any_irq_occured is False


def test_VIC_II_raster_irq_line(vic_ii_raster):
    vic_ii_raster.write_registers(0xD012, 0x10)
    assert vic_ii_raster.irq_raster_line == 0x010

    # Enable raster irq
    vic_ii_raster.write_registers(0xD01A, 0x01)
    while not vic_ii_raster.irq_raster_occured:
        _, irq_line = vic_ii_raster.clock(0)
    # irq has been signalled
    assert irq_line is True


def test_VIC_II_raster_clock(vic_ii_raster):
    frame, irq = vic_ii_raster.clock(0)
    assert frame is None
    assert vic_ii_raster.raster_x == 8
    assert vic_ii_raster.raster_y == 0

    # To the next line
    for _ in range(63):
        vic_ii_raster.clock(0)

    assert vic_ii_raster.raster_x == 0
    assert vic_ii_raster.raster_y == 1

    # To the end of frame (311 lines missing, 1 clock remaining)
    for _ in range(64 * 311 - 1):
        vic_ii_raster.clock(0)
    # End of frame now
    frame, irq = vic_ii_raster.clock(0)

    assert vic_ii_raster.raster_x == 0
    assert vic_ii_raster.raster_y == 0
    assert frame is not None


def test_VIC_II_raster_text_mode(vic_ii_raster):
    vic_ii_raster._frame_on = True
    frame = None
    while frame is None:
        frame, irq = vic_ii_raster.clock(0)
    assert frame.shape == VIDEO_SIZE
