from multiprocessing import shared_memory, Process
from time import sleep

from config import *

import hardware

def cpu(shared_mem):
    print("Cpu start")
    buf = shared_mem.buf
    c = hardware.cpu.CPU(buf, PC=0xFCE2)
    while True:
        c.step()


def vic(shared_mem):
    print("VIC start")
    buf = shared_mem.buf
    s = hardware.screen.Screen(buf)
    s.main()


if __name__ == "__main__":
    shm = shared_memory.SharedMemory(name="c64", create=True, size=65536)
    roms = hardware.roms.ROMS("../"+ROMS_FOLDER)

    mem = shm.buf

    for addr, b in enumerate(roms.contents['basic']):
        mem[0xA000 + addr] = b
    for addr, b in enumerate(roms.contents['chargen']):
        mem[0xD000 + addr] = b
    for addr, b in enumerate(roms.contents['kernal']):
        mem[0xE000 + addr] = b

    cpu = Process(target=cpu, args=(shm,))
    vic = Process(target=vic, args=(shm,))
    cpu.start()
    vic.start()

    sleep(300)

    vic.terminate()
    cpu.terminate()

