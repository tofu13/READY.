from time import perf_counter

import pygame

from .constants import IRQ_RATE, PETSCII, BITVALUES


class CIA:
    def __init__(self, memory):
        self.memory = memory
        self.timer_A = 0x0000
        self.timer_B = 0x0000

        self.timer_A_latch = 0x0000
        self.timer_B_latch = 0x0000

        self.timer_A_start: bool = False
        self.timer_B_start: bool = False

        self.timer_A_underflow: bool = False
        self.timer_A_restart_after_underflow: bool = False

        self.timer_B_underflow: bool = False
        self.timer_B_restart_after_underflow: bool = False

        self.tod_zero = perf_counter()

    def step(self):
        if self.timer_A_start:
            self.timer_A -= 1
            if self.timer_A < 0:
                self.timer_A_underflow = True
                if self.timer_A_restart_after_underflow:
                    self.timer_A_load()
                else:
                    self.timer_A_start = False

    def timer_A_load(self):
        # self.timer_A_underflow = False
        self.timer_A = self.timer_A_latch

    @property
    def timer_A_lo(self):
        return self.timer_A % 256

    @property
    def timer_A_hi(self):
        return self.timer_A // 256

    @property
    def timer_B_lo(self):
        return self.timer_B % 256

    @property
    def timer_B_hi(self):
        return self.timer_B // 256

    @property
    def irq_occured(self) -> bool:
        return self.timer_A_underflow or self.timer_B_underflow  # TODO

    @property
    def tod(self) -> tuple:
        """
        TOD value
        :return: tuple (10th sec, sec, min, hours)
        """
        tod = perf_counter() - self.tod_zero
        int_tod = int(tod)
        return (
            int_tod // 3600 % 24,
            int_tod % 3600 // 60,
            int_tod % 60,
            int((tod - int_tod) * 10),
        )


class CIA_A(CIA):
    def __init__(self, memory):
        super().__init__(memory)
        self.pipe = None
        self.keyboard_row = 0
        self.keyboard_col = 0

        self.memory.read_watchers.append((0xDC00, 0xDCFF, self.get_registers))
        self.memory.write_watchers.append((0xDC00, 0xDCFF, self.set_registers))
        self.irq_delay = 1.0 / IRQ_RATE

    def step(self):
        """
        Execute CIA stuff
        :return: signals [irq, nmi, reset, quit]
        """
        super().step()
        return self.irq_occured

    def get_registers(self, address, value):
        if address == 0xDC01:
            # pygame.event.get()  # Unused?
            pygame.event.pump()
            keypressed = list(pygame.key.get_pressed())
            if not any(keypressed):
                # Shortcut
                return 0xFF
            elif keypressed[pygame.KSCAN_RALT]:
                # Ignore keyboard commands via RALT
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
        elif address == 0xDC04:
            return self.timer_A % 256
        elif address == 0xDC05:
            return self.timer_A // 256
        elif address == 0xDC06:
            return self.timer_B % 256
        elif address == 0xDC07:
            return self.timer_B // 256

        elif address == 0xDC08:
            return self.tod[3]
        elif address == 0xDC09:
            secs = self.tod[2]
            return (secs // 10) * 16 + secs % 10
        elif address == 0xDC0A:
            mins = self.tod[1]
            return (mins // 10) * 16 + mins % 10
        elif address == 0xDC0B:
            # Bit 0..3: Single hours in BCD-format ($0-$9)
            # Bit 4..6: Ten hours in BCD-format ($0-$5)
            # Bit 7: Differentiation AM/PM, 0=AM, 1=PM
            # Writing into this register stops TOD, until register 8 (TOD 10THS) will be read.
            hours = self.tod[0]
            return (hours > 12) * 128 + (hours % 12 // 10) * 16 + hours % 10

        elif address == 0xDC0D:
            # Bit 0: 1 = Underflow Timer A
            # Bit 1: 1 = Underflow Timer B
            # Bit 2: 1 = Time of day and alarm time is equal
            # Bit 3: 1 = SDR full or empty, so full byte was transferred, depending of operating mode serial bus
            # Bit 4: 1 = IRQ Signal occured at FLAG-pin (cassette port Data input, serial bus SRQ IN)
            # Bit 5..6: always 0
            # Bit 7: 1 = IRQ An interrupt occured, so at least one bit of INT MASK and INT DATA is set in both registers.
            result = sum(
                bit * weigth
                for bit, weigth in zip(
                    (
                        self.timer_A_underflow,
                        self.timer_B_underflow,
                        0,  # TODO
                        0,  # TODO
                        0,  # TODO
                        0,
                        0,
                        self.irq_occured,
                    ),
                    BITVALUES
                )
            )
            # Flags will be cleared after reading the register!
            self.timer_A_underflow = False
            self.timer_B_underflow = False
            return result
        return value

    def set_registers(self, address, value):
        if address != 0xDC00:
            print(f"Cia write {address:04X} {value:02X}")
        if address == 0xDC04:
            "Set lo byte of timer_A"
            self.timer_A_latch = self.timer_A_latch // 256 + value
        elif address == 0xDC05:
            "Set hi byte of timer_A"
            self.timer_A_latch = value * 256 + self.timer_A_latch % 256
        elif address == 0xDC0D:
            source = bool(value & 0b10000000)
        elif address == 0xDC0E:
            # Bit 0: 0 = Stop timer; 1 = Start timer
            # Bit 1: 1 = Indicates a timer underflow at port B in bit 6.
            # Bit 2: 0 = Through a timer overflow, bit 6 of port B will get high for one cycle , 1 = Through a timer underflow, bit 6 of port B will be inverted
            # Bit 3: 0 = Timer-restart after underflow (latch will be reloaded), 1 = Timer stops after underflow.
            # Bit 4: 1 = Load latch into the timer once.
            # Bit 5: 0 = Timer counts system cycles, 1 = Timer counts positive slope at CNT-pin
            # Bit 6: Direction of the serial shift register, 0 = SP-pin is input (read), 1 = SP-pin is output (write)
            # Bit 7: Real Time Clock, 0 = 60 Hz, 1 = 50 Hz

            self.timer_A_start = bool(value & 0x01)
            self.timer_A_restart_after_underflow = not bool(value & 0b1000)
            print(f"A {'start' if self.timer_A_start else 'stop'}")
            if value & 0b00010000:
                self.timer_A_load()


class CIA_B(CIA):
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
