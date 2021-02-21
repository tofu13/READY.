import subprocess


def compile(compiler, filename):
    subprocess.run(f"{compiler['path']} {compiler['options']} -o {filename} {filename}.asm".split())
