import cmd
from typing import Optional

from hardware.constants import INVERSE_OPCODES, ASSEMBLER_REGEXES


class Monitor(cmd.Cmd):
    use_rawinput = False

    def __init__(self, machine):
        # region abbreviations
        self.do_d = self.do_disass
        self.do_z = self.do_step
        self.do_n = self.do_next
        # end region

        super().__init__()
        self.machine = machine
        self.current_address = None

    def parse_addresses(self, line: str, span: int = 0x20):
        args = [convert(arg) for arg in line.split(maxsplit=2)]
        if None in args:
            # Errors while converting
            return False

        match len(args):
            case 0:
                start = self.current_address
                end = min(start + span, 0xFFFF)
            case 1:
                start = args[0]
                end = min(start + span, 0xFFFF)
            case 2:
                start, end = args
            case _:
                # Extra arguments
                return False
        return start, end

    def preloop(self):
        self.saved_address = self.machine.cpu.PC
        self.current_address = self.machine.cpu.PC
        self.prompt = f"${self.current_address:04x}> "

    def precmd(self, line):
        return line

    def postcmd(self, stop, args):
        self.prompt = f"${self.current_address:04x}> "
        return stop

    def do_disass(self, line):
        """
        disass|d [<address> [<address>]]

        Disassemble instructions.  If two addresses are specified, they are
        used as a start and end address.  If only one is specified, it is
        treated as the start address and a default number of instructions are
        disassembled.  If no addresses are specified, a default number of
        instructions are disassembled from the dot address.
        """
        if addresses := self.parse_addresses(line, span=0x80):
            self.current_address, end = addresses
            while self.current_address < end:
                output, step = self.machine.memory.disassemble(self.current_address)
                print(f"${self.current_address:04X}: {output}")
                self.current_address = min(self.current_address + step, 0xFFFF)

    def do_mem(self, line):
        """
        mem|m [<address>] [<address>]

        Display the contents of memory.  If no datatype is given, the default
        is used.  If only one address is specified, the length of data
        displayed is based on the datatype.  If no addresses are given, the
        'dot' address is used.
        Please note: due to the ambiguous meaning of 'b' and 'd' these data-
        types must be given in uppercase!
        """
        if addresses := self.parse_addresses(line, span=0x80):
            self.current_address, end = addresses
            print(self.machine.memory.dump(self.current_address, end))
            self.current_address = end

    def do_i(self, line):
        """
        i <address_opt_range>

        Display memory contents as PETSCII text.
        """
        if addresses := self.parse_addresses(line, span=0x040):
            self.current_address, end = addresses
            print(self.machine.memory.dump(self.current_address, end, as_chars=True))
            self.current_address = end

    def do_bk(self, line: str):
        if line:
            address = convert(line.split(maxsplit=1)[0])
            if address is not None:
                self.machine.breakpoints.add(address)
        print("\n".join(map(lambda x: f"${x:04X}", self.machine.breakpoints)))

    def do_del(self, line):
        if line:
            address = convert(line.split(maxsplit=1)[0])
            if address is not None:
                self.machine.breakpoints.discard(address)
        print("\n".join(map(lambda x: f"${x:04X}", self.machine.breakpoints)))

    def do_trace(self, line):
        """
        trace [<start_address> <end_address>]

        Set a tracing exec from start to end.
        Without arguments show tracepoints
        """
        show = False
        args = line.split()
        if len(args) == 2:
            start = convert(args[0])
            end = convert(args[1])
            if start is not None and end is not None:
                self.machine.tracepoints.add((start, end))
                show = True
        if len(args) == 0 or show:
            for start, end in self.machine.tracepoints:
                print(f"${start:04X} - ${end:04X}")

    def do_step(self, line):
        """
        step|z [<count>]

        Single-step through instructions.  COUNT allows stepping
        more than a single instruction at a time ("step into").
        """
        output, step = self.machine.memory.disassemble(self.machine.cpu.PC)
        self.machine.cpu.step()
        self.current_address = self.machine.cpu.PC
        print(output, self.machine.cpu)

    def do_next(self, line):
        """
        next|n [<count>]

        Advance to the next instruction(s).  COUNT allows stepping
        more than a single instruction at a time. Subroutines are
        treated as a single instruction ("step over").
        """
        output, step = self.machine.memory.disassemble(self.machine.cpu.PC)
        starting_indent = self.machine.cpu.indent
        condition = True
        while condition:
            self.machine.cpu.step()
            condition = self.machine.cpu.indent > starting_indent
        self.current_address = self.machine.cpu.PC
        print(output, self.machine.cpu)

    def do_go(self, line):
        """
        go|g [<address>]

        Jump to <address> or to the current monitor address
        """
        args = line.split()
        match len(args):
            case 0:
                address = self.current_address
            case 1:
                if (address := convert(args[0])) is None:
                    return False
            case _:
                return False

        self.machine.cpu.PC = address
        return True

    def do_convert(self, line):
        """
        convert <number>
        """
        args = line.split()
        if (value := convert(args[0])) is not None:
            print("\n".join(multiconvert(value)))

    def do_reset(self, line):
        """
        reset

        Soft reset
        """
        self.machine.cpu.reset(PC=0xFCE2)
        return True

    def do_a(self, line):
        args = line.split()
        if len(args) == 1:
            self.current_address = convert(args[0])
            self.assembler()

    """
            #obsolete ?
            elif cmd == "buf":
                self.machine.input_buffer = " ".join(args)

            #obsolete ?
            elif cmd == "buffile":
                try:
                    with open(args[0], 'r') as ifile:
                        self.machine.input_buffer = ifile.read()
                except FileNotFoundError as e:
                    print(e)
    """

    def do_x(self, line):
        """
        x

        Resume simulation
        """
        self.machine.cpu.PC = self.saved_address
        return True

    def assembler(self):
        while True:
            cmd = input(f"{self.current_address:04X}\t")
            args = cmd.split()
            match len(args):
                case 0:
                    break
                case 1 | 2:
                    data = parse_assembly(args, self.current_address)
                    for byte in data:
                        self.machine.memory[self.current_address] = byte
                        self.current_address += 1
                    if not data:
                        print("? parse error")
                case _:
                    print("? extra arguments")
                    continue


def convert(value: str) -> Optional[int]:
    """Return base-10 int from binary %, octal &, decimal +, hex ($) values"""
    if not value:
        return None
    match value[0]:
        case "%":
            base = 2
            value = value[1:]
        case "&":
            base = 8
            value = value[1:]
        case "+":
            base = 10
            value = value[1:]
        case "$":
            base = 16
            value = value[1:]
        case _:
            base = 16
    try:
        return int(value, base)
    except Exception as err:
        print(err)
        return None


def multiconvert(value: int) -> list[str]:
    """Return int converted into different bases"""
    return [
        f"%{value:016b}",
        f"&{value:06o}",
        f"+{value}",
        f"${value:04X}",
    ]


def parse_assembly(args: list[str], current_address: int) -> list[int]:
    data = []
    mnemonic = args[0].upper()
    if len(args) == 1:
        if (opcode := INVERSE_OPCODES.get((mnemonic, "addressing_IMP"))) is not None:
            data.append(opcode)
    elif len(args) == 2:
        # if args[1].startswith("#"):
        #    if value is not None and (opcode := INVERSE_OPCODES.get((mnemonic, "addressing_IMM"))) is not None:
        #        data.append(opcode)
        #        data.append(value)
        if args[0].upper() in ("BCC", "BCS", "BEQ", "BMI", "BNE", "BPL", "BVC", "BVS"):
            value = convert(args[1])
            if value is not None and (opcode := INVERSE_OPCODES.get((mnemonic, "addressing_REL"))) is not None:
                data.append(opcode)
                jump = value - current_address - 2  # -2 'cauze PC already stepped
                # TODO: check jump in range -128 + 127
                data.append(jump if jump > 0 else 256 + jump)
        else:
            for regex, addressing in ASSEMBLER_REGEXES.items():
                if (match := regex.match(args[1])) is not None:
                    value = [convert(match.groups()[0])]
                    if value[0] > 0x0100:
                        # This is the case when value is an address (16 bits)
                        value = [value[0] % 0x0100, value[0] // 0x0100]
                    if (opcode := INVERSE_OPCODES.get((mnemonic, f"addressing_{addressing}"))) is not None:
                        data.append(opcode)
                        data.extend(value)
                    break
    return data
