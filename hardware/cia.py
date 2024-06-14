from time import perf_counter

import pygame

from .constants import BITVALUES


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

    def clock(self, *args):
        if self.timer_A_start:
            self.timer_A -= 1
            if self.timer_A < 0:
                self.timer_A_underflow = True
                if self.timer_A_restart_after_underflow:
                    self.timer_A_load()
                else:
                    self.timer_A = 0  # Unsure which value to set
                    self.timer_A_start = False

    def timer_A_load(self):
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

        self.keys_pressed = set()

    def clock(self, keys_pressed: set):
        """
        Execute CIA stuff
        :return: signals [irq, nmi, reset, quit]
        """
        # Save key pressed
        self.keys_pressed = keys_pressed

        super().clock()
        return self.irq_occured

    def get_registers(self, address, value):
        # Registers repeated every 0x10
        address &= 0x0F
        if address == 0x01:
            if not self.keys_pressed:
                # Shortcut
                return 0xFF

            keys_pressed = self.keys_pressed.copy()

            if pygame.K_RCTRL in keys_pressed:
                # Ignore keyboard commands via RCTRL
                return 0xFF
            elif pygame.K_UP in keys_pressed:
                # Emulate SHIFT+DOWN
                keys_pressed.update({pygame.K_LSHIFT, pygame.K_DOWN})
            elif pygame.K_LEFT in keys_pressed:
                # Emulate SHIFT+RIGHT
                keys_pressed.update({pygame.K_LSHIFT, pygame.K_RIGHT})
            elif pygame.K_INSERT in keys_pressed:
                # Emulate INS (bonus)
                keys_pressed.update({pygame.K_LSHIFT, pygame.K_DELETE})
            elif {pygame.K_LSHIFT, pygame.K_LESS}.issubset(keys_pressed):
                # Emulate >
                # Keep shift
                keys_pressed.update({pygame.K_PERIOD})
            elif pygame.K_LESS in keys_pressed:
                # Emulate <
                keys_pressed.update({pygame.K_LSHIFT, pygame.K_COMMA})
            elif {pygame.K_RALT, 242}.issubset(keys_pressed):
                # Emulate @
                keys_pressed.difference_update({pygame.K_RALT, 242})
                keys_pressed.update({pygame.K_AT})
            elif {pygame.K_RALT, 224}.issubset(keys_pressed):
                # Emulate #
                keys_pressed.difference_update({pygame.K_RALT, 224})
                keys_pressed.update({pygame.K_LSHIFT, pygame.K_3})
            elif {pygame.K_RALT, 232}.issubset(keys_pressed):
                # Emulate [
                keys_pressed.difference_update({pygame.K_RALT, 232})
                keys_pressed.update({pygame.K_LSHIFT, pygame.K_COLON})
            elif {pygame.K_RALT, pygame.K_PLUS}.issubset(keys_pressed):
                # Emulate ]
                keys_pressed.difference_update({pygame.K_RALT, pygame.K_PLUS})
                keys_pressed.update({pygame.K_LSHIFT, pygame.K_SEMICOLON})

            elif {pygame.K_LSHIFT, pygame.K_QUOTE}.issubset(keys_pressed):
                # Emulate ?
                # Keep shift
                keys_pressed.update({pygame.K_SLASH})
            elif {pygame.K_LSHIFT, pygame.K_0}.issubset(keys_pressed):
                # Emulate =
                # Keep shift
                keys_pressed.update({pygame.K_EQUALS})
            elif {pygame.K_LSHIFT, pygame.K_3}.issubset(keys_pressed):
                # Emulate £ through pygame.CURRENCYUNIT
                keys_pressed.remove(pygame.K_LSHIFT)
                keys_pressed.update({pygame.K_CURRENCYUNIT})
            elif pygame.K_QUOTE in keys_pressed:
                # Emulate '
                keys_pressed.update({pygame.K_LSHIFT, pygame.K_7})
            elif {pygame.K_LSHIFT, pygame.K_COMMA}.issubset(keys_pressed):
                # Emulate ;
                keys_pressed.remove(pygame.K_LSHIFT)
                keys_pressed.update({pygame.K_SEMICOLON})
            elif {pygame.K_LSHIFT, pygame.K_PERIOD}.issubset(keys_pressed):
                # Emulate :
                keys_pressed.remove(pygame.K_LSHIFT)
                keys_pressed.update({pygame.K_COLON})
            elif {pygame.K_LSHIFT, pygame.K_PLUS}.issubset(keys_pressed):
                # Emulate *
                keys_pressed.remove(pygame.K_LSHIFT)
                keys_pressed.update({pygame.K_ASTERISK})

            col = 0xFF - self.memory.read(0xDC00)  # Invert bits
            k = 0x00

            if col & 0b00000001:
                if pygame.K_DELETE in keys_pressed or pygame.K_BACKSPACE in keys_pressed:
                    k |= 0x01
                if pygame.K_RETURN in keys_pressed or pygame.K_KP_ENTER in keys_pressed:
                    k |= 0x02
                if pygame.K_RIGHT in keys_pressed:
                    k |= 0x04
                if pygame.K_F7 in keys_pressed:
                    k |= 0x08
                if pygame.K_F1 in keys_pressed:
                    k |= 0x10
                if pygame.K_F3 in keys_pressed:
                    k |= 0x20
                if pygame.K_F5 in keys_pressed:
                    k |= 0x40
                if pygame.K_DOWN in keys_pressed:
                    k |= 0x80

            if col & 0b00000010:
                if pygame.K_3 in keys_pressed or pygame.K_KP3 in keys_pressed:
                    k |= 0x01
                if pygame.K_w in keys_pressed:
                    k |= 0x02
                if pygame.K_a in keys_pressed:
                    k |= 0x04
                if pygame.K_4 in keys_pressed or pygame.K_KP4 in keys_pressed:
                    k |= 0x08
                if pygame.K_z in keys_pressed:
                    k |= 0x10
                if pygame.K_s in keys_pressed:
                    k |= 0x20
                if pygame.K_e in keys_pressed:
                    k |= 0x40
                if pygame.K_LSHIFT in keys_pressed:
                    k |= 0x80

            if col & 0b00000100:
                if pygame.K_5 in keys_pressed or pygame.K_KP5 in keys_pressed:
                    k |= 0x01
                if pygame.K_r in keys_pressed:
                    k |= 0x02
                if pygame.K_d in keys_pressed:
                    k |= 0x04
                if pygame.K_6 in keys_pressed or pygame.K_KP6 in keys_pressed:
                    k |= 0x08
                if pygame.K_c in keys_pressed:
                    k |= 0x10
                if pygame.K_f in keys_pressed:
                    k |= 0x20
                if pygame.K_t in keys_pressed:
                    k |= 0x40
                if pygame.K_x in keys_pressed:
                    k |= 0x80

            if col & 0b00001000:
                if pygame.K_7 in keys_pressed or pygame.K_KP7 in keys_pressed:
                    k |= 0x01
                if pygame.K_y in keys_pressed:
                    k |= 0x02
                if pygame.K_g in keys_pressed:
                    k |= 0x04
                if pygame.K_8 in keys_pressed or pygame.K_KP8 in keys_pressed:
                    k |= 0x08
                if pygame.K_b in keys_pressed:
                    k |= 0x10
                if pygame.K_h in keys_pressed:
                    k |= 0x20
                if pygame.K_u in keys_pressed:
                    k |= 0x40
                if pygame.K_v in keys_pressed:
                    k |= 0x80

            if col & 0b00010000:
                if pygame.K_9 in keys_pressed or pygame.K_KP9 in keys_pressed:
                    k |= 0x01
                if pygame.K_i in keys_pressed:
                    k |= 0x02
                if pygame.K_j in keys_pressed:
                    k |= 0x04
                if pygame.K_0 in keys_pressed or pygame.K_KP0 in keys_pressed:
                    k |= 0x08
                if pygame.K_m in keys_pressed:
                    k |= 0x10
                if pygame.K_k in keys_pressed:
                    k |= 0x20
                if pygame.K_o in keys_pressed:
                    k |= 0x40
                if pygame.K_n in keys_pressed:
                    k |= 0x80

            if col & 0b00100000:
                if pygame.K_PLUS in keys_pressed or pygame.K_KP_PLUS in keys_pressed:
                    k |= 0x01  # +
                if pygame.K_p in keys_pressed:
                    k |= 0x02
                if pygame.K_l in keys_pressed:
                    k |= 0x04
                if pygame.K_MINUS in keys_pressed or pygame.K_KP_MINUS in keys_pressed:
                    k |= 0x08  # -
                if pygame.K_PERIOD in keys_pressed or pygame.K_KP_PERIOD in keys_pressed:
                    k |= 0x10  # .
                if pygame.K_COLON in keys_pressed:
                    k |= 0x20  # :
                if pygame.K_AT in keys_pressed:
                    k |= 0x40  # @
                if pygame.K_COMMA in keys_pressed:
                    k |= 0x80  # ,

            if col & 0b01000000:
                if pygame.K_CURRENCYUNIT in keys_pressed:
                    k |= 0x01  # £
                if pygame.K_ASTERISK in keys_pressed or pygame.K_KP_MULTIPLY in keys_pressed:
                    k |= 0x02  # *
                if pygame.K_SEMICOLON in keys_pressed:
                    k |= 0x04  # ;
                if pygame.K_HOME in keys_pressed:
                    k |= 0x08
                if pygame.K_RSHIFT in keys_pressed:
                    k |= 0x10
                if pygame.K_EQUALS in keys_pressed:
                    k |= 0x20  # =
                if 232 in keys_pressed:
                    k |= 0x40  # Up arrow / pi
                if pygame.K_SLASH in keys_pressed or pygame.K_KP_DIVIDE in keys_pressed:
                    k |= 0x80  # /

            if col & 0b10000000:
                if pygame.K_1 in keys_pressed or pygame.K_KP1 in keys_pressed:
                    k |= 0x01
                if pygame.K_BACKSLASH in keys_pressed:
                    k |= 0x02
                if pygame.K_LCTRL in keys_pressed:
                    k |= 0x04
                if pygame.K_2 in keys_pressed or pygame.K_KP2 in keys_pressed:
                    k |= 0x08
                if pygame.K_SPACE in keys_pressed:
                    k |= 0x10
                if pygame.K_LALT in keys_pressed:
                    k |= 0x20  # C= KEY
                if pygame.K_q in keys_pressed:
                    k |= 0x40
                if pygame.K_ESCAPE in keys_pressed:
                    k |= 0x80  # RUN STOP

            return 255 - k
        elif address == 0x04:
            return self.timer_A % 256
        elif address == 0x05:
            return self.timer_A // 256
        elif address == 0x06:
            return self.timer_B % 256
        elif address == 0x07:
            return self.timer_B // 256

        elif address == 0x08:
            return self.tod[3]
        elif address == 0x09:
            secs = self.tod[2]
            return (secs // 10) * 16 + secs % 10
        elif address == 0x0A:
            mins = self.tod[1]
            return (mins // 10) * 16 + mins % 10
        elif address == 0x0B:
            # Bit 0..3: Single hours in BCD-format ($0-$9)
            # Bit 4..6: Ten hours in BCD-format ($0-$5)
            # Bit 7: Differentiation AM/PM, 0=AM, 1=PM
            # Writing into this register stops TOD, until register 8 (TOD 10THS) will be read.
            hours = self.tod[0]
            return (hours > 12) * 128 + (hours % 12 // 10) * 16 + hours % 10

        elif address == 0x0D:
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
            # TODO: set interrupt sources
            source = bool(value & 0b10000000)
            source  # Stub -- remove

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

    def clock(self):
        pass

    def get_registers(self, address, value):
        pass

    def set_registers(self, address, value):
        pass
