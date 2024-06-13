import pytest

from hardware.cia import CIA
from hardware.memory import Memory


@pytest.fixture
def cia() -> CIA:
    return CIA(Memory())



@pytest.fixture
def cia_a(memory):
    return cia_a(memory)

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
