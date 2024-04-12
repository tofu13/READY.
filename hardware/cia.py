from time import perf_counter

import pygame

from .constants import IRQ_RATE, BITVALUES


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

    def step(self, *args):
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

        self.keys_pressed = set()

    def step(self, keys_pressed: set):
        """
        Execute CIA stuff
        :return: signals [irq, nmi, reset, quit]
        """
        self.keys_pressed = keys_pressed.copy()
        super().step()
        return self.irq_occured

    def get_registers(self, address, value):
        if address == 0xDC01:
            # pygame.event.get()  # Unused?
            # pygame.event.pump()
            # keypressed = self.keys_pressed
            if not self.keys_pressed:
                # Shortcut
                return 0xFF
            elif pygame.K_RCTRL in self.keys_pressed:
                # Ignore keyboard commands via RCTRL
                return 0xFF
            elif pygame.K_UP in self.keys_pressed:
                # Emulate SHIFT+DOWN
                self.keys_pressed.update({pygame.K_LSHIFT, pygame.K_DOWN})
            elif pygame.K_LEFT in self.keys_pressed:
                # Emulate SHIFT+RIGHT
                self.keys_pressed.update({pygame.K_LSHIFT, pygame.K_RIGHT})
            elif pygame.K_INSERT in self.keys_pressed:
                # Emulate INS (bonus)
                self.keys_pressed.update({pygame.K_LSHIFT, pygame.K_DELETE})
            elif {pygame.K_LSHIFT, pygame.K_LESS}.issubset(self.keys_pressed):
                # Emulate >
                # Keep shift
                self.keys_pressed.update({pygame.K_PERIOD})
            elif pygame.K_LESS in self.keys_pressed:
                # Emulate <
                self.keys_pressed.update({pygame.K_LSHIFT, pygame.K_COMMA})
            elif {pygame.K_RALT, 242}.issubset(self.keys_pressed):
                # Emulate @
                self.keys_pressed.difference_update({pygame.K_RALT, 242})
                self.keys_pressed.update({pygame.K_AT})
            elif {pygame.K_RALT, 224}.issubset(self.keys_pressed):
                # Emulate #
                self.keys_pressed.difference_update({pygame.K_RALT, 224})
                self.keys_pressed.update({pygame.K_LSHIFT, pygame.K_3})
            elif {pygame.K_RALT, 232}.issubset(self.keys_pressed):
                # Emulate [
                self.keys_pressed.difference_update({pygame.K_RALT, 232})
                self.keys_pressed.update({pygame.K_LSHIFT, pygame.K_COLON})
            elif {pygame.K_RALT, pygame.K_PLUS}.issubset(self.keys_pressed):
                # Emulate ]
                self.keys_pressed.difference_update({pygame.K_RALT, pygame.K_PLUS})
                self.keys_pressed.update({pygame.K_LSHIFT, pygame.K_SEMICOLON})

            elif {pygame.K_LSHIFT, pygame.K_QUOTE}.issubset(self.keys_pressed):
                # Emulate ?
                # Keep shift
                self.keys_pressed.update({pygame.K_SLASH})
            elif {pygame.K_LSHIFT, pygame.K_0}.issubset(self.keys_pressed):
                # Emulate =
                # Keep shift
                self.keys_pressed.update({pygame.K_EQUALS})
            elif {pygame.K_LSHIFT, pygame.K_3}.issubset(self.keys_pressed):
                # Emulate £ through pygame.CURRENCYUNIT
                self.keys_pressed.remove(pygame.K_LSHIFT)
                self.keys_pressed.update({pygame.K_CURRENCYUNIT})
            elif pygame.K_QUOTE in self.keys_pressed:
                # Emulate '
                self.keys_pressed.update({pygame.K_LSHIFT, pygame.K_7})
            elif {pygame.K_LSHIFT, pygame.K_COMMA}.issubset(self.keys_pressed):
                # Emulate ;
                self.keys_pressed.remove(pygame.K_LSHIFT)
                self.keys_pressed.update({pygame.K_SEMICOLON})
            elif {pygame.K_LSHIFT, pygame.K_PERIOD}.issubset(self.keys_pressed):
                # Emulate :
                self.keys_pressed.remove(pygame.K_LSHIFT)
                self.keys_pressed.update({pygame.K_COLON})
            elif {pygame.K_LSHIFT, pygame.K_PLUS}.issubset(self.keys_pressed):
                # Emulate *
                self.keys_pressed.remove(pygame.K_LSHIFT)
                self.keys_pressed.update({pygame.K_ASTERISK})

            col = 0xFF - self.memory[0xDC00]  # Invert bits
            k = 0x00

            if col & 0b00000001:
                if pygame.K_DELETE in self.keys_pressed or pygame.K_BACKSPACE in self.keys_pressed:
                    k |= 0x01
                if pygame.K_RETURN in self.keys_pressed or pygame.K_KP_ENTER in self.keys_pressed:
                    k |= 0x02
                if pygame.K_RIGHT in self.keys_pressed:
                    k |= 0x04
                if pygame.K_F7 in self.keys_pressed:
                    k |= 0x08
                if pygame.K_F1 in self.keys_pressed:
                    k |= 0x10
                if pygame.K_F3 in self.keys_pressed:
                    k |= 0x20
                if pygame.K_F5 in self.keys_pressed:
                    k |= 0x40
                if pygame.K_DOWN in self.keys_pressed:
                    k |= 0x80

            if col & 0b00000010:
                if pygame.K_3 in self.keys_pressed or pygame.K_KP3 in self.keys_pressed:
                    k |= 0x01
                if pygame.K_w in self.keys_pressed:
                    k |= 0x02
                if pygame.K_a in self.keys_pressed:
                    k |= 0x04
                if pygame.K_4 in self.keys_pressed or pygame.K_KP4 in self.keys_pressed:
                    k |= 0x08
                if pygame.K_z in self.keys_pressed:
                    k |= 0x10
                if pygame.K_s in self.keys_pressed:
                    k |= 0x20
                if pygame.K_e in self.keys_pressed:
                    k |= 0x40
                if pygame.K_LSHIFT in self.keys_pressed:
                    k |= 0x80

            if col & 0b00000100:
                if pygame.K_5 in self.keys_pressed or pygame.K_KP5 in self.keys_pressed:
                    k |= 0x01
                if pygame.K_r in self.keys_pressed:
                    k |= 0x02
                if pygame.K_d in self.keys_pressed:
                    k |= 0x04
                if pygame.K_6 in self.keys_pressed or pygame.K_KP6 in self.keys_pressed:
                    k |= 0x08
                if pygame.K_c in self.keys_pressed:
                    k |= 0x10
                if pygame.K_f in self.keys_pressed:
                    k |= 0x20
                if pygame.K_t in self.keys_pressed:
                    k |= 0x40
                if pygame.K_x in self.keys_pressed:
                    k |= 0x80

            if col & 0b00001000:
                if pygame.K_7 in self.keys_pressed or pygame.K_KP7 in self.keys_pressed:
                    k |= 0x01
                if pygame.K_y in self.keys_pressed:
                    k |= 0x02
                if pygame.K_g in self.keys_pressed:
                    k |= 0x04
                if pygame.K_8 in self.keys_pressed or pygame.K_KP8 in self.keys_pressed:
                    k |= 0x08
                if pygame.K_b in self.keys_pressed:
                    k |= 0x10
                if pygame.K_h in self.keys_pressed:
                    k |= 0x20
                if pygame.K_u in self.keys_pressed:
                    k |= 0x40
                if pygame.K_v in self.keys_pressed:
                    k |= 0x80

            if col & 0b00010000:
                if pygame.K_9 in self.keys_pressed or pygame.K_KP9 in self.keys_pressed:
                    k |= 0x01
                if pygame.K_i in self.keys_pressed:
                    k |= 0x02
                if pygame.K_j in self.keys_pressed:
                    k |= 0x04
                if pygame.K_0 in self.keys_pressed or pygame.K_KP0 in self.keys_pressed:
                    k |= 0x08
                if pygame.K_m in self.keys_pressed:
                    k |= 0x10
                if pygame.K_k in self.keys_pressed:
                    k |= 0x20
                if pygame.K_o in self.keys_pressed:
                    k |= 0x40
                if pygame.K_n in self.keys_pressed:
                    k |= 0x80

            if col & 0b00100000:
                if pygame.K_PLUS in self.keys_pressed or pygame.K_KP_PLUS in self.keys_pressed:
                    k |= 0x01  # +
                if pygame.K_p in self.keys_pressed:
                    k |= 0x02
                if pygame.K_l in self.keys_pressed:
                    k |= 0x04
                if pygame.K_MINUS in self.keys_pressed or pygame.K_KP_MINUS in self.keys_pressed:
                    k |= 0x08  # -
                if pygame.K_PERIOD in self.keys_pressed or pygame.K_KP_PERIOD in self.keys_pressed:
                    k |= 0x10  # .
                if pygame.K_COLON in self.keys_pressed:
                    k |= 0x20  # :
                if pygame.K_AT in self.keys_pressed:
                    k |= 0x40  # @
                if pygame.K_COMMA in self.keys_pressed:
                    k |= 0x80  # ,

            if col & 0b01000000:
                if pygame.K_CURRENCYUNIT in self.keys_pressed:
                    k |= 0x01  # £
                if pygame.K_ASTERISK in self.keys_pressed or pygame.K_KP_MULTIPLY in self.keys_pressed:
                    k |= 0x02  # *
                if pygame.K_SEMICOLON in self.keys_pressed:
                    k |= 0x04  # ;
                if pygame.K_HOME in self.keys_pressed:
                    k |= 0x08
                if pygame.K_RSHIFT in self.keys_pressed:
                    k |= 0x10
                if pygame.K_EQUALS in self.keys_pressed:
                    k |= 0x20  # =
                if 232 in self.keys_pressed:
                    k |= 0x40  # Up arrow / pi
                if pygame.K_SLASH in self.keys_pressed or pygame.K_KP_DIVIDE in self.keys_pressed:
                    k |= 0x80  # /

            if col & 0b10000000:
                if pygame.K_1 in self.keys_pressed or pygame.K_KP1 in self.keys_pressed:
                    k |= 0x01
                if pygame.K_BACKSLASH in self.keys_pressed:
                    k |= 0x02
                if pygame.K_LCTRL in self.keys_pressed:
                    k |= 0x04
                if pygame.K_2 in self.keys_pressed or pygame.K_KP2 in self.keys_pressed:
                    k |= 0x08
                if pygame.K_SPACE in self.keys_pressed:
                    k |= 0x10
                if pygame.K_LALT in self.keys_pressed:
                    k |= 0x20  # C= KEY
                if pygame.K_q in self.keys_pressed:
                    k |= 0x40
                if pygame.K_ESCAPE in self.keys_pressed:
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
            # Bit 7: 1 = IRQ An interrupt occured, so at least one bit of INT MASK and INT DATA is set in both registers
            result = sum(
                bit * weight
                for bit, weight in zip(
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
            # Bit 2: 0 = Through a timer overflow, bit 6 of port B will get high for one cycle ,
            #        1 = Through a timer underflow, bit 6 of port B will be inverted
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
