import pytest

from hardware.memory import Memory
from hardware import roms

import config


@pytest.fixture
def memory() -> Memory:
    return Memory()


@pytest.fixture()
def memory_with_roms() -> Memory:
    memory = Memory(roms=roms.ROMS(config.TESTING_ROMS_FOLDER))
    memory.hiram = True
    memory.loram = True
    memory.charen = True
    return memory


def test_instance(memory):
    assert isinstance(memory, Memory)


def test_memory_cell(memory):
    memory[42] = 24
    assert memory[42] == 24


def test_memory_slice(memory):
    data = bytearray(range(0xFF))
    memory[0xC000: 0xC0FF] = data
    assert memory[0xC000: 0xC0FF] == data


def test_read_read_word(memory):
    memory[0xC000] = 0xCD
    memory[0xC001] = 0xAB

    assert memory.read_address(0xC000) == 0xABCD


def test_memory_as_seen_by_cpu(memory_with_roms):
    memory_with_roms.cpu_write(0XC000, 42)
    assert memory_with_roms.cpu_read(0xC000) == 42

    assert memory_with_roms.cpu_read(0xA000) == 79  # value from test roms
    # CPU write into active ROM area
    memory_with_roms.cpu_write(0xA000, 42)
    assert memory_with_roms.cpu_read(0xA000) == 79  # value from test roms
    assert memory_with_roms[0xA000] == 42


def test_read_watcher(memory_with_roms):
    def read_watcher(address, value):
        return 42

    memory_with_roms.read_watchers.append((0xD000, 0xDFFF, read_watcher))

    assert memory_with_roms.cpu_read(0xD020) == 42


def test_write_watcher(memory_with_roms):
    def write_watcher(address, value):
        raise Exception

    memory_with_roms.write_watchers.append((0xD000, 0XDFFF, write_watcher))

    # Assert watcher is called
    with pytest.raises(Exception):
        memory_with_roms.cpu_write(0xD020, 42)


def test_vic_read(memory_with_roms):
    # Set bank 0 ($0000-$3FFF)
    memory_with_roms[0xDD00] = 3

    memory_with_roms[0x0400] = 42
    assert memory_with_roms.vic_read(0x0400) == 42
    assert memory_with_roms.vic_read(0x1000) == 16  # value from test roms

    # Set bank 3 ($C000-$FFFF)
    memory_with_roms[0xDD00] = 0

    memory_with_roms[0xC400] = 42
    assert memory_with_roms.vic_read(0x0400) == 42
    assert memory_with_roms.vic_read(0x1000) == 0
