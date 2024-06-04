import pathlib
import pytest

import config
import hardware


@pytest.fixture
def c64():
    roms = hardware.roms.ROMS(config.TESTING_ROMS_FOLDER)
    memory = hardware.memory.Memory(roms=roms)
    return hardware.machine.Machine(
        memory=memory,
        cpu=hardware.cpu.CPU(memory),
        screen=hardware.screen.VirtualScreen(memory),
        ciaA=hardware.cia.CIA_A(memory),
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
