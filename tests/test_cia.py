import pygame
import pytest

from libs.hardware.cia import CIA, CIA_A
from libs.hardware.memory import Memory


@pytest.fixture()
def memory():
    # Dont need ROMS
    memory = Memory()
    # Enable I/O
    memory.cpu_write(0x00, 0xFF)
    memory.cpu_write(0x01, 0x0b100)

    return memory


@pytest.fixture()
def cia(memory) -> CIA:
    return CIA(memory)


@pytest.fixture()
def cia_a(memory):
    return CIA_A(memory)


def test_CIA_timer_A(cia):
    assert cia.timer_A == 0

    cia.timer_A_latch = 0x0002
    cia.timer_A_load()
    assert cia.timer_A == 0x0002
    assert cia.timer_A_lo == 0x02
    assert cia.timer_A_hi == 0x00

    cia.timer_A_start = True
    cia.clock()
    assert cia.timer_A == 0x0001
    assert cia.timer_A_lo == 0x01
    assert cia.timer_A_hi == 0x00

    cia.clock()
    assert cia.irq_occured is False

    cia.timer_A_restart_after_underflow = True
    cia.clock()
    assert cia.irq_occured is True
    assert cia.timer_A == 0x0002

    cia.timer_A_restart_after_underflow = False
    cia.clock()
    cia.clock()
    cia.clock()
    assert cia.timer_A == 0x0000
    assert cia.timer_A_start is False


def test_CIA_tod(cia):
    # TBD
    assert cia.tod == (0, 0, 0, 0)


@pytest.mark.parametrize(("pressed", "column", "expected"), [
    (set(), 0x00, 0x00),
    ({pygame.K_DELETE}, 0x01, 0x01),
    ({pygame.K_RETURN}, 0x01, 0x02),
    ({pygame.K_KP_ENTER}, 0x01, 0x02),
    ({pygame.K_RIGHT}, 0x01, 0x04),
    ({pygame.K_F7}, 0x01, 0x08),
    ({pygame.K_F1}, 0x01, 0x10),
    ({pygame.K_F3}, 0x01, 0x20),
    ({pygame.K_F5}, 0x01, 0x40),
    ({pygame.K_DOWN}, 0x01, 0x80),

    ({pygame.K_3}, 0x02, 0x01),
    ({pygame.K_KP3}, 0x02, 0x01),
    ({pygame.K_w}, 0x02, 0x02),
    ({pygame.K_a}, 0x02, 0x04),
    ({pygame.K_4}, 0x02, 0x08),
    ({pygame.K_KP4}, 0x02, 0x08),
    ({pygame.K_z}, 0x02, 0x10),
    ({pygame.K_s}, 0x02, 0x20),
    ({pygame.K_e}, 0x02, 0x40),
    ({pygame.K_LSHIFT}, 0x02, 0x80),

    ({pygame.K_5}, 0x04, 0x01),
    ({pygame.K_KP5}, 0x04, 0x01),
    ({pygame.K_r}, 0x04, 0x02),
    ({pygame.K_d}, 0x04, 0x04),
    ({pygame.K_6}, 0x04, 0x08),
    ({pygame.K_KP6}, 0x04, 0x08),
    ({pygame.K_c}, 0x04, 0x10),
    ({pygame.K_f}, 0x04, 0x20),
    ({pygame.K_t}, 0x04, 0x40),
    ({pygame.K_x}, 0x04, 0x80),

    ({pygame.K_7}, 0x08, 0x01),
    ({pygame.K_KP7}, 0x08, 0x01),
    ({pygame.K_y}, 0x08, 0x02),
    ({pygame.K_g}, 0x08, 0x04),
    ({pygame.K_8}, 0x08, 0x08),
    ({pygame.K_KP8}, 0x08, 0x08),
    ({pygame.K_b}, 0x08, 0x10),
    ({pygame.K_h}, 0x08, 0x20),
    ({pygame.K_u}, 0x08, 0x40),
    ({pygame.K_v}, 0x08, 0x80),

    ({pygame.K_9}, 0x10, 0x01),
    ({pygame.K_KP9}, 0x10, 0x01),
    ({pygame.K_i}, 0x10, 0x02),
    ({pygame.K_j}, 0x10, 0x04),
    ({pygame.K_0}, 0x10, 0x08),
    ({pygame.K_m}, 0x10, 0x10),
    ({pygame.K_k}, 0x10, 0x20),
    ({pygame.K_o}, 0x10, 0x40),
    ({pygame.K_n}, 0x10, 0x80),

    ({pygame.K_PLUS}, 0x20, 0x01),
    ({pygame.K_KP_PLUS}, 0x20, 0x01),
    ({pygame.K_p}, 0x20, 0x02),
    ({pygame.K_l}, 0x20, 0x04),
    ({pygame.K_MINUS}, 0x20, 0x08),
    ({pygame.K_KP_MINUS}, 0x20, 0x08),
    ({pygame.K_PERIOD}, 0x20, 0x10),
    ({pygame.K_KP_PERIOD}, 0x20, 0x10),
    ({pygame.K_COMMA}, 0x20, 0x80),

    ({pygame.K_KP_MULTIPLY}, 0x40, 0x02),
    ({pygame.K_HOME}, 0x40, 0x08),
    ({pygame.K_RSHIFT}, 0x40, 0x10),
    ({pygame.K_PAGEUP}, 0x40, 0x40),  # ^
    ({pygame.K_KP_DIVIDE}, 0x40, 0x80),

    ({pygame.K_1}, 0x80, 0x01),
    ({pygame.K_KP1}, 0x80, 0x01),
    ({pygame.K_BACKSLASH}, 0x80, 0x02),
    ({pygame.K_LCTRL}, 0x80, 0x04),
    ({pygame.K_2}, 0x80, 0x08),
    ({pygame.K_KP2}, 0x80, 0x08),
    ({pygame.K_SPACE}, 0x80, 0x10),
    ({pygame.K_LALT}, 0x80, 0x20),
    ({pygame.K_q}, 0x80, 0x40),
    ({pygame.K_ESCAPE}, 0x80, 0x80),

])
def test_CIA_A_keyboard(pressed, column, expected, cia_a):
    # Test only keymap-indipendent keys
    cia_a.memory.cpu_write(0xDC00, 0xFF - column)
    cia_a.clock(pressed)
    assert cia_a.memory.cpu_read(0xDC01) == 0xFF - expected
