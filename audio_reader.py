import struct


class WASReader:
    def __init__(self, was_path):
        self.was_file = open(was_path, 'rb')
        self.header = self.read_header()
        # print(self.header, '\n', sum(map(len, self.header)))
        self.directory = self.read_directory()
        # [print('\n', i) for i in self.directory]

    def read_directory(self):
        directory = []
        for i in range(self.header['snd_count']):
            offset = 8 + i * 8
            sound_offset = {
                'id': i,
                'name_offset': self.read_4_bytes(offset),
                'data_offset': self.read_4_bytes(offset + 4)
            }
            directory.append(sound_offset)
        return directory

    def read_header(self):
        return {
            'total_size': self.read_4_bytes(offset=0),
            'snd_count': self.read_4_bytes(offset=4),
            'length': 8
        }

    def read_1_byte(self, offset, byte_format='B'):
        # B - unsigned char, b - signed char
        return self.read_bytes(offset=offset, num_bytes=1, byte_format=byte_format)[0]

    def read_2_bytes(self, offset, byte_format):
        # H - uint16, h - int16
        return self.read_bytes(offset=offset, num_bytes=2, byte_format=byte_format)[0]

    def read_4_bytes(self, offset, byte_format='i'):
        # I - uint32, i - int32
        return self.read_bytes(offset=offset, num_bytes=4, byte_format=byte_format)[0]

    def read_string_null_terminated(self, offset):
        # c - char
        i, result = 0, b''
        while True:
            b = self.read_bytes_raw(offset=offset + i, num_bytes=1)
            if (b == b'\x00') or (b == b''):
                break
            if ord(b) in range(0, 128):
                result += b
            i += 1
        return result.decode('ascii')

    def read_string(self, offset, num_bytes):
        # c - char
        return ''.join(b.decode('ascii') for b in
                       self.read_bytes(offset, num_bytes, byte_format='c' * num_bytes)
                       if ord(b) in range(0, 128)).split('\x00')[0]

    def read_bytes_raw(self, offset, num_bytes):
        self.fas_file.seek(offset)
        buffer = self.fas_file.read(num_bytes)
        return buffer

    def read_bytes(self, offset, num_bytes, byte_format):
        self.was_file.seek(offset)
        buffer = self.was_file.read(num_bytes)
        return struct.unpack(byte_format, buffer)

    def close(self):
        self.was_file.close()
