import pickle

import pygame.event
import pyperclip

import hardware.memory
from hardware.constants import PETSCII, VIDEO_SIZE
from hardware import monitor


class Machine:
    def __init__(self,
                 memory: hardware.memory.Memory,
                 cpu: hardware.cpu.CPU,
                 screen: hardware.screen.VIC_II,
                 ciaA,
                 diskdrive=None
                 ):

        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.ciaA = ciaA
        self.diskdrive = diskdrive

        self.monitor = monitor.Monitor(self)
        self.monitor_active = False

        # Default processor I/O
        self.memory[0] = 47
        # Default processor ports  (HIRAM, LORAM, CHARGEN = 1)
        self.memory[1] = 55
        # Assert datassette stopped
        self.set_datassette_button_status(False)

        self.signal = None
        self.nmi = False

        self.input_buffer = ""
        self._clock_counter = 0

        self.display = pygame.display.set_mode(VIDEO_SIZE, depth=16)  # , flags=pygame.SCALED)
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([
            pygame.QUIT,
            pygame.WINDOWCLOSE,
            pygame.KEYDOWN,
            pygame.KEYUP,
        ])

        self.CAPTION = "Commodore 64 (Text) {:.1f} FPS"

        # pygame.display.set_caption(self.CAPTION)

        self.pygame_clock = pygame.time.Clock()
        self._last_fps = 0

        self.paste_buffer = []

        # self.cpu.breakpoints.add(0xF4C4)

        self.outfile = open("OUTFILE", "wb")

        self.patches = {
            0xF4C4: self.patch_IECIN,
            # 0xEDB9: self.patch_LSTNSA,
            0xF3D5: self.patch_OPEN,
            # 0xED0C: self.patch_LISTEN,
            0xEEA9: self.patch_CLKDATA,
            0xED40: self.patch_SNDBYT,
            0xEE13: self.patch_RDBYTE,
            0xFDF9: self.patch_SETNAM,
            0xFE99: self.patch_SETLFS,
        }

        self.serial_device_number = None
        self.keys_pressed = set()

        self.breakpoints = set()
        self.tracepoints = set()

    def run(self, address):
        """
        Run main loop
        """

        # Setup
        self.cpu.F['B'] = 0
        self.cpu.PC = address

        while True:
            self.clock()

    def clock(self):
        """
        Run a single step of all devices
        """
        # Activate monitor on breakpoints
        if self.breakpoints:
            self.monitor_active |= self.cpu.PC in self.breakpoints
        if self.monitor_active:
            self.monitor.cmdloop()
            self.monitor_active = False

        if self.tracepoints:
            for start, end in self.tracepoints:
                if start <= self.cpu.PC <= end:
                    print(self.cpu)

        if (patch := self.patches.get(self.cpu.PC)) is not None:
            patch()

        # Run VIC-II
        frame = self.screen.clock()

        # Display complete frame
        if frame is not None:
            self.display.blit(frame, (0, 0))
            pygame.display.flip()
            # Get FPS
            self.pygame_clock.tick()  # Max 50 FPS
            if (current_ticks := pygame.time.get_ticks()) - self._last_fps > 1000:
                pygame.display.set_caption(self.CAPTION.format(self.pygame_clock.get_fps()))
                self._last_fps = current_ticks

        # Paste text
        if self.paste_buffer and self.memory[0xC6] == 0:
            # Inject char into empty keyboard buffer
            char = self.paste_buffer.pop(0)
            petscii_code = PETSCII.get(char.lower())
            if not petscii_code:  # TODO: is None
                print(f"WARNING: character {char} not in PETSCII")
            else:
                self.memory[0x277 + self.memory[0xC6]] = petscii_code
                # Update buffer length
                self.memory[0xC6] += 1

        # Run CPU
        self.cpu.clock()

        # Run CIA A, handle interrupt if any
        if self.ciaA.clock(self.keys_pressed):
            self.cpu.irq()

        self._clock_counter += 1
        if self._clock_counter % 1000 == 0:
            self.signal, self.nmi = self.manage_events()

        if self.nmi:
            self.cpu.nmi()
            self.nmi = False

        if self.signal == "RESET":
            self.cpu.reset(PC=0xFCE2)
            self.signal = None
        elif self.signal == "MONITOR":
            self.monitor_active = True
            self.signal = None

    def manage_events(self):
        """
        Manage system events
        """
        signal = None
        nmi = False
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                # Scan RESTORE key
                if event.key == pygame.K_PAGEUP:
                    nmi = True

                # Also scan special keys
                elif event.key == pygame.K_F12:
                    signal = "RESET"
                elif event.key == pygame.K_F11:
                    signal = "MONITOR"
                elif event.key == pygame.K_F10:
                    # F10 -> paste text
                    try:
                        self.paste_buffer = list(pyperclip.paste())
                    except pyperclip.PyperclipException:
                        print(
                            "Can't paste: xsel or xclip system packages not found. "
                            "See https://pyperclip.readthedocs.io/en/latest/index.html#not-implemented-error")

                # Hardware events
                elif event.key == pygame.K_p and event.mod & pygame.KMOD_RCTRL:
                    # PLAY|REC|FFWD|REW is pressed on datassette
                    self.set_datassette_button_status(True)
                elif event.key == pygame.K_s and event.mod & pygame.KMOD_RCTRL:
                    # STOP is pressed on datassette
                    self.set_datassette_button_status(False)

            elif event.type == pygame.KEYUP:
                self.keys_pressed.remove(event.key)

            elif event.type == pygame.WINDOWCLOSE:
                pygame.quit()

        return signal, nmi

    def patch_IECIN(self):
        print("Serial patch IECIN")
        print(self.cpu.A)  # self.cpu.A = 0x42
        # self.cpu.PC = 0xEE84

    def patch_LSTNSA(self):
        print(f"KERNAL patch LSTNSA: A={self.cpu.A}")

    def patch_OPEN(self):
        print(f"Serial patch openfile: A={self.cpu.A}, Y={self.cpu.Y}")

        self.byteprovider = (byte for byte in self.diskdrive.read(self.filename))

    def patch_LISTEN(self):
        print(f"KERNAL patch LISTEN: A={self.cpu.A}")
        self.serial_device_number = self.cpu.A

    def patch_CLKDATA(self):  # Fix name
        # print(f"KERNAL patch Read CLOCK IN and DATA IN.: A={self.cpu.A}")
        self.cpu.PC = 0xEEB2  # Skip to RTS

    def patch_SNDBYT(self):  # fix name
        data = self.memory[0x95]
        # print(f"Write byte to serial bus: data={bytes([data])} {chr(data)}")
        self.outfile.write(bytes([data]))
        self.cpu.PC = 0xEDAC  # Jump to RTS
        # SAQ: ok salva. Ora distingui l'apertura del file dai dati

    def patch_RDBYTE(self):  # fix name
        try:
            self.cpu.A = next(self.byteprovider)
        except StopIteration:
            self.memory[0x90] |= 0x40
        else:
            self.memory[0x90] &= 0xBF
        # print(f"Read byte from serial bus {chr(self.cpu.A)} {hex(self.cpu.A)}")
        self.cpu.PC = 0xEE84

    def patch_SETNAM(self):
        address = self.cpu._combine(self.cpu.X, self.cpu.Y)
        length = self.cpu.A
        self.filename = self.memory.get_slice(address, address + length)
        print(f"set filename to: {self.filename}")

    def patch_SETLFS(self):
        self.logical_file_number = self.cpu.A
        self.serial_device_number = self.cpu.X
        self.secondary_address = self.cpu.Y

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
            lo, hi = f.read(2)
            if format_cbm:
                base = hi << 8 | lo
            data = f.read()
        for i, byte in enumerate(data):
            self.memory[base + i] = byte
        print(f"Loaded {len(data)} bytes starting at ${base:04X}")
        return base

    def set_datassette_button_status(self, status: bool):
        """
        Set bit #5 of address $01
        status True (PLAY|REC|FFWD|REW is pressed) -> clear bit
        status False (STOP has been pressed) -> set bit
        """
        # Bypass normal memory write, this is hardwired
        if status:
            self.memory.write(0x01, self.memory[0x01] & 0b11101111)
        else:
            self.memory.write(0x01, self.memory[0x01] | 0b00010000)


def DefaultMachine() -> Machine:
    import hardware
    from config import ROMS_FOLDER
    roms = hardware.roms.ROMS(ROMS_FOLDER)
    memory = hardware.memory.BytearrayMemory(65536, roms)
    return Machine(
        memory,
        hardware.cpu.CPU(memory),
        hardware.screen.RasterScreen(memory),
        hardware.cia.CIA_A(memory)
    )
