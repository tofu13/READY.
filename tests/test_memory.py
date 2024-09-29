import pytest

import config
from libs.hardware import roms
from libs.hardware.memory import Memory


@pytest.fixture()
def memory() -> Memory:
    return Memory()


@pytest.fixture()
def memory_with_roms() -> Memory:
    """
    Memory with default configuration:
    BASIC ROM is active
    KERNAL ROM is active
    I/O is active
    """
    memory = Memory(roms=roms.ROMS(config.TESTING_ROMS_FOLDER))
    memory.cpu_write(0x00, 0x07)
    memory.cpu_write(0x01, 0x07)
    return memory


def test_cpu_ports(memory_with_roms):
    assert memory_with_roms.loram_port is True
    assert memory_with_roms.hiram_port is True
    assert memory_with_roms.io_port is True

    # Make only loram port writable
    memory_with_roms.cpu_write(0x00, 0b001)

    # Try to reset all ports
    memory_with_roms.cpu_write(0x01, 0b000)

    assert memory_with_roms.loram_port is False
    assert memory_with_roms.hiram_port is True
    assert memory_with_roms.io_port is True

    # Restore ports
    memory_with_roms.cpu_write(0x01, 0b111)
    assert memory_with_roms.loram_port is True
    assert memory_with_roms.hiram_port is True
    assert memory_with_roms.io_port is True


def test_memory_cell(memory):
    memory[42] = 24
    assert memory[42] == 24


def test_memory_slice(memory):
    data = bytearray(range(0xFF))
    memory[0xC000:0xC0FF] = data
    assert memory[0xC000:0xC0FF] == data


def test_read_read_address(memory_with_roms):
    memory_with_roms[0xC000] = 0xCD
    memory_with_roms[0xC001] = 0xAB

    assert memory_with_roms.read_address(0xC000) == 0xABCD

    assert memory_with_roms.read_address(0xFFFE) == 0x6810  # value from test roms
    assert memory_with_roms.read_address(0xA000) == 0x914F  # value from test roms


def test_memory_as_seen_by_cpu(memory_with_roms):
    memory_with_roms.cpu_write(0xC000, 42)
    assert memory_with_roms.cpu_read(0xC000) == 42

    assert memory_with_roms.cpu_read(0xA000) == 79  # value from test roms

    # Set I/O false to access chargen ROM
    memory_with_roms.cpu_write(0x00, 0x04)
    memory_with_roms.cpu_write(0x01, 0x00)

    # CPU write into active ROM area
    memory_with_roms.cpu_write(0xA000, 42)
    assert memory_with_roms.cpu_read(0xA000) == 79  # value from test roms
    assert memory_with_roms[0xA000] == 42

    memory_with_roms.cpu_write(0xFFFF, 42)
    assert memory_with_roms.cpu_read(0xFFFF) == 104  # value from test roms
    assert memory_with_roms[0xFFFF] == 42

    memory_with_roms.cpu_write(0xD020, 42)
    assert memory_with_roms.cpu_read(0xD020) == 95  # value from test roms
    assert memory_with_roms[0xD020] == 42


def test_read_watcher(memory_with_roms):
    def read_watcher(address):
        return 42

    memory_with_roms.read_watchers.append((0xD000, 0xDFFF, read_watcher))

    assert memory_with_roms.cpu_read(0xD020) == 42


def test_write_watcher(memory_with_roms):
    def write_watcher(address, value):
        raise AssertionError()

    memory_with_roms.write_watchers.append((0xD000, 0xDFFF, write_watcher))

    # Assert watcher is called
    with pytest.raises(AssertionError):
        memory_with_roms.cpu_write(0xD020, 42)


def test_vic_read(memory_with_roms):
    # Set bank 0 ($0000-$3FFF)

    # Mock bank select by CIA_B
    memory_with_roms.vic_memory_bank = 0x0000

    memory_with_roms[0x0400] = 42
    assert memory_with_roms.vic_read(0x0400) == 42
    assert memory_with_roms.vic_read(0x1000) == 16  # value from test roms

    # Set bank 3 ($C000-$FFFF)
    memory_with_roms.vic_memory_bank = 0xC000

    memory_with_roms[0xC400] = 42
    assert memory_with_roms.vic_read(0x0400) == 42
    assert memory_with_roms.vic_read(0x1000) == 0


def test_dump(memory_with_roms):
    for i in range(0x10):
        memory_with_roms[0xC000 + i] = i + 32
    assert (
        memory_with_roms.dump(0xC000, 0xC010)
        == "$C000:  20 21 22 23  24 25 26 27  28 29 2A 2B  2C 2D 2E 2F    !\"#$%&'()*+,-./\n"
    )


@pytest.mark.parametrize(
    ("mem", "disassembled"),
    [
        ([0x52], ("52         JAM ", 1)),
        ([0x18], ("18         CLC ", 1)),
        ([0xA9, 0x42], ("A9 42      LDA #$42", 2)),
        ([0xD0, 0xFB], ("D0 FB      BNE $BFFD", 2)),
        ([0xA5, 0x02], ("A5 02      LDA $02", 2)),
        ([0xB5, 0x02], ("B5 02      LDA $02,X", 2)),
        ([0xB6, 0x02], ("B6 02      LDX $02,Y", 2)),
        ([0x41, 0x47], ("41 47      EOR ($47,X)", 2)),
        ([0xD1, 0xA8], ("D1 A8      CMP ($A8),Y", 2)),
        ([0xBD, 0x34, 0x12], ("BD 34 12   LDA $1234,X", 3)),
        ([0xB9, 0x21, 0x43], ("B9 21 43   LDA $4321,Y", 3)),
        ([0x4C, 0x00, 0xC0], ("4C 00 C0   JMP $C000", 3)),
        ([0x6C, 0xFE, 0xFF], ("6C FE FF   JMP ($FFFE)", 3)),
    ],
)
def test_disassemble(memory_with_roms, mem, disassembled):
    memory_with_roms[0xC000:0xC003] = mem
    assert memory_with_roms.disassemble(0xC000) == disassembled
