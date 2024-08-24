import pickle
import time
from typing import Optional

import pygame.event
import pyperclip

from libs import hardware
from libs.hardware.constants import (
    CHARS_TO_PASTE_INTO_KEYBOARD_BUFFER,
    CLOCKS_PER_CONSOLE_REFRESH,
    CLOCKS_PER_EVENT_SERVING,
    CLOCKS_PER_PERFORMANCE_REFRESH,
    PALETTE,
    PETSCII,
    REAL_VIDEO_SIZE,
    SCREEN_CHARCODE,
    SIGNALS,
)


class PatchMixin:
    __slots__ = ["filename", "filesize", "byteprovider"]

    def patch_IECIN(self):
        pass
        # self.cpu.PC = 0xEE84

    def patch_LSTNSA(self):
        pass

    def patch_OPEN(self):
        def provider(self):
            """
            Generator on the open file
            Yields (data, EOF)
            EOF is True when the last byte is reached
            """
            contents = self.diskdrive.read(self.filename)
            size = len(contents)
            pos = 0
            while True:
                byte = contents[pos]
                pos += 1
                yield byte, pos == size

        self.byteprovider = provider(self)

    def patch_LISTEN(self):
        self.serial_device_number = self.cpu.A

    def patch_CLKDATA(self):  # Fix name
        self.cpu.PC = 0xEEB2  # Skip to RTS

    def patch_SNDBYT(self):  # fix name
        data = self.memory[0x95]
        self.outfile.write(bytes([data]))
        self.cpu.PC = 0xEDAC  # Jump to RTS
        # TODO: ok salva. Ora distingui l'apertura del file dai dati

    def patch_RDBYTE(self):  # fix name
        self.cpu.A, eof = next(self.byteprovider)
        if eof:
            self.memory[0x90] |= 0x40
        # else:
        #    self.memory[0x90] &= 0xBF
        # print(f"Read byte from serial bus {chr(self.cpu.A)} {hex(self.cpu.A)}")
        self.cpu.PC = 0xEE84

    def patch_SETNAM(self):
        address = self.cpu.make_address(self.cpu.X, self.cpu.Y)
        length = self.cpu.A
        self.filename = self.memory[address : address + length]

    def patch_SETLFS(self):
        self.logical_file_number = self.cpu.A
        self.serial_device_number = self.cpu.X
        self.secondary_address = self.cpu.Y


class Machine(PatchMixin):
    __slots__ = [
        "memory",
        "cpu",
        "screen",
        "ciaA",
        "ciaB",
        "diskdrive",
        "console",
        "monitor_active",
        "signal",
        "nmi",
        "input_buffer",
        "CAPTION",
        "paste_buffer",
        "patches",
        "serial_device_number",
        "keys_pressed",
        "caps_lock",
        "breakpoints",
        "tracepoints",
        "_clock_counter",
        "_last_perf_timer",
        "_current_fps",
        # Unpickables
        "monitor",
        "display",
        "pygame_clock",
        "outfile",
    ]

    def __init__(
        self,
        memory: hardware.memory.Memory,
        cpu: hardware.cpu.CPU,
        screen: hardware.screen.VIC_II,
        ciaA,
        ciaB,
        diskdrive=None,
        console=False,
        autotype="",
    ):
        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.ciaA = ciaA
        self.ciaB = ciaB
        self.diskdrive = diskdrive
        self.console = console

        self.monitor_active = False

        # Default processor I/O
        self.memory[0] = 47
        # Default processor ports  (HIRAM, LORAM, CHARGEN = 1)
        self.memory[1] = 55
        # Assert datassette stopped
        self.set_datassette_button_status(False)

        self.signal = SIGNALS.NONE
        self.nmi = False

        self.input_buffer = ""
        self._clock_counter = 0

        self.CAPTION = "Commodore 64 (Text) {:.1f} FPS {:.1f}% performance"

        # pygame.display.set_caption(self.CAPTION)

        self._last_perf_timer = time.perf_counter()
        self._current_fps = 0.0

        self.paste_buffer = list(autotype)

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
            self.display = pygame.display.set_mode(
                REAL_VIDEO_SIZE, depth=8, flags=pygame.SCALED
            )
            pygame.event.set_blocked(None)
            pygame.event.set_allowed(
                [
                    pygame.QUIT,
                    pygame.WINDOWCLOSE,
                    pygame.KEYDOWN,
                    pygame.KEYUP,
                ]
            )
            self.pygame_clock = pygame.time.Clock()
        self.monitor = hardware.monitor.Monitor(self)
        self.outfile = open("OUTFILE", "wb")  # TODO: handle this

    def __getstate__(self):
        state = {
            key: getattr(self, key)
            for key in self.__slots__
            # Skip attributes that will be re-created from scratch after loading
            if key
            not in [
                "monitor",
                "display",
                "pygame_clock",
                "outfile",
            ]
        }
        return state

    def __setstate__(self, state):
        for key, value in state.items():
            setattr(self, key, value)
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
        frame, irq = self.screen.clock(self._clock_counter)

        # Display complete frame
        if frame is not None:
            frame = pygame.surfarray.make_surface(frame)
            frame.set_palette(PALETTE)
            self.display.blit(frame, (0, 0))
            pygame.display.flip()
            # Get FPS
            self.pygame_clock.tick()  # Max 50 FPS

        # Run CPU
        self.cpu.clock()

        # Run CIA A
        irq |= self.ciaA.clock(self.keys_pressed)
        irq |= self.ciaB.clock()

        # Handle irq if any
        if irq:
            self.cpu.irq()

        self._clock_counter += 1
        if self._clock_counter % CLOCKS_PER_EVENT_SERVING == 0:
            self.signal, self.nmi = self.manage_events()
            if self.signal is SIGNALS.RESET:
                self.cpu.PC = 0xFCE2
                self.signal = SIGNALS.NONE
            elif self.signal is SIGNALS.MONITOR:
                self.monitor_active = True
                self.signal = SIGNALS.NONE

        if self.console and self._clock_counter % CLOCKS_PER_CONSOLE_REFRESH == 0:
            # Send screen to console
            print("\033[H\033[1J", end="")  # Clear screen
            print(self.screendump())

        if self.nmi:
            self.cpu.nmi()
            self.nmi = False

        if self._clock_counter % CLOCKS_PER_PERFORMANCE_REFRESH == 0:
            _perf_timer = time.perf_counter()
            pygame.display.set_caption(
                # 100% : 1000000 clocks/s = perf% : CLOCK_PER_PERFORMANCE_REFRESH
                self.CAPTION.format(
                    self.pygame_clock.get_fps(),
                    CLOCKS_PER_PERFORMANCE_REFRESH
                    / 10000
                    / (_perf_timer - self._last_perf_timer),
                )
            )
            self._last_perf_timer = _perf_timer

    def manage_events(self):
        """
        Manage system events
        Do housekeeping
        """
        # Paste text
        while (
            self.paste_buffer
            and self.memory[0xC6] < CHARS_TO_PASTE_INTO_KEYBOARD_BUFFER
        ):
            # Inject char into keyboard buffer
            char = self.paste_buffer.pop(0)
            petscii_code = PETSCII.get(char.lower())
            if petscii_code is None:
                print(f"WARNING: character {char} not in PETSCII")
            else:
                self.memory[0x277 + self.memory[0xC6]] = petscii_code
                # Update buffer length
                self.memory[0xC6] += 1

        signal = SIGNALS.NONE
        nmi = False
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                # Scan RESTORE key
                if event.key == pygame.K_PAGEDOWN:
                    nmi = True

                # Also scan special keys
                elif event.key == pygame.K_F12:
                    signal = SIGNALS.RESET
                elif event.key == pygame.K_F11:
                    signal = SIGNALS.MONITOR
                elif event.key == pygame.K_F10:
                    # F10 -> paste text
                    try:
                        self.paste_buffer = list(pyperclip.paste())
                    except pyperclip.PyperclipException:
                        print(
                            "Can't paste: xsel or xclip system packages not found. "
                            "See https://pyperclip.readthedocs.io/en/latest/index.html#not-implemented-error"
                        )

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
        with open(filename, "rb") as f:
            return pickle.load(f)

    def restore(self, filename):  # TODO drop
        with open(filename, "rb") as f:
            self.cpu.A = pickle.load(f)
            self.cpu.X = pickle.load(f)
            self.cpu.Y = pickle.load(f)
            self.cpu.PC = pickle.load(f)
            self.cpu.SP = pickle.load(f)
            self.cpu.F = pickle.load(f)

            # Memory can not be loaded directly as it is referenced
            self.memory.set_slice(0, pickle.load(f))

    def save(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self, f)

    def load(self, filename, base, format_cbm=False):
        with open(filename, "rb") as f:
            # First two bytes are base address for loading into memory (little endian)
            lo, hi = f.read(2)
            if format_cbm:
                base = hi << 8 | lo
            data = f.read()
        for i, byte in enumerate(data):
            self.memory[base + i] = byte
        return base

    def set_datassette_button_status(self, status: bool):
        """
        Set bit #5 of address $01
        status True (PLAY|REC|FFWD|REW is pressed) -> clear bit
        status False (STOP has been pressed) -> set bit
        """
        # Bypass normal memory write, this is hardwired
        if status:
            self.memory[0x01] &= 0b11101111
        else:
            self.memory[0x01] |= 0b00010000

    def screendump(self) -> str:
        dump = ""
        base = self.screen.video_matrix_base_address
        data = self.memory.get_slice(base, base + 1000)
        data_char = [SCREEN_CHARCODE.get(x % 128, ".") for x in data]
        for row in range(25):
            dump += "".join(data_char[row * 40 : (row + 1) * 40 - 1]) + "\n"
        return dump


def DefaultMachine() -> Machine:
    from config import ROMS_FOLDER

    roms = hardware.roms.ROMS(ROMS_FOLDER)
    memory = hardware.memory.Memory(65536, roms)
    return Machine(
        memory,
        hardware.cpu.CPU(memory),
        hardware.screen.RasterScreen(memory),
        hardware.cia.CIA_A(memory),
    )
