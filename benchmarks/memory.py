from timing import timing

from hardware import memory

mem = memory.BytearrayMemory(65536)
data = [b & 0xFF for b in range(0x1000)]

with timing() as t:
    t.repeat(10 ** 6, mem.__getitem__, 0x0800)
print(f"Memory read single address: {t}")

with timing() as t:
    t.repeat(10 ** 6, mem.__setitem__, 0x0800, 0x00)
print(f"Memory write single address: {t}")

with timing() as t:
    t.repeat(10 ** 6, mem.get_slice, 0xC000, 0xD000)
print(f"Memory read slice 4 kB: {t}")

# Slow and not interesting
# with timing() as t:
#    t.repeat(10 ** 6, mem.set_slice, 0x0C00, data)
# print(f"Memory write 4 kB: {t}")
