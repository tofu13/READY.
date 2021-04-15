import pickle
import datetime
import argparse

class Machine:
    def __init__(self, memory, cpu, screen, roms, ciaA):

        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.ciaA = ciaA

        self.monitor = Monitor(self)
        self.monitor_active = False

        # Default processor port (HIRAM, LORAM, CHARGEN = 1)
        self.memory[1] = 7

    def run(self, address):
        """
        Main process loop
        :param address: address to run from
        """

        # Setup
        self.cpu.F['B'] = 0
        self.cpu.PC = address
        running = True

        while running:
            # Activate monitor on events
            if self.monitor_active or self.cpu.PC in self.cpu.breakpoints:
                self.monitor_active = self.monitor.run()

            try:
                # Execute current instruction
                running = self.cpu.step()

                # Run CIA A, save interrupts and special events
                irq, nmi, event = self.ciaA.step()

                # Handle CPU lines IRQ and NMI
                if irq:
                    self.cpu.irq()
                if nmi:
                    self.cpu.nmi()

                if event == "RESET":
                    self.cpu.reset(PC=0xFCE2)
                elif event == "MONITOR":
                    self.monitor_active = True
                elif event == "QUIT":
                    raise KeyboardInterrupt()

            # Handle exit
            except KeyboardInterrupt:
                running = False

        print(f"BRK encountered at ${self.cpu.PC:04X}")

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            machine = cls()
            machine.cpu.A = pickle.load(f)
            machine.cpu.X = pickle.load(f)
            machine.cpu.Y = pickle.load(f)
            machine.cpu.PC = pickle.load(f)
            machine.cpu.SP = pickle.load(f)
            machine.cpu.F = pickle.load(f)
            machine.cpu.memory = pickle.load(f)
        return machine

    def restore(self, filename):
        with open(filename, 'rb') as f:
            self.cpu.A = pickle.load(f)
            self.cpu.X = pickle.load(f)
            self.cpu.Y = pickle.load(f)
            self.cpu.PC = pickle.load(f)
            self.cpu.SP = pickle.load(f)
            self.cpu.F = pickle.load(f)

            # Memory can not be loaded directly as it is referenced
            self.memory.set_slice(0, pickle.load(f))

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.cpu.A, f)
            pickle.dump(self.cpu.X, f)
            pickle.dump(self.cpu.Y, f)
            pickle.dump(self.cpu.PC, f)
            pickle.dump(self.cpu.SP, f)
            pickle.dump(self.cpu.F, f)
            pickle.dump(self.memory, f)

    def load(self, filename, base, format_cbm=False):
        with open(filename, 'rb') as f:
            # First two bytes are base address for loading into memory (little endian)
            l, h = f.read(2)
            if format_cbm:
                base = h << 8 | l
            data = f.read()
        for i, b in enumerate(data):
            self.memory[base + i] = b
        print(f"Loaded {len(data)} bytes starting at ${base:04X}")
        return base


class Monitor:
    def __init__(self, machine):
        self.machine = machine
        self.current_address = None

    def run(self):
        self.current_address = self.machine.cpu.PC
        print (self.machine.cpu)
        loop = True
        while loop:
            args = input(f"${self.current_address:04x}> ").split()
            if not args:
                continue

            cmd = args.pop(0)
            if cmd == "m":
                start = int(args[0], 16) if len(args) > 0 else self.current_address
                end = int(args[1], 16) if len(args) > 1 else start + 0x090
                print(self.machine.memory.dump(start, end))
                self.current_address = end

            elif cmd == "i":
                start = int(args[0], 16) if len(args) > 0 else self.current_address
                end = int(args[1], 16) if len(args) > 1 else start + 0x090
                print(self.machine.memory.dump(start, end, as_chars=True))
                self.current_address = end

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

            elif cmd == "s":
                return True

            elif cmd == "q":
                return False

            elif cmd == "reset":
                self.machine.cpu.reset(PC=0xFCE2)
                return False
            else:
                print(f"Unkwown command {cmd}")
