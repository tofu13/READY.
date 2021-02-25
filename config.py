COMPILERS = {
    "acme":
        {
            "path": "compilers/acme",
            "cmd_line": "{path} -o {filename}.obj {filename}"
        },
    "xa":
        {
            "path": "compilers/xa",
            "cmd_line": "{path} -o {filename}.obj {filename}"
        },
}
DEFAULT_COMPILER = "acme"
