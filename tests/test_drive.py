import pytest

from hardware import disk_drive


@pytest.fixture
def my_drive() -> disk_drive.Drive:
    drive = disk_drive.Drive()
    drive.set_imagefile("test_image.d64")
    return drive


def test_drive_properties(my_drive):
    assert my_drive

    assert my_drive.image_file == "test_image.d64"

    my_drive.set_filename("foo/bar.d64")
    assert my_drive.filename == "foo/bar.d64"

    my_drive.set_filename("demo")
    assert my_drive.filename == "demo"


def test_drive_read(my_drive):
    read = my_drive.read(b"HELLO")

    assert len(read) == 24
    assert read == b'\x01\x08\x15\x08\n\x00\x99 "HELLO WORLD"\x00\x00\x00'
