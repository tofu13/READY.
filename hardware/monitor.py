MONITOR_HELP = """READY. monitor. Commands list:
d|disass [start] [end] -- disassemble
m|mem [start] [end] -- show memory as hex and text
i [start] [end] -- show memory as text
bk [addres] -- show breakpoints. If address specifies, set one at address 
s|setp -- execute next instruction
del [address] -- delete breakpoint at address
q|quit -- exit monitor and resume
reset -- reset machine
"""


class Monitor:
    def __init__(self, machine):
        self.machine = machine
        self.current_address = None

    def run(self):
        self.current_address = self.machine.cpu.PC
        print(self.machine.cpu)
        loop = True
        while loop:
            args = input(f"${self.current_address:04x}> ").split()
            if not args:
                continue

            cmd = args.pop(0).lower()
            if cmd in ("d", "disass"):
                start = int(args[0], 16) if len(args) > 0 else self.current_address
                end = min(int(args[1], 16) if len(args) > 1 else start + 0x040, 0xFFFF)
                while self.current_address < end:
                    output, step = self.machine.memory.disassemble(self.current_address)
                    print(output)
                    self.current_address = min(self.current_address + step, 0xFFFF)
                    # TODO: fix current address

            elif cmd in ("m", "mem"):
                start = int(args[0], 16) if len(args) > 0 else self.current_address
                end = int(args[1], 16) if len(args) > 1 else start + 0x090
                print(self.machine.memory.dump(start, end))
                self.current_address = end & 0xFFFF

            elif cmd == "i":
                start = int(args[0], 16) if len(args) > 0 else self.current_address
                end = int(args[1], 16) if len(args) > 1 else start + 0x090
                print(self.machine.memory.dump(start, end, as_chars=True))
                self.current_address = end & 0xFFFF

            elif cmd == "bk":
                if len(args) > 1:
                    print("breakpoint allows max 1 address argument")
                if len(args) == 1:
                    self.machine.cpu.breakpoints.add(int(args[0], 16))
                print("\n".join(map(lambda x: f"${x:04X}", self.machine.cpu.breakpoints)))

            elif cmd == "del":
                if len(args) == 1:
                    self.machine.cpu.breakpoints.discard(int(args[0], 16))
                    print("\n".join(map(lambda x: f"${x:04X}", self.machine.cpu.breakpoints)))
                else:
                    print("delete breakpoint needs exactly 1 address argument")

            elif cmd == "buf":
                self.machine.input_buffer = " ".join(args)

            elif cmd == "buffile":
                try:
                    with open(args[0], 'r') as ifile:
                        self.machine.input_buffer = ifile.read()
                except FileNotFoundError as e:
                    print(e)

            elif cmd == "s":
                output, step = self.machine.memory.disassemble(self.machine.cpu.PC)
                self.machine.cpu.step()
                self.current_address = self.machine.cpu.PC
                print(output, self.machine.cpu)

            elif cmd == "q":
                return False

            elif cmd == "reset":
                self.machine.cpu.reset(PC=0xFCE2)
                return False

            elif cmd in ("?", "help"):
                print(MONITOR_HELP)

            else:
                print(f"Unkwown command {cmd}")
