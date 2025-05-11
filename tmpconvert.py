import os
import string
import sys


def decode_rt_file(filepath):
    decoded_lines_a = []
    decoded_lines = []
    with open(filepath, "rb") as f:
        lines = f.readlines()

    if not lines:
        return []

    header = lines[0].decode("utf-8", errors="ignore").strip()
    print(f"[header] {header}")

    for line in lines[1:]:
        decoded_line = ''.join(chr(byte - 12) for byte in line)
        decoded_lines_a.append(decoded_line)


    for line in decoded_lines_a:
        decoded_line_c = ''
        for char in line:
            if not char == "¶":
                decoded_line_c += char
        decoded_lines.append(decoded_line_c)
    if sys.argv[1] == "-clear":
        return decoded_lines
    else:
        return decoded_lines_a

# Usage:
if __name__ == "__main__":
    basepath = "C:/BAT/loglang"  # change this as needed
    filepath = os.path.join(basepath, "rt_temp.ltmp")

    decoded = decode_rt_file(filepath)
    print("\n[decoded output]")
    for line in decoded:
        print(line)