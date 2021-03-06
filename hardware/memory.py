class Memory:
    read_watchers = []
    write_watchers = []
    roms = {}

    def __getitem__(self, address):
        #print(f"Memory read at {item}: {value}")
        value = super().__getitem__(address)
        chargen, loram, hiram  = map(int,f"{super().__getitem__(1) & 0x7:03b}")

        if 0xA000 <= address <= 0xBFFF:
            if hiram and loram:
                return self.roms['basic'][address - 0xA000]
        elif 0xE000 <= address <= 0xFFFF:
            if hiram:
                return self.roms['kernal'][address - 0xE000]
        elif 0xD000 <= address <= 0xDFFF:
            if not chargen and (not hiram and not loram):
                return self.roms['chargen'][address - 0xD000]
            elif chargen and (not hiram and not loram):
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
        #print(f"Memory write at {key}: {value}")
        super().__setitem__(address, value)

    def __str__(self, start=0x100, end=None):
        if end is None:
            end = start + 0x0100
        return "\n".join(
            [f"{i:04X}: {super(__class__, self).__getitem__(slice(i, i+16))}" for i in range(start, end, 16)]
        )


class BytearrayMemory(Memory, bytearray):
    pass


if __name__ == '__main__':
    m = BytearrayMemory(65536)
    print(m)