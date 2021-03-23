from .constants import *
import asyncio


# noinspection PyPep8Naming
class CPU:
    # noinspection PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming
    memory = None

    def __init__(self, A=0, X=0, Y=0, PC=0x0000, SP=0xFF):
        self.A = A
        self.X = X
        self.Y = Y
        self.PC = PC
        self.SP = SP
        self.F = {'N': 0, 'V': 0, '-': 1, 'B': 0, 'D': 0, 'I': 1, 'Z': 0, 'C': 0}

        self._indent = 0
        self._debug = False
        self._breakpoints = set()

        for addressing in ADDRESSING_METHODS:
            if not hasattr(self, f"addressing_{addressing}"):
                setattr(self, f"addressing_{addressing}", self._not_implemented)

    def __str__(self):
        st = "".join(f"{k}:{v} " for k, v in self.F.items())
        return f"A: {self.A:02X} X: {self.X:02X} Y: {self.Y:02X} PC: {self.PC:04X} SP: {self.SP:02X} {st}"

    def push(self, value):
        """
        Push a value on the stack, update SP
        :param value: The value to push
        :return: None
        """
        # Stack memory is at page 1 (0x100)
        self.memory[0x100 | self.SP] = value
        self.SP = (self.SP - 1) & 0xFF

    def pop(self):
        """
        Pop a value from the stack, update SP
        :return: The popped value
        """
        # Stack memory is at page 1 (0x100)
        self.SP = (self.SP + 1) & 0xFF
        return self.memory[0x100 | self.SP]

    def fetch(self):
        """
        Fetch next istruction (memory read at PC, advance PC)
        :return: None
        """
        opcode = self.memory[self.PC]
        # print(f"Fetched at {self.PC:04X}: {self.opcodes[opcode]}")
        self.PC += 1
        return opcode

    def step(self):
        """
        Execute next instruction
        :return: False if instruction is BRK, else True
        """
        pc = self.PC
        opcode = self.fetch()
        instruction, mode = OPCODES[opcode]
        try:
            # if instruction is None:
            #    raise ValueError(f"Opcode {opcode:02X} not implemented at {pc}")
            address = getattr(self, f"addressing_{mode}")()
        except Exception as e:
            print(f"ERROR at ${self.PC:04X}, {instruction} {mode}: {e}")

        else:
            try:
                if self._debug:
                    print('\t' * self._indent + f"@${pc:04X} Executing {instruction}\t{mode}{' ' * (4 - len(mode))}",
                          end="")
                getattr(self, instruction)(address)
            except Exception as e:
                print(f"ERROR at ${self.PC:04X}, {instruction} {mode} {address:04X}: {e}")
            else:
                if self._debug:
                    print(f"\t{self}")

    async def run(self, queue, address=None):
        """
        Run from address (or PC if not specified) until BRK
        :param address: address to start execution
        :return: None
        """
        self.F['B'] = 0
        if address is not None:
            self.PC = address
        while not self.F['B'] and self.PC not in self._breakpoints:
            self.step()
            await asyncio.sleep(0)
            if not queue.empty():
                event = await queue.get()
                if event == 'IRQ':
                    self.irq()
                elif event == 'NMI':
                    pass
        print(f"BRK encountered at ${self.PC:04X}")

    def sys(self, address):
        """
        Emulate SYS
        :param address: addres to JSR to
        :return: None
        """
        sp = self.SP
        self.JSR(address)
        while not sp == self.SP or not self.F['B']:
            self.step()

    def irq(self):
        if not self.F['I']:
            # print(f"Serving IRQ - PC={self.PC:04X})")
            self.push(self.PC >> 8)
            self.push(self.PC & 0XFF)
            self.push(self._pack_status_register(self.F))
            self.PC = self._combine(self.memory[0xFFFE], self.memory[0xFFFF])

    # Utils
    def _setNZ(self, value):
        """
        Set N and Z status flags according to value
        :param value:
        :return: None
        """
        self.F['N'] = (value & 0xFF) >> 7
        self.F['Z'] = int(value == 0)

    @staticmethod
    def _combine(low, high):
        """
        Returns a 16 bit value by combining low and high bytes LITTLE ENDIAN
        :param low: The low byte
        :param high: The high byte
        :return: 2-byte value
        """
        return high << 8 | low

    @staticmethod
    def _pack_status_register(value):
        result = 0
        for i, flag in enumerate(value.values()):
            result |= 2 ** (7 - i) * flag
        return result

    def _unpack_status_register(self, value):
        result = dict()
        for i, flag in enumerate(self.F.keys()):
            result[flag] = (value & 2 ** (7 - i)) >> (7 - i)
        return result

    def _not_implemented(self, address):
        raise NotImplementedError

    # Addressing methods
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
        address = self.memory[self.PC]
        self.PC += 1
        return address if address < 127 else address - 256

    def addressing_ABS(self):
        # Data is accessed using 16-bit address specified as a constant.
        l, h = self.memory[self.PC], self.memory[self.PC + 1]
        self.PC += 2
        return self._combine(l, h)

    def addressing_ZP(self):
        # An 8-bit address is provided within the zero page.
        address = self.memory[self.PC]
        self.PC += 1
        return address

    def addressing_ABS_X(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the X register is 
        # added (with carry). 
        l, h = self.memory[self.PC], self.memory[self.PC + 1]
        self.PC += 2
        return self._combine(l, h) + self.X

    def addressing_ABS_Y(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the Y register is 
        # added (with carry). 
        l, h = self.memory[self.PC], self.memory[self.PC + 1]
        self.PC += 2
        return self._combine(l, h) + self.Y

    def addressing_ZP_X(self):
        # An 8-bit address is provided, to which the X register is added (without carry - if the addition overflows, 
        # the address wraps around within the zero page). 
        base_address = self.memory[self.PC]
        self.PC += 1
        return (base_address + self.X) & 0xFF

    def addressing_ZP_Y(self):
        # An 8-bit address is provided, to which the Y register is added (without carry - if the addition overflows, 
        # the address wraps around within the zero page). 
        base_address = self.memory[self.PC]
        self.PC += 1
        return (base_address + self.Y) & 0xFF

    def addressing_IND(self):
        # Data is accessed using a pointer. The 16-bit address of the pointer is given in the two bytes following the
        # opcode. 
        # Note: replicate bug when address is on page boundary
        l, h = self.memory[self.PC], (
            self.memory[self.PC + 1] if self.PC & 0xFF != 0xFF else self.memory[self.PC & 0xFF00])
        self.PC += 2
        address = self._combine(l, h)
        return self._combine(self.memory[address], self.memory[address + 1])

    def addressing_X_IND(self):
        # An 8-bit zero-page address and the X register are added, without carry (if the addition overflows, 
        # the address wraps around within page 0). The resulting address is used as a pointer to the data being 
        # accessed. 
        base = self.memory[self.PC] + self.X
        self.PC += 1
        address = self._combine(self.memory[base], self.memory[base + 1])
        return address

    def addressing_IND_Y(self):
        base = self.memory[self.PC]
        self.PC += 1
        return self._combine(self.memory[base], self.memory[base + 1]) + self.Y

    # Instructions
    def ADC(self, address):
        result = self.A + self.memory[address] + self.F['C']
        self._setNZ(result & 0xFF)
        self.F['C'] = int(result > 0xFF)
        # Thanks https://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
        self.F['V'] = int(((self.A ^ result) & (self.memory[address] ^ result) & 0x80) > 0)
        self.A = result & 0xFF

    def AND(self, address):
        result = self.A & self.memory[address]
        self._setNZ(result)
        self.A = result

    def ASL(self, address):
        if address is None:
            value = self.A
        else:
            value = self.memory[address]
        self.F['C'] = value >> 7
        result = (value << 1) & 0xFF
        self._setNZ(result)
        if address is None:
            self.A = result
        else:
            self.memory[address] = result

    def BRK(self, address):
        self.F['B'] = 1

    def BPL(self, address):
        if not self.F['N']:
            self.PC += address

    def BMI(self, address):
        if self.F['N']:
            self.PC += address

    def BVC(self, address):
        if not self.F['V']:
            self.PC += address

    def BVS(self, address):
        if self.F['V']:
            self.PC += address

    def BCC(self, address):
        if not self.F['C']:
            self.PC += address

    def BCS(self, address):
        if self.F['C']:
            self.PC += address

    def BNE(self, address):
        if not self.F['Z']:
            self.PC += address

    def BEQ(self, address):
        if self.F['Z']:
            self.PC += address

    def BIT(self, address):
        value = self.memory[address]
        self._setNZ(value & self.A)
        self.F['N'] = value >> 7
        self.F['V'] = (value & 0x40) >> 6

    def CLC(self, address):
        self.F['C'] = 0

    def CLD(self, address):
        self.F['D'] = 0

    def CLI(self, address):
        self.F['I'] = 0

    def CLV(self, address):
        self.F['V'] = 0

    def CMP(self, address):
        result = self.A - self.memory[address]
        self.F['C'] = int(result >= 0)
        self._setNZ(result)

    def CPX(self, address):
        result = self.X - self.memory[address]
        self.F['C'] = int(result >= 0)
        self._setNZ(result)

    def CPY(self, address):
        result = self.Y - self.memory[address]
        self.F['C'] = int(result >= 0)
        self._setNZ(result)

    def DEC(self, address):
        result = (self.memory[address] - 1) & 0xFF
        self.memory[address] = result
        self._setNZ(result)

    def DEX(self, address):
        self.X = (self.X - 1) & 0xFF
        self._setNZ(self.X)

    def DEY(self, address):
        self.Y = (self.Y - 1) & 0xFF
        self._setNZ(self.Y)

    def EOR(self, address):
        result = self.A ^ self.memory[address]
        self._setNZ(result)
        self.A = result

    def INC(self, address):
        value = (self.memory[address] + 1) & 0xFF
        self.memory[address] = value
        self._setNZ(value)

    def INX(self, address):
        self.X = (self.X + 1) & 0xFF
        self._setNZ(self.X)

    def INY(self, address):
        self.Y = (self.Y + 1) & 0xFF
        self._setNZ(self.Y)

    def JMP(self, address):
        self.PC = address

    def JSR(self, address):
        value = self.PC - 1
        self.push((value & 0xFF00) >> 8)  # save high byte of PC
        self.push(value & 0x00FF)  # save low byte of PC
        self.PC = address
        self._indent += 1

    def LDA(self, address):
        self.A = self.memory[address]
        self._setNZ(self.A)

    def LDX(self, address):
        self.X = self.memory[address]
        self._setNZ(self.X)

    def LDY(self, address):
        self.Y = self.memory[address]
        self._setNZ(self.Y)

    def LSR(self, address):
        if address is None:
            value = self.A
        else:
            value = self.memory[address]
        self.F['C'] = value & 0x01
        result = value >> 1
        self._setNZ(result)
        if address is None:
            self.A = result
        else:
            self.memory[address] = result

    def NOP(self, address):
        pass

    def ORA(self, address):
        result = self.A | self.memory[address]
        self._setNZ(result)
        self.A = result

    def PHA(self, address):
        self.push(self.A)

    def PHP(self, address):
        self.push(self._pack_status_register(self.F))

    def PLA(self, address):
        self.A = self.pop()
        self._setNZ(self.A)

    def PLP(self, address):
        self.F = self._unpack_status_register(self.pop())

    def ROL(self, address):
        if address is None:
            value = self.A
        else:
            value = self.memory[address]
        _carrytemp = value >> 7
        result = ((value << 1) | self.F['C']) & 0xFF
        self._setNZ(result)
        self.F['C'] = _carrytemp
        if address is None:
            self.A = result
        else:
            self.memory[address] = result

    def ROR(self, address):
        if address is None:
            value = self.A
        else:
            value = self.memory[address]
        _carrytemp = value & 0x01
        result = ((value >> 1) | self.F['C'] << 7) & 0xFF
        self._setNZ(result)
        self.F['C'] = _carrytemp
        if address is None:
            self.A = result
        else:
            self.memory[address] = result

    def RTI(self, Address):
        # TODO: untested
        self.F = self._unpack_status_register(self.pop())
        value = self.pop() + (self.pop() << 8)
        self.PC = value

    def RTS(self, address):
        value = self.pop() + (self.pop() << 8)
        self.PC = value + 1
        self._indent -= 1

    def SBC(self, address):
        result = self.A - self.memory[address] - (1 - self.F['C'])
        self._setNZ(result & 0xFF)
        self.F['C'] = int(result >= 0x00)
        # Thanks https://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
        self.F['V'] = int(((self.A ^ result) & ((0xFF - self.memory[address]) ^ result) & 0x80) > 0)
        self.A = result & 0xFF

    def SEC(self, address):
        self.F['C'] = 1

    def SED(self, address):
        self.F['D'] = 1

    def SEI(self, address):
        self.F['I'] = 1

    def STA(self, address):
        self.memory[address] = self.A

    def STX(self, address):
        self.memory[address] = self.X

    def STY(self, address):
        self.memory[address] = self.Y

    def TAX(self, address):
        self.X = self.A
        self._setNZ(self.A)

    def TAY(self, address):
        self.Y = self.A
        self._setNZ(self.A)

    def TSX(self, adrress):
        self.X = self.SP
        self._setNZ(self.X)

    def TXA(self, address):
        self.A = self.X
        self._setNZ(self.X)

    def TXS(self, address):
        self.SP = self.X

    def TYA(self, address):
        self.A = self.Y
        self._setNZ(self.Y)
