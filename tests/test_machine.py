import pathlib

import pytest

import config
from libs import hardware


@pytest.fixture()
def c64():
    roms = hardware.roms.ROMS(config.TESTING_ROMS_FOLDER)
    memory = hardware.memory.Memory(roms=roms)
    bus = hardware.bus.Bus()
    return hardware.machine.Machine(
        memory=memory,
        bus=bus,
        cpu=hardware.cpu.CPU(memory, bus),
        screen=hardware.screen.VirtualScreen(memory, bus),
        ciaA=hardware.cia.CIA_A(memory, bus),
        ciaB=hardware.cia.CIA_B(memory, bus),
        diskdrive=hardware.disk_drive.Drive(),
    )


def test_machine_save(c64):
    state_file = pathlib.Path("save_state")
    state_file.unlink(missing_ok=True)

    c64.save("save_state")

    state_file = pathlib.Path("save_state")
    assert state_file.exists()


def test_machine_load():
    state_file = pathlib.Path("save_state")
    assert state_file.exists(), "missing state file"

    my_c64 = hardware.machine.Machine.from_file("save_state")

    assert my_c64
