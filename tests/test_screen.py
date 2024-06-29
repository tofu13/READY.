import pytest

import config
from hardware import roms
from hardware.memory import Memory
from hardware.screen import VIC_II


@pytest.fixture()
def memory():
    memory = Memory(roms=roms.ROMS(config.TESTING_ROMS_FOLDER))
    memory.cpu_write(0x00, 0x07)
    memory.cpu_write(0x01, 0x07)
    return memory


@pytest.fixture()
def vic_ii(memory):
    return VIC_II(memory)


def test_vic_ii(vic_ii):
    assert vic_ii
    assert len(vic_ii.sprites) == 8


def test_VIC_II_colors(memory, vic_ii):
    memory.cpu_write(0xD020, 1)
    assert vic_ii.border_color == 1

    memory.cpu_write(0xD060, 10)  # Repeated registry
    assert vic_ii.border_color == 10

    memory.cpu_write(0xD021, 2)
    assert vic_ii.background_color == 2

    memory.cpu_write(0xD022, 3)
    assert vic_ii.background_color_1 == 3

    memory.cpu_write(0xD023, 4)
    assert vic_ii.background_color_2 == 4

    memory.cpu_write(0xD024, 5)
    assert vic_ii.background_color_3 == 5

    memory.cpu_write(0xD025, 5)
    assert vic_ii.sprite_multicolor_1 == 5

    memory.cpu_write(0xD026, 255)  # Also check out of palette
    assert vic_ii.sprite_multicolor_2 == 15


def test_VIC_II_addressing(memory, vic_ii):
    memory.cpu_write(0xD018, 0x10)
    assert vic_ii.video_matrix_base_address == 0x0400

    memory.cpu_write(0xD018, 0xF0)
    assert vic_ii.video_matrix_base_address == 0x3C00

    memory.cpu_write(0xD018, 0x04)
    assert vic_ii.character_generator_base_address == 0x1000

    memory.cpu_write(0xD018, 0x05)
    assert vic_ii.character_generator_base_address == 0x1000

    memory.cpu_write(0xD018, 0x0A)
    assert vic_ii.character_generator_base_address == 0x2800


def test_VIC_II_sprites(memory, vic_ii):
    # Coordinates
    memory.cpu_write(0xD000, 0xFF)
    assert vic_ii.sprites[0].x == 0xFF
    memory.cpu_write(0xD00F, 0x42)
    assert vic_ii.sprites[7].y == 0x42

    memory.cpu_write(0xD002, 0xAB)
    # Move sprite x > 256
    memory.cpu_write(0xD010, 0b10)
    assert vic_ii.sprites[1].X == 0x1AB

    # And back
    memory.cpu_write(0xD010, 0b0)
    assert vic_ii.sprites[1].X == 0xAB

    # Enable
    memory.cpu_write(0xD015, 0b10)
    assert vic_ii.sprites[0].enable is False
    assert vic_ii.sprites[1].enable is True

    # Expand
    memory.cpu_write(0xD017, 0b01)
    assert vic_ii.sprites[0].expand_y is True
    assert vic_ii.sprites[1].expand_y is False

    memory.cpu_write(0xD01D, 0b100)
    assert vic_ii.sprites[0].expand_x is False
    assert vic_ii.sprites[1].expand_x is False
    assert vic_ii.sprites[2].expand_x is True

    # Multicolor
    memory.cpu_write(0xD01C, 0b101)
    assert vic_ii.sprites[0].multicolor is True
    assert vic_ii.sprites[1].multicolor is False
    assert vic_ii.sprites[2].multicolor is True

    # Priority
    memory.cpu_write(0xD01B, 0b110)
    assert vic_ii.sprites[0].priority is False
    assert vic_ii.sprites[1].priority is True
    assert vic_ii.sprites[2].priority is True

    # Color
    memory.cpu_write(0xD02A, 0x0F)
    assert vic_ii.sprites[3].color == 0x0F


def test_VIC_II_irq(memory, vic_ii):
    memory.cpu_write(0xD012, 0x42)
    assert vic_ii.irq_raster_line == 0x42

    memory.cpu_write(0xD011, 0b10000000)
    assert vic_ii.irq_raster_line == 0x142

    memory.cpu_write(0xD011, 0b01111111)
    assert vic_ii.irq_raster_line == 0x42

    memory.cpu_write(0xD01A, 0b1111)
    assert vic_ii.irq_raster_enabled is True
    assert vic_ii.irq_sprite_background_collision_enabled is True
    assert vic_ii.irq_sprite_sprite_collision_enabled is True
    assert vic_ii.irq_lightpen_enabled is True

    memory.cpu_write(0xD01A, 0b0000)
    assert vic_ii.irq_raster_enabled is False
    assert vic_ii.irq_sprite_background_collision_enabled is False
    assert vic_ii.irq_sprite_sprite_collision_enabled is False
    assert vic_ii.irq_lightpen_enabled is False
