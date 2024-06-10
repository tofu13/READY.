import pytest

import config
from hardware.cpu import CPU
from hardware.memory import Memory
from hardware.roms import ROMS


@pytest.fixture
def cpu():
    return CPU(Memory(roms=ROMS(config.TESTING_ROMS_FOLDER)))


def test_cpu_defaults(cpu):
    assert cpu.A == 0
    assert cpu.X == 0
    assert cpu.Y == 0
    assert cpu.PC == 0x0000
    assert cpu.SP == 0xFF
    assert (cpu.F['N']) is False
    assert cpu.F['V'] is False
    assert cpu.F['B'] is False
    assert cpu.F['D'] is False
    assert cpu.F['I'] is True
    assert cpu.F['Z'] is False
    assert cpu.F['C'] is False

    assert cpu._pack_status_register(cpu.F) == 0b00100100
    assert str(cpu) == "0000  00         BRK           - A:00 X:00 Y:00 SP:FF ..-..I.."


def test_cpu_registers(cpu):
    cpu.A = 0xFF
    cpu.X = 0xFF
    cpu.Y = 0xFF
    cpu.PC = 0XFFFF
    cpu.SP = 0X00
    cpu.F = {
        'N': True,
        'V': True,
        '-': True,  # Bad
        'B': True,
        'D': True,
        'I': False,
        'Z': True,
        'C': True,
    }

    assert str(cpu) == "FFFF  00         BRK           - A:FF X:FF Y:FF SP:00 NV-BD.ZC"


def test_cpu_stack(cpu):
    cpu.push(0x42)
    assert cpu.SP == 0xFE

    cpu.push(0xAB)
    assert cpu.SP == 0xFD

    assert cpu.pop() == 0xAB
    assert cpu.SP == 0xFE

    assert cpu.pop() == 0x42
    assert cpu.SP == 0xFF


@pytest.mark.parametrize("value, N, Z", [
    (0x00, False, True),
    (0x01, False, False),
    (0x7F, False, False),
    (0x80, True, False),
    (0x81, True, False),
    (0xFF, True, False),
])
def test_cpu_setNZ(cpu, value, N, Z):
    cpu._setNZ(value)
    assert cpu.F["N"] is N
    assert cpu.F["Z"] is Z


def test_cpu_combine(cpu):
    assert cpu._combine(0x34, 0x12) == 0x1234


@pytest.mark.parametrize("method, expected, advance", [
    ("IMP", None, 0),
    ("IMM", 0XC000, 1),
    ("REL", 0X02, 1),
    ("ABS", 0XC002, 2),
    ("ZP", 0X02, 1),
    ("ABS_X", 0XC003, 2),
    ("ABS_Y", 0XC004, 2),
    ("ZP_X", 0X03, 1),
    ("ZP_Y", 0X04, 1),
    ("IND", 0X1234, 2),
    ("X_IND", 0XABCD, 1),
    ("IND_Y", 0X34A2, 1),

])
def test_cpu_addressing_methods(cpu, method, expected, advance):
    cpu.memory.cpu_write(0xC000, 0x02)
    cpu.memory.cpu_write(0xC001, 0xC0)
    cpu.memory.cpu_write(0xC002, 0x34)
    cpu.memory.cpu_write(0xC003, 0x12)
    cpu.memory.cpu_write(0x0002, 0xA0)
    cpu.memory.cpu_write(0x0003, 0x34)
    cpu.memory.cpu_write(0x0004, 0x12)
    cpu.memory.cpu_write(0x0034, 0xCD)
    cpu.memory.cpu_write(0x0035, 0xAB)

    cpu.X = 0x01
    cpu.Y = 0x02
    cpu.PC = 0xC000

    assert getattr(cpu, f"addressing_{method}")() == expected
    assert cpu.PC == 0xC000 + advance
