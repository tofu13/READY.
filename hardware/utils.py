import subprocess

from hardware.constants import *
from config import *


def compile(filename, compiler=None):
    if compiler is None:
        for name, current_compiler in COMPILERS.items():
            print(f"Trying compiler {name}... ", end="")
            if run_compiler(filename, current_compiler):
                return True
    else:
        return run_compiler(filename, compiler)


def run_compiler(filename, compiler):
    result = subprocess.run(
        compiler['cmd_line'].format(filename=filename, **compiler).split(),
        capture_output=True
    )
    if result.returncode:
        print("Error:", result.stderr)
        return False
    else:
        print("Ok!")
        return True

def bit(value, position, length=1):
    """
    Return bit of number value at position
    Position starts from 0 (LSB)
    :param value:
    :param position:
    :return:
    """
    binary = bin(value)[2:]
    size = len(binary) - 1
    if position > size:
        return 0
    else:
        return int(binary[size - position: size - position + length] ,2)
