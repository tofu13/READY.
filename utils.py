import subprocess

from constants import *


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
