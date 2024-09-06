from time import perf_counter

from .constants import BITVALUES, KEYBOARD


class CIA:
    __slots__ = [
        "memory",
        "bus",
        "timer_A",
        "timer_B",
        "timer_A_latch",
        "timer_B_latch",
        "timer_A_start",
        "timer_B_start",
        "timer_A_underflow",
        "timer_A_restart_after_underflow",
        "timer_B_underflow",
        "timer_B_restart_after_underflow",
        "tod_zero",
    ]

    def __init__(self, memory, bus):
        self.memory = memory
        self.bus = bus
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

    def clock(self):
        # see note on derived classes
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
    __slots__ = ["pipe", "keys_pressed"]

    def __init__(self, memory, bus):
        super().__init__(memory, bus)

        self.memory.read_watchers.append((0xDC00, 0xDCFF, self.get_registers))
        self.memory.write_watchers.append((0xDC00, 0xDCFF, self.set_registers))

        self.keys_pressed = set()

    def clock(self, keys_pressed: set):
        """
        Execute CIA stuff
        :return: signals [irq, nmi, reset, quit]
        """
        # Save keys pressed
        self.keys_pressed = keys_pressed

        # super() is very slow :(
        # CIA.clock(self) is slow
        # Since practicality beats purity, code duplication here
        if self.timer_A_start:
            self.timer_A -= 1
            if self.timer_A < 0:
                self.timer_A_underflow = True
                if self.timer_A_restart_after_underflow:
                    self.timer_A_load()
                else:
                    self.timer_A = 0  # Unsure which value to set
                    self.timer_A_start = False

        if self.irq_occured:
            self.bus.irq_set("timer_A")

    def get_registers(self, address):
        # Registers repeated every 0x10
        match address & 0x0F:
            case 0x01:
                if not self.keys_pressed:
                    # Shortcut
                    return 0xFF
                col = 255 - self.memory[0xDC00]  # Invert bits

                c64keys = []
                keys_pressed = self.keys_pressed.copy()
                for kmap, val in KEYBOARD.items():
                    if kmap.issubset(keys_pressed):
                        c64keys.extend([k.value for k in val])
                        keys_pressed.difference_update(kmap)
                        # break

                k = 0x00
                for k_col, k_row in c64keys:
                    if col & k_col:
                        k |= k_row
                return 255 - k
            case 0x04:
                return self.timer_A % 256
            case 0x05:
                return self.timer_A // 256
            case 0x06:
                return self.timer_B % 256
            case 0x07:
                return self.timer_B // 256
            case 0x08:
                return self.tod[3]
            case 0x09:
                secs = self.tod[2]
                return (secs // 10) * 16 + secs % 10
            case 0x0A:
                mins = self.tod[1]
                return (mins // 10) * 16 + mins % 10
            case 0x0B:
                # Bit 0..3: Single hours in BCD-format ($0-$9)
                # Bit 4..6: Ten hours in BCD-format ($0-$5)
                # Bit 7: Differentiation AM/PM, 0=AM, 1=PM
                # Writing into this register stops TOD, until register 8 (TOD 10THS) will be read.
                hours = self.tod[0]
                return (hours > 12) * 128 + (hours % 12 // 10) * 16 + hours % 10
            case 0x0D:
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
                        BITVALUES,
                    )
                )
                # Flags will be cleared after reading the register!
                self.timer_A_underflow = False
                self.timer_B_underflow = False
                self.bus.irq_clear("timer_A")

                return result
        return 0

    def set_registers(self, address, value):
        match address & 0x0F:
            case 0x04:
                "Set lo byte of timer_A"
                self.timer_A_latch = self.timer_A_latch // 256 + value
            case 0x05:
                "Set hi byte of timer_A"
                self.timer_A_latch = value * 256 + self.timer_A_latch % 256
            case 0x0D:
                # TODO: set interrupt sources
                # source = bool(value & 0b10000000)
                pass

            case 0x0E:
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
                if value & 0b00010000:
                    self.timer_A_load()


class CIA_B(CIA):
    __slots__ = []

    def __init__(self, memory, bus):
        super().__init__(memory, bus)
        # self.memory.read_watchers.append((0xDD00, 0xDDFF, self.get_registers))
        self.memory.write_watchers.append((0xDD00, 0xDDFF, self.set_registers))

    def clock(self):
        return False

    def get_registers(self, address):
        return 0

    def set_registers(self, address, value):
        match address & 0x0F:
            case 0x00:
                # Note:
                # Here, at CIA_B's
                # We'll set a MEMORY internal
                # Used by the VIC
                self.memory.vic_memory_bank = (3 - (value & 0b11)) << 14