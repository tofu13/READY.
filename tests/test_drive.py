import pytest

from libs.hardware import disk_drive

TEST_DISK_IMAGE = "tests/testimage.d64"


@pytest.fixture()
def my_drive() -> disk_drive.Drive:
    drive = disk_drive.Drive()
    drive.set_imagefile(TEST_DISK_IMAGE)
    return drive


def test_drive_properties(my_drive):
    assert my_drive

    assert my_drive.image_file == TEST_DISK_IMAGE


def test_drive_read(my_drive):
    read = my_drive.read(b"HELLO")

    assert len(read) == 36
    assert (
        read
        == b'\x01\x08!\x08\n\x00\x8b "FOO" \xb2 "BAR" \xa7 \x99 "SPAM!"\x00\x00\x00'
    )
