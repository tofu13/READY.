import logging

# Path to ROM files
ROMS_FOLDER = "roms"

# Path to testing ROM files
TESTING_ROMS_FOLDER = "tests/roms"

LOGFILE = "logready"
LOGLEVEL = logging.DEBUG

# Screen driver
# - raster: full simulation, slower
# - fast: partial simulation, faster
# - virtual: headless
# SCREEN = "fast"
SCREEN = "raster"

# Shorten cold start and reset
QUICK_BOOT = True

# Keymap
# KEYMAP = "en"
KEYMAP = "it"

TRACE_EXEC = {}
