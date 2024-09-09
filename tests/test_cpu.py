import pytest

import config
from libs.hardware.bus import Bus
from libs.hardware.cpu import CPU
from libs.hardware.memory import Memory
from libs.hardware.roms import ROMS


@pytest.fixture()
def cpu() -> CPU:
    return CPU(Memory(roms=ROMS(config.TESTING_ROMS_FOLDER)), Bus())


bcd_testcases = (
    ["binary", "decimal"],
    [
        (0x00, 0),
        (0x11, 11),
        (0x42, 42),
        (0x99, 99),
    ],
)


@pytest.mark.parametrize(*bcd_testcases)
def test_binary_to_decimal(binary, decimal):
    assert CPU.binary_to_decimal(binary) == decimal


@pytest.mark.parametrize(*bcd_testcases)
def test_decimal_to_binary(binary, decimal):
    assert CPU.decimal_to_binary(decimal) == binary


def test_cpu_defaults(cpu):
    assert cpu.A == 0
    assert cpu.X == 0
    assert cpu.Y == 0
    assert cpu.PC == 0x0000
    assert cpu.SP == 0xFF
    assert cpu.flag_N is False
    assert cpu.flag_V is False
    assert cpu.flag_B is False
    assert cpu.flag_D is False
    assert cpu.flag_I is True
    assert cpu.flag_Z is False
    assert cpu.flag_C is False

    assert cpu.pack_status_register() == 0b00100100
    assert str(cpu) == "0000  00         BRK           - A:00 X:00 Y:00 SP:FF ..-..I.."


def test_cpu_registers(cpu):
    cpu.A = 0xFF
    cpu.X = 0xFF
    cpu.Y = 0xFF
    cpu.PC = 0xFFFF
    cpu.SP = 0x00
    cpu.flag_N = True
    cpu.flag_V = True
    cpu.flag_B = True
    cpu.flag_D = True
    cpu.flag_I = False
    cpu.flag_Z = True
    cpu.flag_C = True

    assert str(cpu) == "FFFF  68         PLA           - A:FF X:FF Y:FF SP:00 NV-BD.ZC"


def test_cpu_stack(cpu):
    cpu.push(0x42)
    assert cpu.SP == 0xFE

    cpu.push(0xAB)
    assert cpu.SP == 0xFD

    assert cpu.pop() == 0xAB
    assert cpu.SP == 0xFE

    assert cpu.pop() == 0x42
    assert cpu.SP == 0xFF


def test_cpu_irq(cpu):
    cpu.PC = 0xC000
    cpu.flag_I = True
    cpu.irq()
    assert cpu.flag_I is True

    cpu.flag_I = False
    cpu.irq()
    assert cpu.flag_I is True
    assert cpu.PC == 0x6810  # Value from testing roms


def test_cpu_nmi(cpu):
    cpu.PC = 0xC000
    cpu.nmi()
    assert cpu.PC == 0xBA2E  # Value from testing roms


@pytest.mark.parametrize(
    ("value", "N", "Z"),
    [
        (0x00, False, True),
        (0x01, False, False),
        (0x7F, False, False),
        (0x80, True, False),
        (0x81, True, False),
        (0xFF, True, False),
    ],
)
def test_cpu_setNZ(cpu, value, N, Z):
    cpu.setNZ(value)
    assert cpu.flag_N is N
    assert cpu.flag_Z is Z


def test_cpu_combine(cpu):
    assert cpu.make_address(0x34, 0x12) == 0x1234


def test_cpu_save_state(cpu):
    cpu.PC = 0x1234
    cpu.flag_N = True
    cpu.flag_V = True
    cpu.flag_B = True
    cpu.flag_D = True
    cpu.flag_I = False
    cpu.flag_Z = True
    cpu.flag_C = True

    cpu.save_state()

    assert cpu.pop() == 0b11111011
    assert cpu.pop() == 0x34
    assert cpu.pop() == 0x12


@pytest.mark.parametrize(
    ("method", "expected", "advance"),
    [
        ("IMP", None, 0),
        ("IMM", 0xC000, 1),
        ("REL", 0x02, 1),
        ("ABS", 0xC002, 2),
        ("ZP", 0x02, 1),
        ("ABS_X", 0xC003, 2),
        ("ABS_Y", 0xC004, 2),
        ("ZP_X", 0x03, 1),
        ("ZP_Y", 0x04, 1),
        ("IND", 0x1234, 2),
        ("X_IND", 0xABCD, 1),
        ("IND_Y", 0x34A2, 1),
    ],
)
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


@pytest.mark.parametrize(
    ["carry_in", "accumulator", "operand", "result", "C", "Z"],
    [
        (False, 0x00, 0x00, 0x00, False, True),
        (True, 0x00, 0x00, 0x01, False, False),
        (False, 0x48, 0x13, 0x61, False, False),
        (True, 0x58, 0x46, 0x5, True, False),
        (False, 0x81, 0x92, 0x73, True, False),
    ],
)
def test_decimal_ADC(cpu, carry_in, accumulator, operand, result, C, Z):
    cpu.flag_D = True
    cpu.flag_C = carry_in
    cpu.A = accumulator
    cpu.memory[0x02] = operand
    cpu.ADC(0x02)

    assert cpu.A == result
    assert cpu.flag_C is C
    assert cpu.flag_Z is Z


@pytest.mark.parametrize(
    ["carry_in", "accumulator", "operand", "result", "C", "Z"],
    [
        (True, 0x00, 0x00, 0x00, False, True),
        (True, 0x46, 0x12, 0x34, True, False),
        (True, 0x40, 0x13, 0x27, True, False),
        (False, 0x32, 0x2, 0x29, True, False),
        (True, 0x12, 0x21, 0x91, False, False),
    ],
)
def test_decimal_SBC(cpu, carry_in, accumulator, operand, result, C, Z):
    cpu.flag_D = True
    cpu.flag_C = carry_in
    cpu.A = accumulator
    cpu.memory[0x02] = operand
    cpu.SBC(0x02)

    assert cpu.A == result
    assert cpu.flag_C is C
    assert cpu.flag_Z is Z
