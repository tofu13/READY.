import pytest

import config
from hardware import roms
from hardware.memory import Memory
from hardware.screen import VIC_II


@pytest.fixture
def test_memory():
    memory = Memory(roms=roms.ROMS(config.TESTING_ROMS_FOLDER))
    memory.hiram = True
    memory.loram = True
    memory.charen = True
    return memory


def test_VIC_II(test_memory):
    my_vic_ii = VIC_II(test_memory)
    assert my_vic_ii


def test_VIC_II_registers(test_memory):
    my_vic_ii = VIC_II(test_memory)

    test_memory.cpu_write(0xD020, 1)
    assert my_vic_ii.border_color == 1

    test_memory.cpu_write(0xD021, 2)
    assert my_vic_ii.background_color == 2

    test_memory.cpu_write(0xD022, 3)
    assert my_vic_ii.background_color_1 == 3

    test_memory.cpu_write(0xD023, 4)
    assert my_vic_ii.background_color_2 == 4

    test_memory.cpu_write(0xD024, 5)
    assert my_vic_ii.background_color_3 == 5

    test_memory.cpu_write(0xD018, 0x10)
    assert my_vic_ii.video_matrix_base_address == 0x0400

    test_memory.cpu_write(0xD018, 0xF0)
    assert my_vic_ii.video_matrix_base_address == 0x3C00

    test_memory.cpu_write(0xD018, 0x04)
    assert my_vic_ii.character_generator_base_address == 0x1000

    test_memory.cpu_write(0xD018, 0x05)
    assert my_vic_ii.character_generator_base_address == 0x1000

    test_memory.cpu_write(0xD018, 0x0A)
    assert my_vic_ii.character_generator_base_address == 0x2800
