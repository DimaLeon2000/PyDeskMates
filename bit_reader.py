def read_bits_per_pixel(byte, bits_per_pixel):
    # this might come in handy
    bits = [(byte >> (i - bits_per_pixel)) % (2 ** bits_per_pixel) for i in range(8, 0, -bits_per_pixel)]
    return bits


def read_rgb(value, reverse):
    return (value % 256, (value >> 8) % 256, (value >> 16) % 256) if reverse else\
        ((value >> 16) % 256, (value >> 8) % 256, value % 256)
