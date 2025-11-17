import sys
import re

def parse_c_array(path):
    with open(path, "r") as f:
        content = f.read()

    m = re.search(r'uint8_t\s+\w+_map\[\]\s*=\s*\{([^}]+)\}', content, re.DOTALL)
    if not m:
        return None

    hex_values = re.findall(r'0x([0-9A-Fa-f]{2})', m.group(1))
    bytes_all = [int(h, 16) for h in hex_values]

    # Extraemos solo los datos de los píxeles (los 1024 bytes después de la paleta)
    pixel_data = bytes_all[8:1032]

    # --- LÍNEA MÁGICA ---
    # Invertimos cada bit de cada byte. El operador '~' hace la inversión bit a bit.
    # El '& 0xff' es para asegurar que el resultado se mantenga como un byte de 8 bits.
    inverted_pixel_data = [~b & 0xff for b in pixel_data]
    
    return inverted_pixel_data

def write_output(frames, out_path):
    lines = ["# test_animation.py", ""]
    vars = []

    for i, frame in enumerate(frames):
        v = f"test_frame_{i}"
        vars.append(v)
        ba = "b'" + "".join([f"\\x{b:02x}" for b in frame]) + "'"
        lines.append(f"{v} = bytearray({ba})")

    lines.append("")
    lines.append("TEST_ANIMATION = [")
    for v in vars:
        lines.append(f"    {v},")
    lines.append("]")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    paths = sorted(sys.argv[1:])
    frames = []

    for p in paths:
        frame = parse_c_array(p)
        if frame:
            frames.append(frame)

    write_output(frames, "test_animation.py")

if __name__ == "__main__":
    main()