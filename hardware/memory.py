class Memory:
    def __init__(self, ram=None, roms=None):
        """
        Memory class that implements PLA for routing reads and write
        to/from RAM, ROMS, I/O.
        """
        self.ram = ram if ram is not None else bytearray(65536)
        self.roms = roms.contents if roms is not None else dict()

        self.charen, self.loram, self.hiram = True, True, True
        self.read_watchers = []
        self.write_watchers = []

    def __getitem__(self, item):
        return self.ram[item]

    def __setitem__(self, key, value):
        self.ram[key] = value

    def cpu_read(self, address: int | slice) -> int:
        """Return memory content (RAM, ROM, I/O) as seen by the cpu"""
        if 0xA000 <= address <= 0xBFFF and self.hiram and self.loram:
            return self.roms['basic'][address - 0xA000]
        elif 0xE000 <= address <= 0xFFFF and self.hiram:
            return self.roms['kernal'][address - 0xE000]
        elif 0xD000 <= address <= 0xDFFF:
            if not self.charen and (self.hiram or self.loram):
                return self.roms['chargen'][address - 0xD000]
            else:
                for start, end, callback in self.read_watchers:
                    if start <= address <= end:
                        return callback(address, self.ram[address])
        return self.ram[address]

    def cpu_write(self, address: int, value: int):
        """Write into RAM or I/O depending on CPU ports"""
        # Hard coded processor port at $01
        if address == 1:
            self.charen, self.loram, self.hiram = map(bool, map(int, f"{value & 0x7:03b}"))
            # Set only writable bits in the processor port
            value &= self.ram[0x00]
            value |= self.ram[0x01] & (255 - self.ram[0])

        for start, end, callback in self.write_watchers:
            if start <= address <= end:
                callback(address, value)
                break

        # Anyway, write into RAM
        self.ram[address] = value

    def vic_read(self, address: int) -> int:
        """Returns memory content as seen by VIC-II"""
        memory_bank = (3 - (self[0xDD00] & 0b11) << 14)

        # CHARGEN ROM is visible in banks 0 and 2 at $1000-1FFF
        if memory_bank in {0x0000, 0x8000} and 0x1000 <= address < 0x2000:
            return self.roms["chargen"][address - 0x1000]

        return self[memory_bank + address]

    def read_address(self, address: int) -> int:
        """
        Optimized consecutive reads
        Return big endian word (16-bit address)
        """
        if 0xA000 <= address <= 0xBFFF and self.hiram and self.loram:
            lo, hi = self.roms['basic'][address - 0xA000: address - 0xA000 + 2]
        elif 0xE000 <= address <= 0xFFFF and self.hiram:
            lo, hi = self.roms['kernal'][address - 0xE000: address - 0xE000 + 2]
        else:
            lo, hi = self.ram[address: address + 2]
        return hi * 256 + lo


class BytearrayMemory(Memory, bytearray):
    """
    A memory class where data is stored into a bytearray
    """

    def __init__(self, size: int, roms=None):
        super().__init__(size)
        if roms is not None:
            self.roms = roms.contents
