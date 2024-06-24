import pickle
import time
from typing import Optional

import pygame.event
import pyperclip

import hardware.memory
from hardware.constants import CLOCKS_PER_PERFORMANCE_REFRESH, CLOCKS_PER_CONSOLE_REFRESH, SCREEN_CHARCODE, \
    CLOCKS_PER_EVENT_SERVING, PETSCII, VIDEO_SIZE, \
    PALETTE


class PatchMixin:
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
        self.filename = self.memory[address: address + length]
        print(f"set filename to: {self.filename}")

    def patch_SETLFS(self):
        self.logical_file_number = self.cpu.A
        self.serial_device_number = self.cpu.X
        self.secondary_address = self.cpu.Y


class Machine(PatchMixin):
    def __init__(self,
                 memory: hardware.memory.Memory,
                 cpu: hardware.cpu.CPU,
                 screen: hardware.screen.VIC_II,
                 ciaA,
                 diskdrive=None,
                 console=False
                 ):

        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.ciaA = ciaA
        self.diskdrive = diskdrive
        self.console = console

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

        self.CAPTION = "Commodore 64 (Text) {:.1f} FPS {:.1f}% performance"

        # pygame.display.set_caption(self.CAPTION)

        self._cumulative_perf_timer = 0.0
        self._current_fps = 0.0

        self.paste_buffer = []

        # self.cpu.breakpoints.add(0xF4C4)

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
        self.caps_lock = False

        self.breakpoints = set()
        self.tracepoints = set()

        self.post_init()

    def post_init(self):
        """
        Second stage init, for proper loading of saved state
        """
        if not isinstance(self.screen, hardware.screen.VirtualScreen):
            self.display = pygame.display.set_mode(VIDEO_SIZE, depth=8, flags=pygame.SCALED)
            pygame.event.set_blocked(None)
            pygame.event.set_allowed([
                pygame.QUIT,
                pygame.WINDOWCLOSE,
                pygame.KEYDOWN,
                pygame.KEYUP,
            ])
            self.pygame_clock = pygame.time.Clock()
        self.monitor = hardware.monitor.Monitor(self)
        self.outfile = open("OUTFILE", "wb")  # TODO: handle this

    def __getstate__(self):
        state = self.__dict__.copy()
        # Drop attributes that will be re-created from scratch after loading
        for attribute in [
            "monitor",
            "display",
            "pygame_clock",
            "outfile",
        ]:
            if attribute in state:
                del state[attribute]
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        self.post_init()
        self.monitor_active = False  # Exit monitor after loading

    def run(self, address: Optional[int] = None) -> None:
        """
        Run main loop
        """
        if address:
            self.cpu.PC = address

        while True:
            self.clock()

    def clock(self):
        """
        Run a single step of all devices
        """
        self._cumulative_perf_timer -= time.perf_counter()
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
        frame = self.screen.clock(self._clock_counter)

        # Display complete frame
        if frame is not None:
            if not isinstance(frame, pygame.Surface):
                frame = pygame.surfarray.make_surface(frame)
                frame.set_palette(PALETTE
                                  # [
                                  # pygame.Color(0,0,0),
                                  # pygame.Color(255,255,255),
                                  # ]
                                  )
            self.display.blit(frame, (0, 0))
            pygame.display.flip()
            # Get FPS
            self.pygame_clock.tick()  # Max 50 FPS

        # Run CPU
        self.cpu.clock()

        # Run CIA A, handle interrupt if any
        if self.ciaA.clock(self.keys_pressed):
            self.cpu.irq()

        self._clock_counter += 1
        if self._clock_counter % CLOCKS_PER_EVENT_SERVING == 0:
            self.signal, self.nmi = self.manage_events()

        if self.console and self._clock_counter % CLOCKS_PER_CONSOLE_REFRESH == 0:
            # Send screen to console
            print("\033[H\033[1J", end="")  # Clear screen
            print(self.screendump())

        if self.nmi:
            self.cpu.nmi()
            self.nmi = False

        if self.signal == "RESET":
            self.cpu.reset(PC=0xFCE2)
            self.signal = None
        elif self.signal == "MONITOR":
            self.monitor_active = True
            self.signal = None

        self._cumulative_perf_timer += time.perf_counter()
        if self._clock_counter % CLOCKS_PER_PERFORMANCE_REFRESH == 0:
            pygame.display.set_caption(
                # 100% : 1000000 clocks/s = perf% : CLOCK_PER_PERFORMANCE_REFRESH
                self.CAPTION.format(self.pygame_clock.get_fps(),
                                    CLOCKS_PER_PERFORMANCE_REFRESH / 10000 / self._cumulative_perf_timer))
            self._cumulative_perf_timer = 0.0

    def manage_events(self):
        """
        Manage system events
        Do housekeeping
        """
        # Paste text
        if self.paste_buffer and self.memory[0xC6] == 0:
            # Inject char into empty keyboard buffer
            char = self.paste_buffer.pop(0)
            petscii_code = PETSCII.get(char.lower())
            if petscii_code is None:
                print(f"WARNING: character {char} not in PETSCII")
            else:
                self.memory[0x277] = petscii_code
                # Update buffer length
                self.memory[0xC6] += 1

        signal = None
        nmi = False
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                # Scan RESTORE key
                if event.key == pygame.K_PAGEDOWN:
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
                elif event.key == pygame.K_CAPSLOCK:
                    self.caps_lock = not self.caps_lock
                    if not self.caps_lock:
                        self.keys_pressed.remove(pygame.K_LSHIFT)
                else:
                    self.keys_pressed.add(event.key)

                if self.caps_lock:
                    self.keys_pressed.add(pygame.K_LSHIFT)

            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)

            elif event.type == pygame.WINDOWCLOSE:
                pygame.quit()

        return signal, nmi

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    def restore(self, filename):  # TODO drop
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
            pickle.dump(self, f)

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
            self.memory[0x01] = self.memory[0x01] & 0b11101111
        else:
            self.memory[0x01] = self.memory[0x01] | 0b00010000

    def screendump(self) -> str:
        dump = ""
        base = self.screen.video_matrix_base_address
        data = self.memory.get_slice(base, base + 1000)
        data_char = list(map(lambda x: SCREEN_CHARCODE.get(x % 128, "."), data))
        for row in range(25):
            dump += "".join(data_char[row * 40: (row + 1) * 40 - 1]) + "\n"
        return dump


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
