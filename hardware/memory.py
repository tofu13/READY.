from hardware.constants import SCREEN_CHARCODE, OPCODES


class Memory:
    def __init__(self, ram=None, roms=None):
        """
        Memory class that implements PLA for routing reads and write
        to/from RAM, ROMS, I/O.
        """
        self.ram = ram if ram is not None else bytearray(65536)
        self.roms = roms.contents if roms is not None else dict()

        self.read_watchers = []
        self.write_watchers = []

        # Internals
        self._io, self._loram, self._hiram = True, True, True

    def __getitem__(self, item):
        return self.ram[item]

    def __setitem__(self, key, value):
        self.ram[key] = value

    def cpu_read(self, address: int | slice) -> int:
        """Return memory content (RAM, ROM, I/O) as seen by the cpu"""
        if 0xA000 <= address <= 0xBFFF and self._hiram and self._loram:
            return self.roms['basic'][address - 0xA000]
        elif 0xE000 <= address <= 0xFFFF and self._hiram:
            return self.roms['kernal'][address - 0xE000]
        elif 0xD000 <= address <= 0xDFFF:
            if not self._io and (self._hiram or self._loram):
                return self.roms['chargen'][address - 0xD000]
            else:
                for start, end, callback in self.read_watchers:
                    if start <= address <= end:
                        return callback(address, self.ram[address])
        return self.ram[address]

    def cpu_write(self, address: int, value: int):
        """Write into RAM or I/O depending on CPU ports"""
        # Hard coded processor port at $01
        if address == 0x01:
            # Set only writable bits in the processor port
            mask = self.ram[0x00]
            self.ram[0x01] = ((255 - mask) & self.ram[0x01]) | (mask & value)
            # Update internal flags
            self._io, self._loram, self._hiram = map(bool, map(int, f"{self.ram[0x01] & 0x7:03b}"))
            return

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
        if 0xA000 <= address <= 0xBFFF and self._hiram and self._loram:
            lo, hi = self.roms['basic'][address - 0xA000: address - 0xA000 + 2]
        elif 0xE000 <= address <= 0xFFFF and self._hiram:
            lo, hi = self.roms['kernal'][address - 0xE000: address - 0xE000 + 2]
        else:
            lo, hi = self.ram[address: address + 2]
        return hi * 256 + lo

    def dump(self, start: int = None, end: int = None, as_chars: bool = False) -> str:
        """
        Return a textual representation of memory from start to end
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
        step = 0x28 if as_chars else 0x10

        out = ""
        for row in range(start, end, step):
            data = [self.cpu_read(i) for i in range(start, end)]
            data_hex = [f"{'' if i % 4 else ' '}{byte:02X} " for i, byte in enumerate(data)]
            data_char = map(lambda x: SCREEN_CHARCODE.get(x, "."), data)

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
        instruction, mode, _ = OPCODES[self[address]]

        # Skip data bytes (or invalid opcodes)
        instruction = instruction or "???"

        if mode == "addressing_IMP":
            arg = ""
            step = 1
        elif mode == "addressing_ABS":
            arg = f"${self[address + 2]:02X}{self[address + 1]:02X}"
            step = 3
        elif mode == "addressing_ABS_X":
            arg = f"${self[address + 2]:02X}{self[address + 1]:02X},X"
            step = 3
        elif mode == "addressing_ABS_Y":
            arg = f"${self[address + 2]:02X}{self[address + 1]:02X},Y"
            step = 3
        elif mode == "addressing_REL":
            delta = self[address + 1]
            arg = f"${(address + delta + 2 if delta < 127 else address + delta - 254):04X}"
            step = 2
        elif mode == "addressing_IMM":
            arg = f"#${self[address + 1]:02X}"
            step = 2
        elif mode == "addressing_ZP":
            arg = f"${self[address + 1]:02X}"
            step = 2
        elif mode == "addressing_ZP_X":
            arg = f"${self[address + 1]:02X},X"
            step = 2
        elif mode == "addressing_ZP_Y":
            arg = f"${self[address + 1]:02X},Y"
            step = 2
        elif mode == "addressing_IND":
            arg = f"(${self[address + 2]:02X}{self[address + 1]:02X})"
            step = 3
        elif mode == "addressing_X_IND":
            arg = f"$({self[address + 1]:02X},X)"
            step = 2
        elif mode == "addressing_IND_Y":
            arg = f"(${self[address + 1]:02X}),Y"
            step = 2
        else:
            # Skip invalid addressing mode
            arg = ""
            step = 1
        # Compose line
        output += f"{' '.join([f'{self[_]:02X}' for _ in range(address, address + step)])}" \
                  f"{'   ' * (4 - step)}{instruction} {arg}"
        address = (address + step) & 0xFFFF

        return output, step


class BytearrayMemory(Memory, bytearray):
    """
    A memory class where data is stored into a bytearray
    """

    def __init__(self, size: int, roms=None):
        super().__init__(size)
        if roms is not None:
            self.roms = roms.contents
