from multiprocessing import Array


class Memory:
    read_watchers = []
    write_watchers = []
    roms = {}
    chargen, loram, hiram = None, None, None

    def __getitem__(self, address: int):
        # print(f"Memory read at {item}: {value}")
        if 0xA000 <= address <= 0xBFFF:
            if self.hiram and self.loram:
                return self.roms['basic'][address - 0xA000]
        elif 0xE000 <= address <= 0xFFFF:
            if self.hiram:
                return self.roms['kernal'][address - 0xE000]
        elif 0xD000 <= address <= 0xDFFF:
            if not self.chargen and (not self.hiram and not self.loram):
                return self.roms['chargen'][address - 0xD000]
            else:
                for start, end, callback in self.read_watchers:
                    if start <= address <= end:
                        return callback(address, super().__getitem__(address))

        return super().__getitem__(address)

    def __setitem__(self, address: int, value) -> None:
        if value < 0 or value > 255:
            raise ValueError(f"Trying to write to memory a value ({value}) out of range (0-255).")

        # Hard coded processor port at $01
        if address == 1:
            self.chargen, self.loram, self.hiram = map(bool, map(int, f"{value & 0x7:03b}"))

        for start, end, callback in self.write_watchers:
            if start <= address <= end:
                callback(address, value)
                break
        # print(f"Memory write at {key}: {value}")
        super().__setitem__(address, value)

    def __str__(self):
        return self.dump()

    def dump(self, start: int=None, end: int=None) -> str:
        """
        Return a textual representiation of memory from start to end
        :param start:
        :param end:
        :return:
        """
        if start is None:
            start = 0x0000
            end = 0xFFFF
        else:
            if end is None:
                end = start + 0x0100

        out = ""
        for row in range(start, end, 0x10):
            data = self.get_slice(row, row + 0x10)
            data_hex = [f"{'' if i%4 else ' '}{byte:02X} " for i, byte in enumerate(data)]
            data_char = map(lambda x: chr(x) if 32 < x < 127 else '.', data)

            out += f"${row:04X}: {''.join(data_hex)}  {''.join(data_char)}\n"
        return out

    def get_slice(self, start: int, end: int):
        """
        Return memory from start to end in a bytearray
        :param start:
        :param end:
        :return:
        """
        return bytearray([self[i] for i in range(start, end)])

    def set_slice(self, start: int, data) -> None:
        """
        Set data into memory starting from start
        :param start:
        :param data:
        :return:
        """
        for i, byte in enumerate(data):
            self[start + i] = byte

    def get_chargen(self):
        """
        Quick returns chargen rom
        :return:
        """
        return self.roms['chargen']


class BytearrayMemory(Memory, bytearray):
    """
    A memory class where data is stored into a bytearray
    """
    def __init__(self, size: int, roms=None):
        super().__init__(size)
        if roms is not None:
            self.roms = roms.contents


class CTypesMemory:
    read_watchers = []
    write_watchers = []
    roms = {}
    contents = Array('B', 65536)

    def __getitem__(self, address):
        # print(f"Memory read at {item}: {value}")
        value = self.contents[address]
        chargen, loram, hiram = map(int, f"{self.contents[1] & 0x7:03b}")

        if 0xA000 <= address <= 0xBFFF:
            if hiram and loram:
                return self.roms['basic'][address - 0xA000]
        elif 0xE000 <= address <= 0xFFFF:
            if hiram:
                return self.roms['kernal'][address - 0xE000]
        elif 0xD000 <= address <= 0xDFFF:
            if not chargen and (not hiram and not loram):
                return self.roms['chargen'][address - 0xD000]
            elif chargen:
                for start, end, callback in self.read_watchers:
                    if start <= address <= end:
                        return callback(address, value)
        return value

    def __setitem__(self, address, value):
        if value < 0 or value > 255:
            raise ValueError(f"Trying to write to memory a value ({value}) out of range (0-255).")
        for start, end, callback in self.write_watchers:
            if start <= address <= end:
                callback(address, value)
                break
        # print(f"Memory write at {key}: {value}")
        self.contents[address] = value


if __name__ == '__main__':
    m = BytearrayMemory(65536)
    print(m)
