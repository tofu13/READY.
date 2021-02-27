import os

from .utils import *

class ROMS:
    def __init__(self, roms_folder):
        self.contents = {}
        self.load(roms_folder)

    def load(self, roms_folder):
        for name, begin, end, bank_bit in ROMSLIST:
            with open(os.path.join(roms_folder, name), 'rb') as rom:
                self.contents[name] = bytearray(rom.read())

    def init(self):
        for name, begin, end, bank_bit in ROMSLIST:
            self.memory.read_watchers.append([begin, end, self.read_rom])

        # Set default bank switching (all roms on)
        self.memory[0x0000] = 0xE9
        self.memory[0x0001] = 0x07

    def read_rom(self, address, value):
        for name, begin, end, bank_bit in ROMSLIST:
            # Check bank switching bit too
            if begin <= address <= end and bit(self.memory[SYMBOLS['R6510']], bank_bit):
                return self.contents[name][address-begin]
        return value
