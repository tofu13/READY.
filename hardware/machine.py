import pickle

import pygame.event
import pyperclip

from hardware.constants import PETSCII, TRANSPARENT_COLOR, VIDEO_SIZE
from hardware import monitor


class Machine:
    def __init__(self, memory, cpu, screen, ciaA):

        self.memory = memory
        self.cpu = cpu
        self.screen = screen
        self.ciaA = ciaA

        self.monitor = monitor.Monitor(self)
        self.monitor_active = False

        # Default processor I/O
        self.memory[0] = 47
        # Default processor ports  (HIRAM, LORAM, CHARGEN = 1)
        self.memory[1] = 55
        # Assert datassette stopped
        self.set_datassette_button_status(False)

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

        self.display.set_colorkey(TRANSPARENT_COLOR)
        self.CAPTION = "Commodore 64 (Text) {:.1f} FPS"

        # pygame.display.set_caption(self.CAPTION)

        self.clock = pygame.time.Clock()
        self._last_fps = 0

        self.paste_buffer = []

    def run(self, address):
        """
        Main process loop
        :param address: address to run from
        """

        # Setup
        self.cpu.F['B'] = 0
        self.cpu.PC = address

        signal = None
        nmi = False

        while True:
            # Activate monitor on breakpoints
            if self.cpu.breakpoints:
                self.monitor_active |= self.cpu.PC in self.cpu.breakpoints
            if self.monitor_active:
                self.monitor_active = self.monitor.run()
                self.monitor_active = False

            # Run VIC-II cycle
            frame = self.screen.step()

            # Display complete frame
            if frame is not None:
                self.display.blit(frame, (0, 0))
                pygame.display.flip()
                # Get FPS
                self.clock.tick()  # Max 50 FPS
                if (current_ticks := pygame.time.get_ticks()) - self._last_fps > 1000:
                    pygame.display.set_caption(self.CAPTION.format(self.clock.get_fps()))
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

            # Execute current instruction
            self.cpu.step()

            # Run CIA A, handle interrupt if any
            if self.ciaA.step():
                self.cpu.irq()

            self._clock_counter += 1
            if self._clock_counter % 100000 == 0:
                signal, nmi = self.manage_events()

            if nmi:
                self.cpu.nmi()
                nmi = False

            if signal == "RESET":
                self.cpu.reset(PC=0xFCE2)
                signal = None
            elif signal == "MONITOR":
                self.monitor_active = True
                signal = None

        # BRK encountered, exit

    def manage_events(self):
        """
        Manage system events
        """
        signal = None
        nmi = False
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
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
                elif event.key == pygame.K_p and event.mod & pygame.KMOD_RALT:
                    # PLAY|REC|FFWD|REW is pressed on datassette
                    self.set_datassette_button_status(True)
                elif event.key == pygame.K_s and event.mod & pygame.KMOD_RALT:
                    # STOP is pressed on datassette
                    self.set_datassette_button_status(False)

            elif event.type == pygame.WINDOWCLOSE:
                pygame.quit()

        return signal, nmi

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
