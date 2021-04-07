from datetime import datetime

from .constants import *

import asyncio


class CIAA:
    memory = None
    pipe = None
    keyboard_row = 0
    keyboard_col = 0

    def init(self):
        self.memory.read_watchers.append((0xDC00, 0xDCFF, self.get_registers))
        self.memory.write_watchers.append((0xDC00, 0xDCFF, self.set_registers))
        self.irq_delay = 1000000 / IRQ_RATE
        self.last_irq = datetime.now()

    def fake_keyboard(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.mod & pygame.KMOD_LSHIFT:
                    selector = 1
                elif event.mod & pygame.KMOD_LALT:
                    selector = 2
                else:
                    selector = 0

                key = KEYTABLE.get(event.key)
                # print(event.unicode, selector, key)

                if key:
                    key = key[selector]
                if key:
                    # Inject char into keyboard buffer
                    self.memory[0x277 + self.memory[0xC6]] = key
                    # Update counter
                    self.memory[0xC6] += 1
                    # print (key)

        # row, col = KEYSCAN.get(event.key, [8,8])
        # self.keyboard_row = 0xFF - 2 ** row
        # self.keyboard_col = 0xFF - 2 ** col

        #            print ("READ K",self.keyboard_row, self.keyboard_col)

        #    elif event.type == pygame.KEYUP:
        #        self.memory[0xDC01] = 0xFF No key pressed

            # self.fake_keyboard()

    def step(self):
        """
        Execute CIA stuff
        :return: raise IRQ:bool, raise NMI:bool
        """
        irq = False
        nmi = False

        # Generate time IRQ
        if (datetime.now() - self.last_irq).microseconds >= self.irq_delay:
            self.last_irq = datetime.now()
            irq = True

            # Scan RESTORE key for NMI
            # Note: use the same timing as interrupts: not accurate but close to reality
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_PAGEUP:
                        nmi = True

        return irq, nmi

    def get_registers(self, address, value):
        if address == 0xDC01:
            pygame.event.get()
            keypressed = list(pygame.key.get_pressed())
            if not any(keypressed):
                return 0xFF
            col = 0xFF - self.memory[0xDC00]  # Invert bits
            k = 0x00
            shift = False
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
                if keypressed[pygame.KSCAN_RSHIFT] or shift:
                    k |= 0x10
                if keypressed[pygame.KSCAN_BACKSLASH]:
                    k |= 0x20  # =
                if keypressed[pygame.KSCAN_NONUSBACKSLASH]:
                    k |= 0x40  # Up arrow
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
                    k |= 0x20
                if keypressed[pygame.KSCAN_Q]:
                    k |= 0x40
                if keypressed[pygame.KSCAN_ESCAPE]:
                    k |= 0x80

            # print(hex(col),hex(k))
            # print(f"Cia read {address:04X} {k:02X}")

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

    def loop(self, memory):
        while True:
            asyncio.sleep(1)

    def get_registers(self, address, value):
        # print("read ciaA", address)
        return value

    def set_registers(self, address, value):
        # print("write ciaA", address, value)
        pass
