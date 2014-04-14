import sys
if len(sys.argv) > 0:
    DELIM = chr(int(sys.argv[1]))
else:
    DELIM = ","
for line in sys.stdin:
    sys.stdout.write(line.replace(", ", DELIM))