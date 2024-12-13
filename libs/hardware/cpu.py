import logging

from config import TRACE_EXEC

from .constants import BITVALUES, OPCODES


# noinspection PyPep8Naming
class CPU:
    __slots__ = [
        "A",
        "X",
        "Y",
        "PC",
        "SP",
        "flag_N",
        "flag_V",
        "flag_B",
        "flag_D",
        "flag_I",
        "flag_Z",
        "flag_C",
        "memory",
        "bus",
        "addressing_methods",
        "indent",
        "_debug",
        "_cycles_left",
        "_fetching",
        "_instruction",
        "_mode",
    ]

    def __init__(
        self,
        memory,
        bus,
        A: int = 0,
        X: int = 0,
        Y: int = 0,
        PC: int = 0x0000,
        SP: int = 0xFF,
        SR: int = 0b00100100,
    ):
        self.memory = memory
        self.bus = bus

        self.A = A
        self.X = X
        self.Y = Y
        self.PC = PC
        self.SP = SP
        self.unpack_status_register(SR)

        self.indent = 0
        self._debug = False

        self.addressing_methods = {
            "addressing_IMP": self.addressing_IMP,
            "addressing_IMM": self.addressing_IMM,
            "addressing_REL": self.addressing_REL,
            "addressing_ABS": self.addressing_ABS,
            "addressing_ZP": self.addressing_ZP,
            "addressing_ABS_X": self.addressing_ABS_X,
            "addressing_ABS_Y": self.addressing_ABS_Y,
            "addressing_ZP_X": self.addressing_ZP_X,
            "addressing_ZP_Y": self.addressing_ZP_Y,
            "addressing_IND": self.addressing_IND,
            "addressing_X_IND": self.addressing_X_IND,
            "addressing_IND_Y": self.addressing_IND_Y,
        }

        self._fetching = True
        self._cycles_left = 0
        self._instruction = ""

    def __str__(self):
        st = "".join(
            symbol if flag else "."
            for symbol, flag in zip(
                "NV-BDIZC",
                [
                    self.flag_N,
                    self.flag_V,
                    True,
                    self.flag_B,
                    self.flag_D,
                    self.flag_I,
                    self.flag_Z,
                    self.flag_C,
                ],
            )
        )
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
        self.memory[0x100 + self.SP] = value
        self.SP = (self.SP - 1) & 0xFF

    def pop(self):
        """
        Pop a value from the stack, update SP
        :return: The popped value
        """
        # Stack memory is at page 1 (0x100)
        self.SP = (self.SP + 1) & 0xFF
        return self.memory[0x100 + self.SP]

    @staticmethod
    def binary_to_decimal(value):
        hi, lo = value // 0x10, value & 0x0F
        return hi * 10 + lo

    @staticmethod
    def decimal_to_binary(value):
        hi, lo = value // 10, value % 10
        return hi * 16 + lo

    def clock(self) -> bool:
        """
        Fetch next instruction or continue executing current
        Return True when an instruction is fully executed
        and CPU is ready to fetch a new one
        """
        if self._cycles_left > 0:
            # Still working on last instruction
            self._cycles_left -= 1
            return self._cycles_left == 0 and self._fetching

        if self._fetching:
            # Handle nmi if any occured
            if self.bus.nmi:
                self.nmi()
                return False

            # Handle irq if any occured
            elif self.bus.irq and not self.flag_I:
                self.irq()
                return False

            # Fetch
            opcode = self.memory.cpu_read(self.PC)
            # Decode
            self._instruction, self._mode, self._cycles_left, is_legal = OPCODES[opcode]
            self._cycles_left -= 2  # One for fetch, One pre-reserved for execute
            self._fetching = False
            if not is_legal:
                logging.debug(f"Illegal {self}")
            return False

        # Execute
        self.PC += 1
        address = self.addressing_methods[self._mode]()
        getattr(self, self._instruction)(address)
        self._fetching = True

        if self.PC in TRACE_EXEC:
            logging.debug(self)

        return self._cycles_left == 0

    def irq(self):
        """
        Handle IRQ
        """
        self.save_state()
        self.flag_I = True  # Do ignore other IRQ while serving. Re-enable after RTI
        self.PC = self.memory.read_address(0xFFFE)
        self._cycles_left += 7

    def nmi(self):
        """
        Handle NMI
        """
        self.save_state()
        self.PC = self.memory.read_address(0xFFFA)
        self._cycles_left += 7

    # Utils
    def setNZ(self, value):
        """
        Set N and Z status flags according to value
        :param value:
        :return: None
        """
        self.flag_N = value >= 0x80 or value < 0
        self.flag_Z = value == 0

    @staticmethod
    def make_address(low, high):
        """
        Returns a 16 bit value by combining low and high bytes LITTLE ENDIAN
        :param low: The low byte
        :param high: The high byte
        :return: 2-byte value
        """
        return high * 0x100 + low

    def pack_status_register(self):
        result = 0
        for i, flag in enumerate(
            [
                self.flag_C,
                self.flag_Z,
                self.flag_I,
                self.flag_D,
                self.flag_B,
                True,
                self.flag_V,
                self.flag_N,
            ]
        ):
            result += BITVALUES[i] * flag
        return result

    def unpack_status_register(self, value):
        for i, flag in enumerate(
            [
                "flag_C",
                "flag_Z",
                "flag_I",
                "flag_D",
                "flag_B",
                None,
                "flag_V",
                "flag_N",
            ]
        ):
            if flag is not None:
                setattr(self, flag, bool(value & BITVALUES[i]))

    def save_state(self):
        """
        Save processor status before IRQ or NMI
        """
        self.push(self.PC // 0x100)
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
        address = self.memory.read_address(self.PC) + self.X
        if address > 0xFFFF:
            logging.warning(f"ABS,X overflow @ ${self.PC-1:0x4}")
            address &= 0xFFFF
        self.PC += 2
        return address

    def addressing_ABS_Y(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the Y register is
        # added (with carry).
        address = self.memory.read_address(self.PC) + self.Y
        if address > 0xFFFF:
            logging.warning("ABS,Y overflow @ ${self.PC-1:0x4}")
            address &= 0xFFFF
        self.PC += 2
        return address

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
        base = (self.memory.cpu_read(self.PC) + self.X) & 0xFF
        self.PC += 1
        return self.memory.read_address_zp(base)

    def addressing_IND_Y(self):
        base = self.memory.cpu_read(self.PC)
        self.PC += 1
        return self.memory.read_address(base) + self.Y

    # endregion

    # region Legal Instructions
    def ADC(self, address):
        value = self.memory.cpu_read(address)
        if self.flag_D:
            A = self.binary_to_decimal(self.A)
            value = self.binary_to_decimal(value)
            result = A + value + self.flag_C
            self.setNZ(result & 0xFF)  # ?
            self.flag_C = result > 99
            self.flag_V = bool((self.A ^ result) & (value ^ result) & 0x80)  # ???
            result = self.decimal_to_binary(result % 100)
        else:
            result = self.A + value + self.flag_C
            self.setNZ(result & 0xFF)
            self.flag_C = result > 0xFF
            # Thanks https://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
            self.flag_V = bool((self.A ^ result) & (value ^ result) & 0x80)
        self.A = result & 0xFF

    def AND(self, address):
        result = self.A & self.memory.cpu_read(address)
        self.setNZ(result)
        self.A = result

    def ASL(self, address):
        value = self.A if address is None else self.memory.cpu_read(address)
        self.flag_C = value >= 0x80
        result = (value * 2) & 0xFF
        self.setNZ(result)
        if address is None:
            self.A = result
        else:
            self.memory.cpu_write(address, 0xFF)  # Obscure CPU internal on RMW ops
            self.memory.cpu_write(address, result)

    def BRK(self, address):
        self.flag_B = True

    def BPL(self, address):
        if not self.flag_N:
            self._cycles_left += 1
            self.PC += address

    def BMI(self, address):
        if self.flag_N:
            self._cycles_left += 1
            self.PC += address

    def BVC(self, address):
        if not self.flag_V:
            self._cycles_left += 1
            self.PC += address

    def BVS(self, address):
        if self.flag_V:
            self._cycles_left += 1
            self.PC += address

    def BCC(self, address):
        if not self.flag_C:
            self._cycles_left += 1
            self.PC += address

    def BCS(self, address):
        if self.flag_C:
            self._cycles_left += 1
            self.PC += address

    def BNE(self, address):
        if not self.flag_Z:
            self._cycles_left += 1
            self.PC += address

    def BEQ(self, address):
        if self.flag_Z:
            self._cycles_left += 1
            self.PC += address

    def BIT(self, address):
        value = self.memory.cpu_read(address)
        self.setNZ(value & self.A)
        self.flag_N = value >= 0x80
        self.flag_V = bool(value & 0x40)

    def CLC(self, address):
        self.flag_C = False

    def CLD(self, address):
        self.flag_D = False

    def CLI(self, address):
        self.flag_I = False

    def CLV(self, address):
        self.flag_V = False

    def CMP(self, address):
        result = self.A - self.memory.cpu_read(address)
        self.flag_C = result >= 0
        result &= 0xFF
        self.setNZ(result)

    def CPX(self, address):
        result = self.X - self.memory.cpu_read(address)
        self.flag_C = result >= 0
        result &= 0xFF
        self.setNZ(result)

    def CPY(self, address):
        result = self.Y - self.memory.cpu_read(address)
        self.flag_C = result >= 0
        result &= 0xFF
        self.setNZ(result)

    def DEC(self, address):
        result = (self.memory.cpu_read(address) - 1) & 0xFF
        self.memory.cpu_write(address, 0xFF)  # Obscure CPU internal on RMW ops
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
        self.memory.cpu_write(address, 0xFF)  # Obscure CPU internal on RMW ops
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
        self.push((value & 0xFF00) // 0x100)  # save high byte of PC
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
        self.flag_C = bool(value & 0x01)
        result = value // 2
        self.setNZ(result)
        if address is None:
            self.A = result
        else:
            self.memory.cpu_write(address, 0xFF)  # Obscure CPU internal on RMW ops
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
        self.unpack_status_register(self.pop())

    def ROL(self, address):
        value = self.A if address is None else self.memory.cpu_read(address)
        _carrytemp = value >= 0x80
        result = ((value * 2) + self.flag_C) & 0xFF
        self.setNZ(result)
        self.flag_C = _carrytemp
        if address is None:
            self.A = result
        else:
            self.memory.cpu_write(address, 0xFF)  # Obscure CPU internal on RMW ops
            self.memory.cpu_write(address, result)

    def ROR(self, address):
        value = self.A if address is None else self.memory.cpu_read(address)
        _carrytemp = value & 0x01
        result = ((value // 2) + self.flag_C * 0x80) & 0xFF
        self.setNZ(result)
        self.flag_C = _carrytemp
        if address is None:
            self.A = result
        else:
            self.memory.cpu_write(address, 0xFF)  # Obscure CPU internal on RMW ops
            self.memory.cpu_write(address, result)

    def RTI(self, Address):
        self.unpack_status_register(self.pop())
        self.PC = self.make_address(self.pop(), self.pop())

    def RTS(self, address):
        value = self.make_address(self.pop(), self.pop())
        self.PC = value + 1
        self.indent -= 1

    def SBC(self, address):
        value = self.memory.cpu_read(address)
        if self.flag_D:
            A = self.binary_to_decimal(self.A)
            value = self.binary_to_decimal(value)
            result = A - value - (1 - self.flag_C)
            self.setNZ(result & 0xFF)
            self.flag_C = result > 0x00
            # Thanks https://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
            self.flag_V = bool((self.A ^ result) & ((0xFF - value) ^ result) & 0x80)
            result = self.decimal_to_binary(result % 100)
        else:
            result = self.A - value - (1 - self.flag_C)
            self.setNZ(result & 0xFF)
            self.flag_C = result >= 0x00
            # Thanks https://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
            self.flag_V = bool((self.A ^ result) & ((0xFF - value) ^ result) & 0x80)
        self.A = result & 0xFF

    def SEC(self, address):
        self.flag_C = True

    def SED(self, address):
        self.flag_D = True

    def SEI(self, address):
        self.flag_I = True

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

    # region Illegal Instructions

    def JAM(self, address):
        logging.warning(f"Got JAM @ ${self.PC-1:04X}")

    def ALR(self, address):
        # AND oper + LSR
        # A AND oper, 0 -> [76543210] -> C
        value = self.A & self.memory.cpu_read(address)
        self.flag_C = bool(value & 0x01)
        result = value // 2
        self.setNZ(result)
        self.A = result

    def ANC(self, address):
        # AND oper + set C as ASL
        # A AND oper, bit(7) -> C
        result = self.A & self.memory.cpu_read(address)
        self.setNZ(result)
        self.A = result
        self.flag_C = bool(result & 0x80)

    def ANE(self, address):
        # (A OR CONST) AND X AND oper -> A
        # TODO
        pass

    def ARR(self, address):
        # AND oper + ROR
        result = (self.A & self.memory.cpu_read(address)) // 2
        # C is bit 6
        self.flag_C = result & 0x40
        # V is bit 6 xor bit 5
        self.flag_V = (result & 0x40) ^ (result & 0x20)
        self.setNZ(result)
        self.A = result

    def DCP(self, address):
        # DEC oper + CMP oper
        # M - 1 -> M, A - M
        result = (self.memory.cpu_read(address) - 1) & 0xFF
        self.memory.cpu_write(address, 0xFF)  # Obscure CPU internal on RMW ops
        self.memory.cpu_write(address, result)
        result = self.A - result
        self.flag_C = result >= 0
        result &= 0xFF
        self.setNZ(result)

    def ISC(self, address):
        # INC oper + SBC oper
        # M + 1 -> M, A - M - C -> A
        value = (self.memory.cpu_read(address) + 1) & 0xFF
        self.memory.cpu_write(address, 0xFF)  # Obscure CPU internal on RMW ops
        self.memory.cpu_write(address, value)
        # TODO BCD mode
        result = self.A - value - (1 - self.flag_C)
        self.setNZ(result & 0xFF)
        self.flag_C = result >= 0x00
        self.flag_V = bool((self.A ^ result) & ((0xFF - value) ^ result) & 0x80)
        self.A = result & 0xFF

    def LAS(self, address):
        # LDA/TSX oper
        # M AND SP -> A, X, SP
        value = self.memory.cpu_read(address) & self.SP
        self.A = self.X = self.SP = value
        self.setNZ(value)

    def LAX(self, address):
        # LDA oper + LDX oper
        # M -> A -> X
        self.A = self.memory.cpu_read(address)
        self.X = self.A
        self.setNZ(self.A)

    def LXA(self, address):
        # (A OR CONST) AND X AND oper -> A
        # TODO
        pass

    def RLA(self, address):
        # ROL oper + AND oper
        # M = C <- [76543210] <- C, A AND M -> A
        value = self.memory.cpu_read(address)
        _carrytemp = value >= 0x80
        result = ((value * 2) + self.flag_C) & 0xFF
        self.flag_C = _carrytemp
        self.memory.cpu_write(address, result)
        self.A &= result
        self.setNZ(self.A)

    def RRA(self, address):
        # ROR oper + ADC oper
        # M = C -> [76543210] -> C, A + M + C -> A, C
        # TODO: BCD mode
        value = self.memory.cpu_read(address)
        _carrytemp = value & 0x01
        result = ((value // 2) + self.flag_C * 0x80) & 0xFF
        self.memory.cpu_write(address, result)

        result = result + self.A + self.flag_C
        self.setNZ(result & 0xFF)
        self.flag_C = result > 0xFF
        self.flag_V = bool((self.A ^ result) & (value ^ result) & 0x80)
        self.A = result & 0xFF

    def SAX(self, address):
        # A and X are put on the bus at the same time
        # (resulting effectively in an AND operation) and stored in M
        # A AND X -> M
        self.memory.cpu_write(address, self.A and self.X)

    def SHA(self, address):
        # Stores A AND X AND (high-byte of addr. + 1) at addr
        # high_byte = address // 0x100
        # TODO (get original operand...)
        pass

    def SHX(self, address):
        # Stores X AND (high-byte of addr. + 1) at addr.
        # high_byte = address // 0x100
        # TODO (get original operand...)
        pass

    def SHY(self, address):
        # Stores Y AND X AND (high-byte of addr. + 1) at addr
        # high_byte = address // 0x100
        # TODO (get original operand...)
        pass

    def SLO(self, address):
        # ASL oper + ORA oper
        # M = C <- [76543210] <- 0, A OR M -> A
        value = self.memory.cpu_read(address)
        self.flag_C = value >= 0x80
        result = (value * 2) & 0xFF
        self.A |= result
        self.setNZ(self.A)

    def SRE(self, address):
        # LSR oper + EOR oper
        # M = 0 -> [76543210] -> C, A EOR M -> A
        value = self.memory.cpu_read(address)
        self.flag_C = bool(value & 0x01)
        result = value // 2
        self.memory.cpu_write(address, result)
        self.A = self.A ^ result
        self.setNZ(self.A)

    def SBX(self, address):
        # CMP and DEX at once, sets flags like CMP
        # (A AND X) - oper -> X
        result = (self.A & self.X) - self.memory.cpu_read(address)
        self.flag_C = result >= 0
        result &= 0xFF
        self.setNZ(result)
        self.X = result

    def TAS(self, address):
        # Puts A AND X in SP and stores A AND X AND (high-byte of addr. + 1) at addr.
        # TODO
        pass

    def USBC(self, address):
        # (A OR CONST) AND X AND oper -> A
        # same as SBC
        pass

    # endregion
