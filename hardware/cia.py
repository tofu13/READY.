from .constants import *
import time

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
import asyncio

class CIAA:
    memory = None
    pipe = None
    keyboard_row = 0
    keyboard_col = 0

    def init(self):
        self.memory.read_watchers.append((0xDC00, 0xDCFF, self.get_registers))
        #self.memory.write_watchers.append((0xDC00, 0xDCFF, self.set_registers))

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

         #row, col = KEYSCAN.get(event.key, [8,8])
         #self.keyboard_row = 0xFF - 2 ** row
         #self.keyboard_col = 0xFF - 2 ** col

         #            print ("READ K",self.keyboard_row, self.keyboard_col)


         #    elif event.type == pygame.KEYUP:
         #        self.memory[0xDC01] = 0xFF No key pressed

    async def loop(self, queue):
        delay = 1/IRQ_RATE
        while True:
            await queue.put("IRQ")
            await asyncio.sleep(delay)
            self.fake_keyboard()



    def get_registers(self, address, value):
        #print (address)
        if address == 0xDC01:
            return 0xFF # Remove

            pygame.event.get()
            col = self.memory[0xDC00]
            k = 0xFF
            if col == 0xFE:
                if pygame.key.get_pressed()[pygame.K_DELETE] or pygame.key.get_pressed()[pygame.K_BACKSPACE]:
                    k = 0xFE
                elif pygame.key.get_pressed()[pygame.K_RETURN]:
                    k = 0xFD
                elif pygame.key.get_pressed()[pygame.K_RIGHT]:
                    k = 0xFB
                elif pygame.key.get_pressed()[pygame.K_F7]:
                    k = 0xF7
                elif pygame.key.get_pressed()[pygame.K_F1]:
                    k = 0xEF
                elif pygame.key.get_pressed()[pygame.K_F3]:
                    k = 0xDF
                elif pygame.key.get_pressed()[pygame.K_F5]:
                    k = 0xBF
                elif pygame.key.get_pressed()[pygame.K_DOWN]:
                    k = 0x7F

            elif col == 0xFD:
                if pygame.key.get_pressed()[pygame.K_3]:
                    k = 0xFE
                elif pygame.key.get_pressed()[pygame.K_w]:
                    k = 0xFD
                elif pygame.key.get_pressed()[pygame.K_a]:
                    k = 0xFB
                elif pygame.key.get_pressed()[pygame.K_4]:
                    k = 0xF7
                elif pygame.key.get_pressed()[pygame.K_z]:
                    k = 0xEF
                elif pygame.key.get_pressed()[pygame.K_f]:
                    k = 0xDF
                elif pygame.key.get_pressed()[pygame.K_e]:
                    k = 0xBF
                #elif pygame.key.get_pressed()[pygame.K_e]:
                #    k = 0x7F

            elif col == 0xFB:
                if pygame.key.get_pressed()[pygame.K_5]:
                    k = 0xFE
                elif pygame.key.get_pressed()[pygame.K_r]:
                    k = 0xFD
                elif pygame.key.get_pressed()[pygame.K_d]:
                    k = 0xFB
                elif pygame.key.get_pressed()[pygame.K_6]:
                    k = 0xF7
                elif pygame.key.get_pressed()[pygame.K_c]:
                    k = 0xEF
                elif pygame.key.get_pressed()[pygame.K_f]:
                    k = 0xDF
                elif pygame.key.get_pressed()[pygame.K_t]:
                    k = 0xBF
                elif pygame.key.get_pressed()[pygame.K_x]:
                    k = 0x7F

            elif col == 0xF7:
                if pygame.key.get_pressed()[pygame.K_7]:
                    k = 0xFE
                elif pygame.key.get_pressed()[pygame.K_y]:
                    k = 0xFD
                elif pygame.key.get_pressed()[pygame.K_b]:
                    k = 0xFB
                elif pygame.key.get_pressed()[pygame.K_8]:
                    k = 0xF7
                elif pygame.key.get_pressed()[pygame.K_c]:
                    k = 0xEF
                elif pygame.key.get_pressed()[pygame.K_h]:
                    k = 0xDF
                elif pygame.key.get_pressed()[pygame.K_u]:
                    k = 0xBF
                elif pygame.key.get_pressed()[pygame.K_v]:
                    k = 0x7F

            elif col == 0xEF:
                if pygame.key.get_pressed()[pygame.K_9]:
                    k = 0xFE
                elif pygame.key.get_pressed()[pygame.K_i]:
                    k = 0xFD
                elif pygame.key.get_pressed()[pygame.K_j]:
                    k = 0xFB
                elif pygame.key.get_pressed()[pygame.K_0]:
                    k = 0xF7
                elif pygame.key.get_pressed()[pygame.K_m]:
                    k = 0xEF
                elif pygame.key.get_pressed()[pygame.K_k]:
                    k = 0xDF
                elif pygame.key.get_pressed()[pygame.K_o]:
                    k = 0xBF
                elif pygame.key.get_pressed()[pygame.K_n]:
                    k = 0x7F

            elif col == 0xDF:
                if pygame.key.get_pressed()[pygame.K_PLUS]:
                    k = 0xFE
                elif pygame.key.get_pressed()[pygame.K_p]:
                    k = 0xFD
                elif pygame.key.get_pressed()[pygame.K_l]:
                    k = 0xFB
                elif pygame.key.get_pressed()[pygame.K_MINUS]:
                    k = 0xF7
                elif pygame.key.get_pressed()[pygame.K_PERIOD]:
                    k = 0xEF
                elif pygame.key.get_pressed()[pygame.K_COLON]:
                    k = 0xDF
                elif pygame.key.get_pressed()[pygame.K_AT]:
                    k = 0xBF
                elif pygame.key.get_pressed()[pygame.K_COMMA]:
                    k = 0x7F

            elif col == 0xBF:
                #if pygame.key.get_pressed()[pygame.K_]:
                #    k = 0xFE
                if False:
                    pass
                elif pygame.key.get_pressed()[pygame.K_ASTERISK]:
                    k = 0xFD
                elif pygame.key.get_pressed()[pygame.K_SEMICOLON]:
                    k = 0xFB
                elif pygame.key.get_pressed()[pygame.K_HOME]:
                    k = 0xF7
                #elif pygame.key.get_pressed()[pygame.K_PERIOD]:
                #    k = 0xEF
                elif pygame.key.get_pressed()[pygame.K_EQUALS]:
                    k = 0xDF
                elif pygame.key.get_pressed()[pygame.K_POWER]:
                    k = 0xBF
                elif pygame.key.get_pressed()[pygame.K_SLASH]:
                    k = 0x7F

            elif col == 0x7F:
                if pygame.key.get_pressed()[pygame.K_1]:
                    k = 0xFE
                elif pygame.key.get_pressed()[pygame.K_BACKSLASH]:
                    k = 0xFD
                elif pygame.key.get_pressed()[pygame.K_TAB]:
                    k = 0xFB
                elif pygame.key.get_pressed()[pygame.K_2]:
                    k = 0xF7
                elif pygame.key.get_pressed()[pygame.K_SPACE]:
                    k = 0xEF
                #elif pygame.key.get_pressed()[pygame.K_]:
                #    k = 0xDF
                elif pygame.key.get_pressed()[pygame.K_q]:
                    k = 0xBF
                elif pygame.key.get_pressed()[pygame.K_ESCAPE]:
                    k = 0x7F

            #print(hex(col),hex(k))
            return k
        elif address == 0xDC0D:
            return 0x80
        return value

    def set_registers(self, address, value):
        #print("write ciaA", address, value)
        #self.memory[address] = value
        pass


class CIAB:
    memory = None

    def init(self):
        self.memory.read_watchers.append((0xDD00, 0xDDFF, self.get_registers))
        self.memory.write_watchers.append((0xDD00, 0xDDFF, self.set_registers))

    def loop(self, memory):
        while True:
            time.sleep(1)


    def get_registers(self, address, value):
        #print("read ciaA", address)
        return value
    def set_registers(self, address, value):
        #print("write ciaA", address, value)
        pass
