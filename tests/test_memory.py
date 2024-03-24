import pytest

import config
from hardware.memory import BytearrayMemory
from hardware import roms


@pytest.fixture
def memory():
    return BytearrayMemory(65536)


@pytest.fixture()
def memory_with_roms():
    memory = BytearrayMemory(65536, roms=roms.ROMS("../" + config.ROMS_FOLDER))
    memory.hiram = True
    memory.loram = True
    memory.chargen = True
    return memory


def test_instance(memory):
    assert isinstance(memory, BytearrayMemory)


def test_write_read_cell(memory):
    memory[42] = 24
    assert memory[42] == 24


def test_write_read_slice(memory):
    data = bytearray(range(0xFF))
    memory.set_slice(0xC000, data)
    assert memory.get_slice(0xC000, 0xC0FF) == data


def test_read_direct(memory):
    def dummy_read_watcher(address, value):
        return 0

    memory.read_watchers.append((0xD000, 0xDFFF, dummy_read_watcher))
    # enable CHAREN
    memory[1] = 4

    memory[0xDF00] = 24
    assert memory[0xDF00] == 0
    assert memory.read(0xDF00) == 24


def test_write_direct(memory):
    def dummy_write_watcher(address, value):
        pytest.fail("Should not be called")

    memory.write_watchers.append((0xD000, 0xDFFF, dummy_write_watcher))
    # enable CHAREN
    memory[1] = 4

    memory.write(0xDF00, 24)
    assert memory[0xDF00] == 0
    assert memory.read(0xDF00) == 24


def test_read_read_word(memory_with_roms):
    memory_with_roms[0xC000] = 0xCD
    memory_with_roms[0xC001] = 0xAB

    assert memory_with_roms.read_address(0xC000) == 0xABCD
    assert memory_with_roms.read_address(0xFFFC) == 0xFCE2
