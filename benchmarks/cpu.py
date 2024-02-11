import inspect
from timing import timing
from hardware.machine import DefaultMachine

machine = DefaultMachine()


def benchmark_cpu():
    """
            LDX #$0F
    loop:   STX $C000
            DEX
            BNE loop
            BRK
    """

    machine.memory.set_slice(0x0801, [0xa2, 0x0f, 0x8e, 0x00, 0xC0, 0xca, 0xd0, 0xfa, 0x00])
    with timing() as t:
        t.repeat(10000, machine.run, 0x0801)
    print(t)


def benchmark_cpu_BRK():
    """
            BRK
    """
    machine.memory[0x0800] = 0x00
    with timing() as t:
        t.repeat(10000, machine.run, 0x0800)
    print(t)


# Run all benchmarks* a la pytest
for benchmark in [meth for meth_name, meth in inspect.currentframe().f_locals.items() if
                  meth_name.startswith("benchmark")]:
    benchmark()

