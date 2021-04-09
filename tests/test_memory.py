from unittest import TestCase
from hardware.memory import *

class TestMemory(TestCase):
    def setUp(self) -> None:
        self.memory = BytearrayMemory(65536)

    def test_instance(self):
        self.assertIsInstance(self.memory, Memory)

    def test_write_read_cell(self):
        self.memory[42] = 24
        self.assertEqual(24, self.memory[42])

    def test_write_read_slice(self):
        data = bytearray(range(0xFF))
        self.memory.set_slice(0xC000, data)
        self.assertEqual(self.memory.get_slice(0xC000, 0xC0FF), data)

