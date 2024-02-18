from time import perf_counter

import pygame
import pyperclip

from .constants import IRQ_RATE, PETSCII


class CIAA:
    def __init__(self, memory):
        self.memory = memory
        self.pipe = None
        self.keyboard_row = 0
        self.keyboard_col = 0

        self.memory.read_watchers.append((0xDC00, 0xDCFF, self.get_registers))
        self.memory.write_watchers.append((0xDC00, 0xDCFF, self.set_registers))
        self.irq_delay = 1.0 / IRQ_RATE
        self.last_irq = perf_counter()

        self.paste_buffer = []

    def step(self):
        """
        Execute CIA stuff
        :return: signals [irq, nmi, reset, quit]
        """
        irq = False
        nmi = False
        signal = None

        # Generate time IRQ
        if (perf_counter() - self.last_irq) >= self.irq_delay:
            self.last_irq = perf_counter()
            irq = True

            # Scan RESTORE key for NMI
            # Note: use the same timing as interrupts: not accurate but close to reality
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_PAGEUP:
                        nmi = True
                    # Also scan special keys
                    if event.key == pygame.K_F12:
                        signal = "RESET"
                    if event.key == pygame.K_F11:
                        signal = "MONITOR"
                    if event.key == pygame.K_F10:
                        # F10 -> paste text
                        try:
                            self.paste_buffer = list(pyperclip.paste())
                        except pyperclip.PyperclipException:
                            print(
                                "Can't paste: xsel or xclip system packages not found. "
                                "See https://pyperclip.readthedocs.io/en/latest/index.html#not-implemented-error")
                if event.type == pygame.QUIT:
                    signal = "QUIT"

        if self.paste_buffer and self.memory[0xC6] == 0:
            # Inject char into empty keyboard buffer
            char = self.paste_buffer.pop(0)
            petscii_code = PETSCII.get(char.lower())
            if not petscii_code:
                print(f"WARNING: character {char} not in PETSCII")
            else:
                self.memory[0x277 + self.memory[0xC6]] = petscii_code
                # Update buffer length
                self.memory[0xC6] += 1

        return irq, nmi, signal

    def get_registers(self, address, value):
        if address == 0xDC01:
            pygame.event.get()
            keypressed = list(pygame.key.get_pressed())
            if not any(keypressed):
                # Shortcut
                return 0xFF
            elif keypressed[pygame.KSCAN_UP]:
                # Emulate SHIFT+DOWN
                keypressed[pygame.KSCAN_RSHIFT] = True
                keypressed[pygame.KSCAN_DOWN] = True
            elif keypressed[pygame.KSCAN_LEFT]:
                # Emulate SHIFT+RIGHT
                keypressed[pygame.KSCAN_RSHIFT] = True
                keypressed[pygame.KSCAN_RIGHT] = True

            col = 0xFF - self.memory[0xDC00]  # Invert bits
            k = 0x00

            if col & 0b00000001:
                if keypressed[pygame.KSCAN_DELETE] or keypressed[pygame.KSCAN_BACKSPACE]:
                    k |= 0x01
                if keypressed[pygame.KSCAN_RETURN] or keypressed[pygame.KSCAN_KP_ENTER]:
                    k |= 0x02
                if keypressed[pygame.KSCAN_RIGHT]:
                    k |= 0x04
                if keypressed[pygame.KSCAN_F7]:
                    k |= 0x08
                if keypressed[pygame.KSCAN_F1]:
                    k |= 0x10
                if keypressed[pygame.KSCAN_F3]:
                    k |= 0x20
                if keypressed[pygame.KSCAN_F5]:
                    k |= 0x40
                if keypressed[pygame.KSCAN_DOWN]:
                    k |= 0x80

            if col & 0b00000010:
                if keypressed[pygame.KSCAN_3] or keypressed[pygame.KSCAN_KP3]:
                    k |= 0x01
                if keypressed[pygame.KSCAN_W]:
                    k |= 0x02
                if keypressed[pygame.KSCAN_A]:
                    k |= 0x04
                if keypressed[pygame.KSCAN_4] or keypressed[pygame.KSCAN_KP4]:
                    k |= 0x08
                if keypressed[pygame.KSCAN_Z]:
                    k |= 0x10
                if keypressed[pygame.KSCAN_S]:
                    k |= 0x20
                if keypressed[pygame.KSCAN_E]:
                    k |= 0x40
                if keypressed[pygame.KSCAN_LSHIFT]:
                    k |= 0x80

            if col & 0b00000100:
                if keypressed[pygame.KSCAN_5] or keypressed[pygame.KSCAN_KP5]:
                    k |= 0x01
                if keypressed[pygame.KSCAN_R]:
                    k |= 0x02
                if keypressed[pygame.KSCAN_D]:
                    k |= 0x04
                if keypressed[pygame.KSCAN_6] or keypressed[pygame.KSCAN_KP6]:
                    k |= 0x08
                if keypressed[pygame.KSCAN_C]:
                    k |= 0x10
                if keypressed[pygame.KSCAN_F]:
                    k |= 0x20
                if keypressed[pygame.KSCAN_T]:
                    k |= 0x40
                if keypressed[pygame.KSCAN_X]:
                    k |= 0x80

            if col & 0b00001000:
                if keypressed[pygame.KSCAN_7] or keypressed[pygame.KSCAN_KP7]:
                    k |= 0x01
                if keypressed[pygame.KSCAN_Y]:
                    k |= 0x02
                if keypressed[pygame.KSCAN_G]:
                    k |= 0x04
                if keypressed[pygame.KSCAN_8] or keypressed[pygame.KSCAN_KP8]:
                    k |= 0x08
                if keypressed[pygame.KSCAN_B]:
                    k |= 0x10
                if keypressed[pygame.KSCAN_H]:
                    k |= 0x20
                if keypressed[pygame.KSCAN_U]:
                    k |= 0x40
                if keypressed[pygame.KSCAN_V]:
                    k |= 0x80

            if col & 0b00010000:
                if keypressed[pygame.KSCAN_9] or keypressed[pygame.KSCAN_KP9]:
                    k |= 0x01
                if keypressed[pygame.KSCAN_I]:
                    k |= 0x02
                if keypressed[pygame.KSCAN_J]:
                    k |= 0x04
                if keypressed[pygame.KSCAN_0] or keypressed[pygame.KSCAN_KP0]:
                    k |= 0x08
                if keypressed[pygame.KSCAN_M]:
                    k |= 0x10
                if keypressed[pygame.KSCAN_K]:
                    k |= 0x20
                if keypressed[pygame.KSCAN_O]:
                    k |= 0x40
                if keypressed[pygame.KSCAN_N]:
                    k |= 0x80

            if col & 0b00100000:
                if keypressed[pygame.KSCAN_MINUS] or keypressed[pygame.KSCAN_KP_PLUS]:
                    k |= 0x01  # +
                if keypressed[pygame.KSCAN_P]:
                    k |= 0x02
                if keypressed[pygame.KSCAN_L]:
                    k |= 0x04
                if keypressed[pygame.KSCAN_EQUALS] or keypressed[pygame.KSCAN_KP_MINUS]:
                    k |= 0x08  # -
                if keypressed[pygame.KSCAN_PERIOD] or keypressed[pygame.KSCAN_KP_PERIOD]:
                    k |= 0x10  # .
                if keypressed[pygame.KSCAN_SEMICOLON]:
                    k |= 0x20  # :
                if keypressed[pygame.KSCAN_LEFTBRACKET]:
                    k |= 0x40  # @
                if keypressed[pygame.KSCAN_COMMA]:
                    k |= 0x80  # ,

            if col & 0b01000000:
                if keypressed[pygame.KSCAN_INSERT]:
                    k |= 0x01  # £
                if keypressed[pygame.KSCAN_RIGHTBRACKET] or keypressed[pygame.KSCAN_KP_MULTIPLY]:
                    k |= 0x02  # *
                if keypressed[pygame.KSCAN_APOSTROPHE]:
                    k |= 0x04  # ;
                if keypressed[pygame.KSCAN_HOME]:
                    k |= 0x08
                if keypressed[pygame.KSCAN_RSHIFT]:
                    k |= 0x10
                if keypressed[pygame.KSCAN_BACKSLASH]:
                    k |= 0x20  # =
                if keypressed[pygame.KSCAN_END]:
                    k |= 0x40  # Up arrow / pi
                if keypressed[pygame.KSCAN_SLASH] or keypressed[pygame.KSCAN_KP_DIVIDE]:
                    k |= 0x80  # /

            if col & 0b10000000:
                if keypressed[pygame.KSCAN_1] or keypressed[pygame.KSCAN_KP1]:
                    k |= 0x01
                if keypressed[pygame.KSCAN_GRAVE]:
                    k |= 0x02
                if keypressed[pygame.KSCAN_LCTRL]:
                    k |= 0x04
                if keypressed[pygame.KSCAN_2] or keypressed[pygame.KSCAN_KP2]:
                    k |= 0x08
                if keypressed[pygame.KSCAN_SPACE]:
                    k |= 0x10
                if keypressed[pygame.KSCAN_LALT]:
                    k |= 0x20  # C= KEY
                if keypressed[pygame.KSCAN_Q]:
                    k |= 0x40
                if keypressed[pygame.KSCAN_ESCAPE]:
                    k |= 0x80  # RUN STOP

            return 255 - k
        elif address == 0xDC0D:
            return 0x80
        return value

    def set_registers(self, address, value):
        # print (f"Cia write {address:04X} {value:02X}")
        # self.memory[address] = value
        pass


class CIAB:
    memory = None

    def init(self):
        self.memory.read_watchers.append((0xDD00, 0xDDFF, self.get_registers))
        self.memory.write_watchers.append((0xDD00, 0xDDFF, self.set_registers))

    def step(self):
        pass

    def get_registers(self, address, value):
        pass

    def set_registers(self, address, value):
        pass
