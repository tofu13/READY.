from multiprocessing import Array
from hardware.constants import OPCODES


class Memory:
    read_watchers = []
    write_watchers = []
    roms = {}
    chargen, loram, hiram = None, None, None

    def __getitem__(self, address: int) -> int:
        # print(f"Memory read at {address}: {value}")
        if 0xA000 <= address <= 0xBFFF and self.hiram and self.loram:
            return self.roms['basic'][address - 0xA000]
        elif 0xE000 <= address <= 0xFFFF and self.hiram:
            return self.roms['kernal'][address - 0xE000]
        elif 0xD000 <= address <= 0xDFFF:
            if not self.chargen and (not self.hiram and not self.loram):
                return self.roms['chargen'][address - 0xD000]
            else:
                for start, end, callback in self.read_watchers:
                    if start <= address <= end:
                        return callback(address, super().__getitem__(address))

        return super().__getitem__(address)

    def __setitem__(self, address: int, value: int) -> None:
        # Hard coded processor port at $01
        if address == 1:
            self.chargen, self.loram, self.hiram = map(bool, map(int, f"{value & 0x7:03b}"))
            # Set only writable bits in the processor port
            value &= self[0x00]
            value |= self[0x01] & (255 - self[0])

        for start, end, callback in self.write_watchers:
            if start <= address <= end:
                callback(address, value)
                break

        # print(f"Memory write at {key}: {value}")
        super().__setitem__(address, value)

    def __str__(self):
        return self.dump()

    def dump(self, start: int = None, end: int = None, as_chars: bool = False) -> str:
        """
        Return a textual representiation of memory from start to end
        :param as_chars:
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
        step = 0x20 if as_chars else 0x10

        out = ""
        for row in range(start, end, step):
            data = self.get_slice(row, row + step)
            data_hex = [f"{'' if i % 4 else ' '}{byte:02X} " for i, byte in enumerate(data)]
            data_char = map(lambda x: chr(x) if 32 < x < 127 else '.', data)

            out += f"${row:04X}: "
            if as_chars:
                out += f"{''.join(data_char)}\n"
            else:
                out += f"{''.join(data_hex)}  {''.join(data_char)}\n"
        return out

    def disassemble(self, address) -> str:
        """
        Return disassembled memory
        :param address:
        :return:
        """
        output = ""
        instruction, mode = OPCODES[self[address]]

        # Skip data bytes (or invalid opcodes)
        instruction = instruction or "???"

        if mode == "IMP":
            arg = ""
            step = 1
        elif mode == "ABS":
            arg = f"${self[address + 2]:02X}{self[address + 1]:02X}"
            step = 3
        elif mode == "ABS_X":
            arg = f"${self[address + 2]:02X}{self[address + 1]:02X},X"
            step = 3
        elif mode == "ABS_Y":
            arg = f"${self[address + 2]:02X}{self[address + 1]:02X},Y"
            step = 3
        elif mode == "REL":
            delta = self[address + 1]
            arg = f"${(address + delta + 2 if delta < 127 else address + delta - 254):04X}"
            step = 2
        elif mode == "IMM":
            arg = f"#${self[address + 1]:02X}"
            step = 2
        elif mode == "ZP":
            arg = f"${self[address + 1]:02X}"
            step = 2
        elif mode == "ZP_X":
            arg = f"${self[address + 1]:02X},X"
            step = 2
        elif mode == "ZP_Y":
            arg = f"${self[address + 1]:02X},Y"
            step = 2
        elif mode == "IND":
            arg = f"$({self[address + 2]:02X}{self[address + 1]:02X})"
            step = 3
        elif mode == "X_IND":
            arg = f"$({self[address + 1]:02X},X)"
            step = 3
        elif mode == "IND_Y":
            arg = f"$({self[address + 1]:02X}),Y"
            step = 3
        else:
            # Skip invalid addressing mode
            arg = ""
            step = 1

        # Compose line
        output += f"${address:04X}  {' '.join([f'{self[_]:02X}' for _ in range(address, address + step)])}" \
                  f"{'   ' * (4 - step)}{instruction} {arg}"
        address = (address + step) & 0xFFFF

        return output, step

    def read(self, address) -> int:
        """
        Direct read from memory, no masking
        """
        return super().__getitem__(address)

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
            lo, hi = super().__getitem__(slice(address, address + 2))
        return hi * 256 + lo

    def write(self, address, value) -> None:
        """
        Direct write to memory, no masking
        """
        super().__setitem__(address, value)

    def get_slice(self, start: int, end: int) -> bytearray:
        """
        Return memory from start to end in a bytearray
        Warning: ignores ROMs masking, data are always read from (underlying) memory
        :param start:
        :param end:
        :return:
        """
        return super().__getitem__(slice(start, end))

    def set_slice(self, start: int, data) -> None:
        """
        Set data into memory starting from start
        :param start:
        :param data:
        :return:
        """
        super().__setitem__(slice(start, start + len(data)), data)

    def get_chargen(self) -> bytearray:
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
