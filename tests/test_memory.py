from unittest import TestCase
from hardware.memory import BytearrayMemory


class TestMemory(TestCase):
    def setUp(self) -> None:
        self.memory = BytearrayMemory(65536)

    def test_instance(self):
        self.assertIsInstance(self.memory, BytearrayMemory)

    def test_write_read_cell(self):
        self.memory[42] = 24
        self.assertEqual(24, self.memory[42])

    def test_write_read_slice(self):
        data = bytearray(range(0xFF))
        self.memory.set_slice(0xC000, data)
        self.assertEqual(self.memory.get_slice(0xC000, 0xC0FF), data)

    def test_read_direct(self):
        def dummy_read_watcher(address, value):
            return 0

        self.memory.read_watchers.append((0xD000, 0xDFFF, dummy_read_watcher))
        # enable CHAREN
        self.memory[1] = 4

        self.memory[0xDF00] = 24
        self.assertEqual(self.memory[0xDF00], 0)
        self.assertEqual(self.memory.read(0xDF00), 24)

    def test_write_direct(self):
        def dummy_write_watcher(address, value):
            self.fail("Should not be called")

        self.memory.write_watchers.append((0xD000, 0xDFFF, dummy_write_watcher))
        # enable CHAREN
        self.memory[1] = 4

        self.memory.write(0xDF00, 24)
        self.assertEqual(self.memory[0xDF00], 0)
        self.assertEqual(self.memory.read(0xDF00), 24)
