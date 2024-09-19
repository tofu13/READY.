import pytest

from libs.hardware.bus import Bus


@pytest.fixture()
def mybus():
    return Bus()


def test_bus_detect_nmi_single_source(mybus):
    assert mybus.nmi is False

    mybus.nmi_set("test_nmi")
    # Detect ramp
    assert mybus.nmi is True
    # Ack'ed
    assert mybus.nmi is False


def test_bus_detect_nmi_many_sources(mybus):
    assert mybus.nmi is False

    mybus.nmi_set("test_nmi_1")
    mybus.nmi_set("test_nmi_2")
    # Detect ramp
    assert mybus.nmi is True
    # Ack'ed
    assert mybus.nmi is False
    # Cleanup

    # Clear a source
    mybus.nmi_clear("test_nmi_1")

    assert mybus.nmi is False

    # Re-raise while other source is up
    mybus.nmi_set("test_nmi_1")
    assert mybus.nmi is False


def test_bus_detect_irq_single_source(mybus):
    assert mybus.irq is False

    mybus.irq_set("test_irq")
    assert mybus.irq is True
    assert mybus.irq is True


def test_bus_detect_irq_many_sources(mybus):
    assert mybus.irq is False

    mybus.irq_set("test_irq_1")
    mybus.irq_set("test_irq_2")
    assert mybus.irq is True

    # Clear a source
    mybus.irq_clear("test_irq_1")

    assert mybus.irq is True

    # Clear a source
    mybus.irq_clear("test_irq_2")
    assert mybus.irq is False


def test_memory_sub(mybus):
    assert mybus.memory_bus_required() is False

    mybus.require_memory_bus(2)

    assert mybus.memory_bus_required() is True
    assert mybus.memory_bus_required() is True
    assert mybus.memory_bus_required() is False
    assert mybus.memory_bus_required() is False
