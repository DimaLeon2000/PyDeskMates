def read_bits_per_pixel(byte, bits_per_pixel):
    # this might come in handy
    for i in range(8, 0, -bits_per_pixel):
        yield (byte >> (i - bits_per_pixel)) % (2 ** bits_per_pixel)
    # bits = [(byte >> (i - bits_per_pixel)) % (2 ** bits_per_pixel) for i in range(8, 0, -bits_per_pixel)]
    # return bits


def read_rgb(value, reverse=False):
    return (value % 256, (value >> 8) % 256, (value >> 16) % 256) if reverse else\
        ((value >> 16) % 256, (value >> 8) % 256, value % 256)

def read_rgb_to_hex(value, reverse=False):
    return '0x%02x%02x%02x' % (value % 256, (value >> 8) % 256, (value >> 16) % 256) if reverse else\
        '0x%02x%02x%02x' % ((value >> 16) % 256, (value >> 8) % 256, value % 256)


def get_bit_depth(value):
    n = 1
    while value >= (1 << n): n <<= 1
    return n
    # print('The value can be stored in', n, 'bits')

