from .constants import BITRANGE, OPCODES


# noinspection PyPep8Naming
class CPU:
    # noinspection PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming
    memory = None
    A = 0x00
    X = 0x00
    Y = 0x00
    PC = 0x0000
    SP = 0xFF
    F = {
        "N": False,
        "V": False,
        "-": True,
        "B": False,
        "D": False,
        "I": True,
        "Z": False,
        "C": False,
    }

    def __init__(
        self,
        memory,
        A: int = 0,
        X: int = 0,
        Y: int = 0,
        PC: int = 0x0000,
        SP: int = 0xFF,
    ):
        self.memory = memory

        self.indent = 0
        self._debug = False

        self.addressing_methods = {
            name: getattr(self, name)
            for name in dir(self)
            if name.startswith("addressing")
        }

        self._cycles_left = 0

    def __str__(self):
        st = "".join(symbol if flag else "." for symbol, flag in self.F.items())
        assembly, _ = self.memory.disassemble(self.PC)
        return (
            f"{self.PC:04X}  "
            f"{assembly}{' ' * (24 - len(assembly))} - "
            f"A:{self.A:02X} X:{self.X:02X} Y:{self.Y:02X} SP:{self.SP:02X} {st}"
        )

    def push(self, value):
        """
        Push a value on the stack, update SP
        :param value: The value to push
        :return: None
        """
        # Stack memory is at page 1 (0x100)
        self.memory.cpu_write(0x100 | self.SP, value)
        self.SP = (self.SP - 1) & 0xFF

    def pop(self):
        """
        Pop a value from the stack, update SP
        :return: The popped value
        """
        # Stack memory is at page 1 (0x100)
        self.SP = (self.SP + 1) & 0xFF
        return self.memory.cpu_read(0x100 | self.SP)

    def fetch(self):
        """
        Fetch next istruction (memory read at PC, advance PC)
        :return: None
        """
        opcode = self.memory.cpu_read(self.PC)
        # print(f"Fetched at {self.PC:04X}: {self.opcodes[opcode]}")
        self.PC += 1
        return opcode

    def clock(self) -> None:
        """
        Execute next instruction
        """
        if self._cycles_left > 0:
            # Still working on last instruction
            self._cycles_left -= 1
            return

        opcode = self.fetch()
        instruction, mode, self._cycles_left = OPCODES[opcode]
        try:
            # if instruction is None:
            #    raise ValueError(f"Opcode {opcode:02X} not implemented at {pc}")
            address = self.addressing_methods[mode]()
        except Exception as e:
            print(f"ERROR at ${self.PC:04X}, {instruction} {mode}: {e}")
        else:
            try:
                getattr(self, instruction)(address)
            except Exception as e:
                print(
                    f"ERROR at ${self.PC:04X}, {instruction} {mode} {address:04X}: {e}"
                )
                raise e

    def irq(self):
        """
        Handle IRQ
        """
        if not self.F["I"]:
            self.F["I"] = True  # Do ignore other IRQ while serving. Re-enable after RTI
            self.save_state()
            self.PC = self.memory.read_address(0xFFFE)

    def nmi(self):
        """
        Handle NMI
        """
        self.save_state()
        self.PC = self.memory.read_address(0xFFFA)

    # Utils
    def setNZ(self, value):
        """
        Set N and Z status flags according to value
        :param value:
        :return: None
        """
        self.F["N"] = value >= 0x80 or value < 0
        self.F["Z"] = value == 0

    @staticmethod
    def make_address(low, high):
        """
        Returns a 16 bit value by combining low and high bytes LITTLE ENDIAN
        :param low: The low byte
        :param high: The high byte
        :return: 2-byte value
        """
        return high << 8 | low

    def pack_status_register(self):
        result = 0
        for i, flag in enumerate(self.F.values()):
            result += BITRANGE[i][1] * flag
        return result

    def unpack_status_register(self, value):
        result = {}
        for i, flag in enumerate(self.F.keys()):
            result[flag] = bool(value & BITRANGE[i][1])
        return result

    def save_state(self):
        """
        Save processor status before IRQ or NMI
        """
        self.push(self.PC >> 8)
        self.push(self.PC & 0xFF)
        self.push(self.pack_status_register())

    # region Addressing methods
    @staticmethod
    def addressing_IMP():
        # The data is implied by the operation.
        return None

    def addressing_IMM(self):
        # Data is taken from the byte following the opcode.
        address = self.PC
        self.PC += 1
        return address

    def addressing_REL(self):
        # An 8-bit signed offset is provided. This value is added to the program counter (PC) to find the effective
        # address.
        address = self.memory.cpu_read(self.PC)
        self.PC += 1
        return address if address < 127 else address - 256

    def addressing_ABS(self):
        # Data is accessed using 16-bit address specified as a constant.
        address = self.memory.read_address(self.PC)
        self.PC += 2
        return address

    def addressing_ZP(self):
        # An 8-bit address is provided within the zero page.
        address = self.memory.cpu_read(self.PC)
        self.PC += 1
        return address

    def addressing_ABS_X(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the X register is
        # added (with carry).
        address = self.memory.read_address(self.PC)
        self.PC += 2
        return address + self.X

    def addressing_ABS_Y(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the Y register is
        # added (with carry).
        address = self.memory.read_address(self.PC)
        self.PC += 2
        return address + self.Y

    def addressing_ZP_X(self):
        # An 8-bit address is provided, to which the X register is added (without carry - if the addition overflows,
        # the address wraps around within the zero page).
        base_address = self.memory.cpu_read(self.PC)
        self.PC += 1
        return (base_address + self.X) & 0xFF

    def addressing_ZP_Y(self):
        # An 8-bit address is provided, to which the Y register is added (without carry - if the addition overflows,
        # the address wraps around within the zero page).
        base_address = self.memory.cpu_read(self.PC)
        self.PC += 1
        return (base_address + self.Y) & 0xFF

    def addressing_IND(self):
        # Data is accessed using a pointer. The 16-bit address of the pointer is given in the two bytes following the
        # opcode.
        # Note: replicate bug when address is on page boundary
        lo, hi = (
            self.memory.cpu_read(self.PC),
            (
                self.memory.cpu_read(self.PC + 1)
                if self.PC & 0xFF != 0xFF
                else self.memory.cpu_read(self.PC & 0xFF00)
            ),
        )
        self.PC += 2
        address = self.make_address(lo, hi)
        return self.memory.read_address(address)

    def addressing_X_IND(self):
        # An 8-bit zero-page address and the X register are added, without carry (if the addition overflows,
        # the address wraps around within page 0). The resulting address is used as a pointer to the data being
        # accessed.
        base = self.memory.cpu_read(self.PC) + self.X
        self.PC += 1
        return self.memory.read_address(self.memory.cpu_read(base))

    def addressing_IND_Y(self):
        base = self.memory.cpu_read(self.PC)
        self.PC += 1
        return self.memory.read_address(base) + self.Y

    # endregion

    # region Instructions
    def ADC(self, address):
        result = self.A + self.memory.cpu_read(address) + self.F["C"]
        self.setNZ(result & 0xFF)
        self.F["C"] = result > 0xFF
        # Thanks https://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
        self.F["V"] = bool(
            (self.A ^ result) & (self.memory.cpu_read(address) ^ result) & 0x80
        )
        self.A = result & 0xFF

    def AND(self, address):
        result = self.A & self.memory.cpu_read(address)
        self.setNZ(result)
        self.A = result

    def ASL(self, address):
        value = self.A if address is None else self.memory.cpu_read(address)
        self.F["C"] = value >= 0x80
        result = (value << 1) & 0xFF
        self.setNZ(result)
        if address is None:
            self.A = result
        else:
            self.memory.cpu_write(address, result)

    def BRK(self, address):
        self.F["B"] = True

    def BPL(self, address):
        if not self.F["N"]:
            self.PC += address

    def BMI(self, address):
        if self.F["N"]:
            self.PC += address

    def BVC(self, address):
        if not self.F["V"]:
            self.PC += address

    def BVS(self, address):
        if self.F["V"]:
            self.PC += address

    def BCC(self, address):
        if not self.F["C"]:
            self.PC += address

    def BCS(self, address):
        if self.F["C"]:
            self.PC += address

    def BNE(self, address):
        if not self.F["Z"]:
            self.PC += address

    def BEQ(self, address):
        if self.F["Z"]:
            self.PC += address

    def BIT(self, address):
        value = self.memory.cpu_read(address)
        self.setNZ(value & self.A)
        self.F["N"] = value >= 0x80
        self.F["V"] = bool(value & 0x40)

    def CLC(self, address):
        self.F["C"] = False

    def CLD(self, address):
        self.F["D"] = False

    def CLI(self, address):
        self.F["I"] = False

    def CLV(self, address):
        self.F["V"] = False

    def CMP(self, address):
        result = self.A - self.memory.cpu_read(address)
        self.F["C"] = result >= 0
        if result < 0:
            result += 255
        self.setNZ(result)

    def CPX(self, address):
        result = self.X - self.memory.cpu_read(address)
        self.F["C"] = result >= 0
        if result < 0:
            result += 255
        self.setNZ(result)

    def CPY(self, address):
        result = self.Y - self.memory.cpu_read(address)
        self.F["C"] = result >= 0
        if result < 0:
            result += 255
        self.setNZ(result)

    def DEC(self, address):
        result = (self.memory.cpu_read(address) - 1) & 0xFF
        self.memory.cpu_write(address, result)
        self.setNZ(result)

    def DEX(self, address):
        self.X = (self.X - 1) & 0xFF
        self.setNZ(self.X)

    def DEY(self, address):
        self.Y = (self.Y - 1) & 0xFF
        self.setNZ(self.Y)

    def EOR(self, address):
        result = self.A ^ self.memory.cpu_read(address)
        self.setNZ(result)
        self.A = result

    def INC(self, address):
        value = (self.memory.cpu_read(address) + 1) & 0xFF
        self.memory.cpu_write(address, value)
        self.setNZ(value)

    def INX(self, address):
        self.X = (self.X + 1) & 0xFF
        self.setNZ(self.X)

    def INY(self, address):
        self.Y = (self.Y + 1) & 0xFF
        self.setNZ(self.Y)

    def JMP(self, address):
        self.PC = address

    def JSR(self, address):
        value = self.PC - 1
        self.push((value & 0xFF00) >> 8)  # save high byte of PC
        self.push(value & 0x00FF)  # save low byte of PC
        self.PC = address
        self.indent += 1

    def LDA(self, address):
        self.A = self.memory.cpu_read(address)
        self.setNZ(self.A)

    def LDX(self, address):
        self.X = self.memory.cpu_read(address)
        self.setNZ(self.X)

    def LDY(self, address):
        self.Y = self.memory.cpu_read(address)
        self.setNZ(self.Y)

    def LSR(self, address):
        value = self.A if address is None else self.memory.cpu_read(address)
        self.F["C"] = value & 0x01
        result = value >> 1
        self.setNZ(result)
        if address is None:
            self.A = result
        else:
            self.memory.cpu_write(address, result)

    def NOP(self, address):
        pass

    def ORA(self, address):
        result = self.A | self.memory.cpu_read(address)
        self.setNZ(result)
        self.A = result

    def PHA(self, address):
        self.push(self.A)

    def PHP(self, address):
        self.push(self.pack_status_register())

    def PLA(self, address):
        self.A = self.pop()
        self.setNZ(self.A)

    def PLP(self, address):
        self.F = self.unpack_status_register(self.pop())

    def ROL(self, address):
        value = self.A if address is None else self.memory.cpu_read(address)
        _carrytemp = value >= 0x80
        result = ((value << 1) | self.F["C"]) & 0xFF
        self.setNZ(result)
        self.F["C"] = _carrytemp
        if address is None:
            self.A = result
        else:
            self.memory.cpu_write(address, result)

    def ROR(self, address):
        value = self.A if address is None else self.memory.cpu_read(address)
        _carrytemp = value & 0x01
        result = ((value >> 1) | self.F["C"] << 7) & 0xFF
        self.setNZ(result)
        self.F["C"] = _carrytemp
        if address is None:
            self.A = result
        else:
            self.memory.cpu_write(address, result)

    def RTI(self, Address):
        # TODO: untested
        self.F = self.unpack_status_register(self.pop())
        value = self.pop() + (self.pop() << 8)
        self.PC = value
        self.F["I"] = False  # Re-enable interrupts after serving

    def RTS(self, address):
        value = self.pop() + (self.pop() << 8)
        self.PC = value + 1
        self.indent -= 1

    def SBC(self, address):
        result = self.A - self.memory.cpu_read(address) - (1 - self.F["C"])
        self.setNZ(result & 0xFF)
        self.F["C"] = result >= 0x00
        # Thanks https://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
        self.F["V"] = bool(
            (self.A ^ result) & ((0xFF - self.memory.cpu_read(address)) ^ result) & 0x80
        )
        self.A = result & 0xFF

    def SEC(self, address):
        self.F["C"] = True

    def SED(self, address):
        self.F["D"] = True

    def SEI(self, address):
        self.F["I"] = True

    def STA(self, address):
        self.memory.cpu_write(address, self.A)

    def STX(self, address):
        self.memory.cpu_write(address, self.X)

    def STY(self, address):
        self.memory.cpu_write(address, self.Y)

    def TAX(self, address):
        self.X = self.A
        self.setNZ(self.A)

    def TAY(self, address):
        self.Y = self.A
        self.setNZ(self.A)

    def TSX(self, adrress):
        self.X = self.SP
        self.setNZ(self.X)

    def TXA(self, address):
        self.A = self.X
        self.setNZ(self.X)

    def TXS(self, address):
        self.SP = self.X

    def TYA(self, address):
        self.A = self.Y
        self.setNZ(self.Y)

    # endregion
