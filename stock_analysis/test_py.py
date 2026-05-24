import sys
print("Executable:", sys.executable)
print("Version:", sys.version)
print("Paths:")
for p in sys.path:
    print("  ", p)