class Memory:
    read_watchers = []
    write_watchers = []

    def __getitem__(self, address):
        value = super().__getitem__(address)
        #print(f"Memory read at {item}: {value}")
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

    def read(self, address):
        """
        Direct read of address, no watchers involved
        :param address:
        :return: the value at address
        """
        return super().__getitem__(address)

    def write(self, address, value):
        """
        Direct write of address, no watchers involved
        :param address:
        :return:
        """
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