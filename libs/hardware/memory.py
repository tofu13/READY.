from typing import Optional

from libs.hardware.constants import OPCODES, SCREEN_CHARCODE


class Memory:
    __slots__ = [
        "ram",
        "ram_color",
        "rom_basic",
        "rom_kernal",
        "rom_chargen",
        "read_watchers",
        "write_watchers",
        "io_port",
        "loram_port",
        "hiram_port",
        "vic_memory_bank",
        "_any_ram",
    ]

    def __init__(self, ram=None, roms=None):
        """
        Memory class that implements PLA for routing reads and write
        to/from RAM, ROMS, I/O, including color ram
        """
        self.ram = ram if ram is not None else bytearray(65536)
        self.ram_color: bytearray = bytearray(1024)
        if roms is None:
            self.rom_basic = None
            self.rom_kernal = None
            self.rom_chargen = None
        else:
            self.rom_basic = roms.contents["basic"]
            self.rom_kernal = roms.contents["kernal"]
            self.rom_chargen = roms.contents["chargen"]

        self.read_watchers = []
        self.write_watchers = []

        # Internals
        self.io_port, self.loram_port, self.hiram_port = True, True, True
        self._any_ram: bool = True
        self.vic_memory_bank: int = 0x0000

    def __getitem__(self, item):
        return self.ram[item]

    def __setitem__(self, key, value):
        self.ram[key] = value

    def cpu_read(self, address: int | slice) -> int:
        """Return memory content (RAM, ROM, I/O) as seen by the cpu"""
        if address < 0xA000:  # Maybe helps, maybe not
            value = self.ram[address]
        elif 0xA000 <= address <= 0xBFFF and self.hiram_port and self.loram_port:
            value = self.rom_basic[address - 0xA000]
        elif 0xE000 <= address and self.hiram_port:
            value = self.rom_kernal[address - 0xE000]
        elif 0xD800 <= address <= 0xDBFF and self.io_port and self._any_ram:
            value = self.ram_color[address - 0xD800]
        elif 0xD000 <= address <= 0xDFFF:
            if self.io_port and self._any_ram:
                # io_port on and RAM on -> I/O
                for start, end, callback in self.read_watchers:
                    if start <= address <= end:
                        value = callback(address)
                        break
                else:
                    # Unmapped I/O
                    value = 0x00
            elif self._any_ram:
                # io_port off with RAM on -> CHARGEN
                value = self.rom_chargen[address - 0xD000]
            else:
                # io_port ignored with all RAM off -> underlying RAM
                value = self.ram[address]
        else:
            # Actual RAM
            value = self.ram[address]
        return value

    def cpu_write(self, address: int, value: int):
        """Write into RAM or I/O depending on CPU ports"""
        # Hard coded processor port at $01
        if address == 0x01:
            # Set only writable bits in the processor port
            mask = self.ram[0x00]
            value = ((255 - mask) & self.ram[0x01]) | (mask & value)
            self.ram[0x01] = value
            # Update internal flags
            self.io_port, self.hiram_port, self.loram_port = map(
                bool, map(int, f"{value & 0x7:03b}")
            )
            # Cache any RAM flag
            self._any_ram = self.hiram_port or self.loram_port

        elif 0xD800 <= address <= 0xDBFF and self.io_port and self._any_ram:
            # Store only lower nibble to 4-bit color ram
            self.ram_color[address - 0xD800] = value & 0x0F

        elif 0xD000 <= address <= 0xDFFF and self.io_port and self._any_ram:
            for start, end, callback in self.write_watchers:
                if start <= address <= end:
                    callback(address, value)
                    break
                else:
                    # Writing to unmapped I/O
                    pass
        else:
            # Ok, time to really write into RAM
            self.ram[address] = value

    def set_vic_bank(self, bank_bits: int):
        # bank_bits is 2-bit selector from CIA_B register 0 bits #0 #1
        self.vic_memory_bank = (3 - bank_bits) << 14

    def vic_read(self, address: int) -> int:
        """Returns memory content as seen by VIC-II"""
        # memory_bank = 3 - (self[0xDD00] & 0b11) << 14

        # CHARGEN ROM is visible in banks 0 and 2 at $1000-1FFF
        if self.vic_memory_bank in {0x0000, 0x8000} and 0x1000 <= address < 0x2000:
            return self.rom_chargen[address - 0x1000]

        return self[self.vic_memory_bank + address]

    def read_address(self, address: int) -> int:
        """
        Optimized consecutive reads
        Return big endian word (16-bit address)
        """
        if 0xA000 <= address <= 0xBFFF and self._any_ram:
            lo, hi = self.rom_basic[address - 0xA000 : address - 0xA000 + 2]
        elif 0xE000 <= address and self.hiram_port:
            lo, hi = self.rom_kernal[address - 0xE000 : address - 0xE000 + 2]
        else:
            lo, hi = self.ram[address : address + 2]
        return hi * 256 + lo

    def read_address_zp(self, address: int) -> int:
        """
        Optimized consecutive reads at zeropage (with wraparound)
        Return big endian word (16-bit address)
        """
        lo, hi = self.ram[address], self.ram[(address + 1) & 0xFF]
        return hi * 256 + lo

    def dump(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        as_chars: bool = False,
    ) -> str:
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
        elif end is None:
            end = start + 0x0100
        step = 0x28 if as_chars else 0x10

        out = ""
        pointer = start
        for row in range(start, end, step):
            data = [self.cpu_read(i) for i in range(pointer, pointer + step)]
            data_hex = [
                f"{'' if i % 4 else ' '}{byte:02X} " for i, byte in enumerate(data)
            ]
            data_char = (SCREEN_CHARCODE.get(x, ".") for x in data)

            out += f"${row:04X}: "
            if as_chars:
                out += f"{''.join(data_char)}\n"
            else:
                out += f"{''.join(data_hex)}  {''.join(data_char)}\n"
            pointer += step
        return out

    def disassemble(self, address) -> tuple[str, int]:
        """
        Return disassembled memory
        :param address:
        :return:
        """
        output = ""
        instruction, mode, cycles, is_legal = OPCODES[self.cpu_read(address)]

        # Skip data bytes (or invalid opcodes)
        instruction = instruction or "???"

        match mode:
            case "addressing_IMP":
                arg = (
                    "A"
                    if instruction
                    in (
                        "ROL",
                        "ROR",
                        "ASL",
                        "LSR",
                    )
                    else ""
                )
                steps = 1
            case "addressing_ABS":
                arg = (
                    f"${self.cpu_read(address + 2):02X}{self.cpu_read(address + 1):02X}"
                )
                steps = 3
            case "addressing_ABS_X":
                arg = f"${self.cpu_read(address + 2):02X}{self.cpu_read(address + 1):02X},X"
                steps = 3
            case "addressing_ABS_Y":
                arg = f"${self.cpu_read(address + 2):02X}{self.cpu_read(address + 1):02X},Y"
                steps = 3
            case "addressing_REL":
                delta = self.cpu_read(address + 1)
                arg = f"${(address + delta + 2 if delta < 127 else address + delta - 254):04X}"
                steps = 2
            case "addressing_IMM":
                arg = f"#${self.cpu_read(address + 1):02X}"
                steps = 2
            case "addressing_ZP":
                arg = f"${self.cpu_read(address + 1):02X}"
                steps = 2
            case "addressing_ZP_X":
                arg = f"${self.cpu_read(address + 1):02X},X"
                steps = 2
            case "addressing_ZP_Y":
                arg = f"${self.cpu_read(address + 1):02X},Y"
                steps = 2
            case "addressing_IND":
                arg = f"(${self.cpu_read(address + 2):02X}{self.cpu_read(address + 1):02X})"
                steps = 3
            case "addressing_X_IND":
                arg = f"(${self.cpu_read(address + 1):02X},X)"
                steps = 2
            case "addressing_IND_Y":
                arg = f"(${self.cpu_read(address + 1):02X}),Y"
                steps = 2
            case _:
                # Skip invalid addressing mode
                arg = ""
                steps = 1
        # Compose line
        output += (
            f"{' '.join([f'{self.cpu_read(cell):02X}' for cell in range(address, address + steps)])}"
            f"{'   ' * (4 - steps)}{instruction} {arg}"
        )

        return output, steps
