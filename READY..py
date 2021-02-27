from constants import *
from config import *
from utils import *

import hardware

import argparse
import os.path

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
        self.F = {'N': 0, 'V': 0, '-': 1, 'B': 0, 'D': 0, 'I': 0, 'Z': 0, 'C': 0}

        self.opcodes = dict()
        for opcode, specs in OPCODES.items():
            if specs is not None:
                if not hasattr(self, specs[0]):
                    setattr(self, specs[0], self._not_implemented)
                self.opcodes[opcode] = getattr(self, specs[0])
        for addressing in ADDRESSING_METHODS:
            if not hasattr(self, f"addressing_{addressing}"):
                setattr(self, f"addressing_{addressing}", self._not_implemented)

    def __str__(self):
        st = "".join(f"{k}:{v} " for k,v in self.F.items())
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
        #print(f"Fetched at {self.PC:04X}: {self.opcodes[opcode]}")
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
        address = getattr(self, f"addressing_{mode}")()
        print(f"@${pc:04X} Executing {instruction}\t{mode if mode != 'None' else ''}\t{self}")
        getattr(self, instruction)(address)
        return instruction != 'BRK'

    def run(self, address=None):
        """
        Run from address (or PC if not specified) until BRK
        :param address: address to start execution
        :return: None
        """
        self.F['B'] = 0
        if address is not None:
            self.PC = address
        while not self.F['B']:
            self.step()

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

    def _pack_status_register(self, value):
        result = 0
        for i, flag in enumerate(value.values()):
            result |= 2**(7 - i) * flag
        return result

    def _unpack_status_register(self, value):
        result = dict()
        for i, flag in enumerate(self.F.keys()):
            result[flag] = (value & 2**(7 - i)) >> (7 - i)
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
        # An 8-bit signed offset is provided. This value is added to the program counter (PC) to find the effective address.
        address = self.memory[self.PC]
        self.PC += 1
        return address if address < 127 else address - 256

    def addressing_ABS(self):
        # Data is accessed using 16-bit address specified as a constant.
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return self._combine(l, h)

    def addressing_ZP(self):
        # An 8-bit address is provided within the zero page.
        address = self.memory[self.PC]
        self.PC += 1
        return address

    def addressing_ABS_X(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the X register is added (with carry).
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return self._combine(l, h) + self.X

    def addressing_ABS_Y(self):
        # Data is accessed using a 16-bit address specified as a constant, to which the value of the Y register is added (with carry).
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        return self._combine(l, h) + self.Y

    def addressing_ZP_X(self):
        # An 8-bit address is provided, to which the X register is added (without carry - if the addition overflows, the address wraps around within the zero page).
        l = self.memory[self.PC]
        self.PC += 1
        return (l + self.X) & 0xFF

    def addressing_ZP_Y(self):
        # An 8-bit address is provided, to which the Y register is added (without carry - if the addition overflows, the address wraps around within the zero page).
        l = self.memory[self.PC]
        self.PC += 1
        return (l + self.Y) & 0xFF

    def addressing_IND(self):
        # Data is accessed using a pointer. The 16-bit address of the pointer is given in the two bytes following the opcode.
        l, h = self.memory[self.PC], self.memory[self.PC +1]
        self.PC += 2
        address = self._combine(l, h)
        return self._combine(self.memory[address], self.memory[address + 1])

    def addressing_X_IND(self):
        # An 8-bit zero-page address and the X register are added, without carry (if the addition overflows, the address wraps around within page 0). The resulting address is used as a pointer to the data being accessed.
        base = self.memory[self.PC] + self.X
        self.PC += 1
        address = self._combine(self.memory[base], self.memory[base + 1])
        return address

    def addressing_IND_Y(self):
        base = self.memory[self.PC]
        self.PC += 1
        address = self._combine(self.memory[base], self.memory[base + 1]) + self.Y
        return address

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
        self.A = result

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
        self.push((value & 0xFF00) >> 8) # save high byte of PC
        self.push(value & 0x00FF) # save low byte of PC
        self.PC = address

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
        result = value >> 1
        self._setNZ(result)
        self.F['C'] = value & 0x01
        self.A = result

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

    def PLP(self, address):
        self.F = self._unpack_status_register(self.pop())

    def ROL(self, address):
        if address is None:
            value = self.A
        else:
            value = self.memory[address]
        result = ((value << 1) | self.F['C']) & 0xFF
        self.F['C'] = value >> 7
        self._setNZ(result)
        self.A = result

    def ROR(self, address):
        if address is None:
            value = self.A
        else:
            value = self.memory[address]
        result = ((value >> 1) | self.F['C'] << 7) & 0xFF
        self.F['C'] = value & 0x01
        self._setNZ(result)
        self.A = result

    def RTI(self, Address):
        # TODO: untested
        self.F = self._unpack_status_register(self.pop())
        value = self.pop() + (self.pop() << 8)
        self.PC = value + 1

    def RTS(self, address):
        value = self.pop() + (self.pop() << 8)
        self.PC = value + 1

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

    def TXA(self, address):
        self.A = self.X
        self._setNZ(self.X)

    def TYA(self, address):
        self.A = self.Y
        self._setNZ(self.Y)


class Screen:
    memory = None

    def init(self):
        pass
    #   self.memory.write_watchers.append([0x0100, 0x07FF, self.refresh])

    def refresh(self, address, value):
        print("\n".join(
            ["".join(map(chr,self.memory[1024 + i*40: 1024 + i*40 + 39])) for i in range(0, 24, 40)])
        )
        return value

class ROMS:
    def __init__(self):
        self.contents = {}
        self.load()

    def load(self):
        for name, begin, end, bank_bit in ROMSLIST:
            with open(os.path.join(ROMS_FOLDER, name), 'rb') as rom:
                self.contents[name] = bytearray(rom.read())

    def init(self):
        for name, begin, end, bank_bit in ROMSLIST:
            self.memory.read_watchers.append([begin, end, self.read_rom])

    def read_rom(self, address, value):
        for name, begin, end, bank_bit in ROMSLIST:
            # Check bank switching bit too
            if begin <= address <= end and bit(self.memory[SYMBOLS['R6510']], bank_bit):
                return self.contents[name][address-begin]
        return value



class Machine:
    def __init__(self, memory, cpu, screen, roms):
        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.roms = roms

        self.cpu.memory = self.memory
        self.screen.memory = self.memory
        self.screen.init()
        if self.roms is not None:
            self.roms.memory = self.memory
            self.roms.init()

    def load(self, filename, base, format_cbm=False):
        with open(filename, 'rb') as f:
            if format_cbm:
                # First two bytes are base address for loading into memory (cbm file format, little endian)
                l, h = f.read(2)
                base = h << 8 | l
            data = f.read()
        for i, b in enumerate(data):
            self.memory[base + i] = b
        print(f"Loaded {len(data)} bytes starting at ${base:04X}")
        return base


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-1", "--cbm-format", action='store_true',
                        help="First two bytes of file are little endian load address (like in LOAD\"*\",8,1)")
    #parser.add_argument("-a", "--assembly", action='store_true',
    #                    help=f"Compile and run an assembler file using compiler specified with"
    #                         f" -c (default: {DEFAULT_COMPILER}). See config.")
    parser.add_argument("-c", "--compiler", action='store', default=f"{DEFAULT_COMPILER}",
                        help=f"Use this compiler. Available: {', '.join(COMPILERS.keys()) or 'none :( '}. See config.")
    parser.add_argument("-s", "--load-address", action='store',
                        help=f"Load binary file at address (if not specified: ${DEFAULT_LOAD_ADDRESS:04X}). "
                             f"Use (escaped)$ or 0x for hex value.")
    parser.add_argument("-n","--no-roms", action='store_true', default=False,
                        help="Do not load roms")
    args = parser.parse_args()

    print(args)
    if args.cbm_format and args.load_address:
        raise parser.error("-1/--cbmformat and -s/--load-addres conflicts. Choose one.")

    if args.load_address:
        try:
            if args.load_address.startswith("0x"):
                base = int(args.load_address[2:], 16)
            elif args.load_address.startswith("$"):
                base = int(args.load_address[1:], 16)
            else:
                base = int(args.load_address)
        except ValueError as err:
            raise parser.error(f"Invalid load address {args.load_address}")
        if not 0 <= base <= 0xFFFF:
            raise parser.error(f"Invalid load address {args.load_address}")

    base = None

    roms = None if args.no_roms else ROMS()
    c64 = Machine(hardware.memory.BytearrayMemory(65536), CPU(), Screen(), roms)

    if roms:
        # Set default bank switching (all roms on)
        c64.memory[0x0000] = 0xE9
        c64.memory[0x0001] = 0x07

    if True:
        base = c64.load(args.filename, base or DEFAULT_LOAD_ADDRESS, args.cbm_format)
        c64.cpu.run(base)
        pass
