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
