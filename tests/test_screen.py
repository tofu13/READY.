import pytest

from hardware import memory, screen


@pytest.fixture
def test_memory():
    mem = memory.BytearrayMemory(65536)
    mem[0x0001] = 7
    return mem


def test_VIC_II(test_memory):
    my_vic_ii = screen.VIC_II(test_memory)
    assert my_vic_ii

    test_memory[0xD020] = 250
    assert my_vic_ii.border_color == 10
    assert test_memory[0xD020] == 250

    test_memory[0xD021] = 249
    assert my_vic_ii.background_color == 9
    assert test_memory[0xD021] == 249

    test_memory[0xD022] = 248
    assert my_vic_ii.background_color_1 == 8
    assert test_memory[0xD022] == 248

    test_memory[0xD023] = 16
    assert my_vic_ii.background_color_2 == 0
    assert test_memory[0xD023] == 16

    test_memory[0xD024] = 1
    assert my_vic_ii.background_color_3 == 1
    assert test_memory[0xD024] == 1

    test_memory[0xDD00] = 0b11
    assert my_vic_ii.memory_bank == 0x0000
    test_memory[0xDD00] = 0b10
    assert my_vic_ii.memory_bank == 0x4000
    test_memory[0xDD00] = 0b01
    assert my_vic_ii.memory_bank == 0x8000
    test_memory[0xDD00] = 0b00
    assert my_vic_ii.memory_bank == 0xC000

    test_memory[0xDD00] = 0b11
    test_memory[0xD018] = 0x10
    assert my_vic_ii.video_matrix_base_address == 0x0400

    test_memory[0xDD00] = 0b00
    test_memory[0xD018] = 0xF0
    assert my_vic_ii.video_matrix_base_address == 0xFC00

    test_memory[0xDD00] = 0b11
    test_memory[0xD018] = 0x05
    assert my_vic_ii.character_generator_base_address == 0x1000

    test_memory[0xDD00] = 0b11
    test_memory[0xD018] = 0x09
    assert my_vic_ii.character_generator_base_address == 0x2000

    test_memory[0xDD00] = 0b00
    test_memory[0xD018] = 0x09
    assert my_vic_ii.character_generator_base_address == 0xE000
