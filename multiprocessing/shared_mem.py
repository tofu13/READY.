from multiprocessing import shared_memory, Process
from time import sleep

from config import *

import hardware

def cpu(shared_mem, shared_bus):
    print("Cpu start")
    buf = shared_mem.buf
    bus = shared_bus.buf
    c = hardware.cpu.CPU(buf, PC=0xFCE2)
    while True:
        if bus[0]:
            c.irq()
            bus[0] = 0
        else:
            c.step()


def vic(shared_mem, shared_bus):
    print("VIC start")
    buf = shared_mem.buf
    s = hardware.screen.Screen(buf)
    while True:
        s.step()


def cia(shared_mem, shared_bus):
    buf = shared_mem.buf
    bus = shared_bus.buf
    c = hardware.cia.CIAA(buf)
    while True:
        irq, nmi, signal = c.step()
        bus[0] = int(irq)


if __name__ == "__main__":
    shm = shared_memory.SharedMemory(name="c64", create=True, size=65536)
    bus = shared_memory.SharedMemory(name="c64_bus", create=True, size=8)
    # BUS [irq, nmi, ...]

    roms = hardware.roms.ROMS("../"+ROMS_FOLDER)

    mem = shm.buf

    for addr, b in enumerate(roms.contents['basic']):
        mem[0xA000 + addr] = b
    for addr, b in enumerate(roms.contents['chargen']):
        mem[0xD000 + addr] = b
    for addr, b in enumerate(roms.contents['kernal']):
        mem[0xE000 + addr] = b

    cpu = Process(target=cpu, args=(shm, bus))
    vic = Process(target=vic, args=(shm, bus))
    cia = Process(target=cia, args=(shm, bus))
    vic.start()
    cia.start()
    cpu.start()

    sleep(300)

    vic.terminate()
    cia.terminate()
    cpu.terminate()

