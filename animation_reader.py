# import os
import struct
# import time


class FASReader:
    def __init__(self, fas_path):
        # filename = os.path.splitext(os.path.basename(fas_path))[0]
        self.fas_file = open(fas_path, 'rb')
        self.header = self.read_header()
        self.bitmap_infos = []
        bitmap_infos_size = 0
        for i in range(self.header['doublepal_count'] * 2):
            # bitmap_info = {
            #     'header_size': self.read_4_bytes(offset=self.header['header_size'] + bitmap_infos_size,
            #                                      byte_format='I'),
            #     'width': self.read_4_bytes(offset=self.header['header_size'] + 4 + bitmap_infos_size),
            #     'height': self.read_4_bytes(offset=self.header['header_size'] + 8 + bitmap_infos_size),
            #     'planes': self.read_2_bytes(offset=self.header['header_size'] + 12 + bitmap_infos_size),
            #     'bpp': self.read_2_bytes(offset=self.header['header_size'] + 14 + bitmap_infos_size),
            #     'compression': self.read_4_bytes(offset=self.header['header_size'] + 16 + bitmap_infos_size,
            #                                      byte_format='I'),
            #     'image_size': self.read_4_bytes(offset=self.header['header_size'] + 20 + bitmap_infos_size,
            #                                     byte_format='I'),
            #     'temp': [self.read_4_bytes(offset=self.header['header_size'] + 24 + bitmap_infos_size),
            #              self.read_4_bytes(offset=self.header['header_size'] + 28 + bitmap_infos_size),
            #              self.read_4_bytes(offset=self.header['header_size'] + 32 + bitmap_infos_size,
            #                                byte_format='I'),
            #              self.read_4_bytes(offset=self.header['header_size'] + 36 + bitmap_infos_size,
            #                                byte_format='I')],
            #     'colormap': []
            # }
            # for j in range(bitmap_info['temp'][2] if (bitmap_info['temp'][2] != 0) else 2 ** bitmap_info['bpp']):
            #     bitmap_info['colormap'].append(self.read_4_bytes(offset=self.header['header_size'] + 40 +
            #                                                     bitmap_infos_size + j * 4, byte_format='I'))
            bitmap_info_header_size = self.read_4_bytes(offset=self.header['header_size'] + bitmap_infos_size,
                                                        byte_format='I')
            bpp = self.read_2_bytes(offset=self.header['header_size'] + 14 + bitmap_infos_size)
            # colors_used = self.read_4_bytes(offset=self.header['header_size']
            #                                        + 32 + bitmap_infos_size, byte_format='I')
            # print(hex(self.header['header_size'] + bitmap_infos_size)+':', bitmap_info_header_size, colors_used)
            bitmap_info = struct.pack('<I', bitmap_info_header_size) + struct.pack('<i', self.header['width'])\
                          + struct.pack('<i', self.header['height']) +\
                          self.read_bytes_raw(offset=self.header['header_size'] + 12 + bitmap_infos_size,
                                              num_bytes=bitmap_info_header_size - 12 + (2 ** bpp)*4)
            self.bitmap_infos.append(bitmap_info)
            # bitmap_infos_size += bitmap_info['header_size'] + len(bitmap_info['colormap']) * 4
            bitmap_infos_size += len(bitmap_info)
            # print(bitmap_info)
        if self.header['version'] >= 1:
            self.char_id = self.read_1_byte(offset=self.header['header_size'] + bitmap_infos_size)
        if self.header['version'] >= 2:
            self.extra_sprite_files = self.read_extra_sprite_files(self.header['header_size'] + bitmap_infos_size
                                                                   + int(self.header['version'] >= 1))
        else:
            self.extra_sprite_files = {'size': 0, 'count': 0, 'files': []}  # Failsafe
        if self.header['version'] >= 3:  # get missing upper 2 bytes of the frame_size variable
            self.header['frame_size'] += self.read_2_bytes(offset=self.header['header_size'] + bitmap_infos_size
                                                           + int(self.header['version'] >= 1)
                                                           + int(self.header['version'] >= 2)
                                                           * self.extra_sprite_files['size']) << 16
        touch_colors = self.read_2_bytes(offset=self.header['header_size'] + bitmap_infos_size
                                         + int(self.header['version'] >= 1)
                                         + int(self.header['version'] >= 2) * self.extra_sprite_files['size']
                                         + int(self.header['version'] >= 3) * 2)
        if touch_colors >= 1:  # check for hotspots
            touch_width = self.read_2_bytes(offset=self.header['header_size'] + bitmap_infos_size
                                            + int(self.header['version'] >= 1) + touch_colors * 4 + 2
                                            + int(self.header['version'] >= 2) * self.extra_sprite_files['size']
                                            + int(self.header['version'] >= 3) * 2
                                            )
            self.touch = {
                'colors': [self.read_4_bytes(offset=self.header['header_size'] + bitmap_infos_size
                                             + int(self.header['version'] >= 1) + i * 4 + 2
                                             + int(self.header['version'] >= 2) * self.extra_sprite_files['size']
                                             + int(self.header['version'] >= 3) * 2, byte_format='I')
                           for i in range(touch_colors)],
                'width': touch_width,
                'bitmap': self.read_bytes_raw(offset=self.header['header_size'] + bitmap_infos_size
                                              + int(self.header['version'] >= 1) + touch_colors * 4 + 4
                                              + int(self.header['version'] >= 2) * self.extra_sprite_files['size']
                                              + int(self.header['version'] >= 3) * 2,
                                              num_bytes=touch_width * self.header['height'])
                # 'bitmap': self.read_bytes_iter(offset=self.header['header_size'] + bitmap_infos_size
                #                           + int(self.header['version'] >= 1) + touch_colors * 4 + 4
                #                           + int(self.header['version'] >= 2) * self.extra_sprites['size']
                #                           + int(self.header['version'] >= 3) * 2,
                #                           num_bytes=touch_width * self.header['height'], byte_format='B')
            }
            self.seq_offset = (self.header['header_size'] + bitmap_infos_size + int(self.header['version'] >= 1) + 2
                               + int(self.header['version'] >= 2) * self.extra_sprite_files['size']
                               + int(self.header['version'] >= 3) * 2
                               + (touch_colors >= 1) * (touch_colors * 4 + 2 + len(list(self.touch['bitmap']))))
        else:
            self.seq_offset = (self.header['header_size'] + bitmap_infos_size + int(self.header['version'] >= 1) + 2
                               + int(self.header['version'] >= 2) * self.extra_sprite_files['size']
                               + int(self.header['version'] >= 3) * 2)
        self.seq_header = self.read_seq_header(self.seq_offset)
        self.seq_directory = self.read_seq_directory(self.seq_offset + self.seq_header['header_size'])
        if self.header['version'] >= 1:  # checksum (format version >= 1)
            self.checksum = self.read_1_byte(self.seq_offset + self.seq_header['total_size'])
            # name_sum = 0
            # for i in range(len(filename)):
            #     name_sum += ord(filename.upper()[i])
            # name_sum %= 256
            # print('Checksum', 'OK!' if name_sum == checksum else 'FAILED!')
            # assert(name_sum == checksum)

        self.frames_header = self.read_frames_header(self.seq_offset + self.seq_header['total_size']
                                                     + (self.header['version'] >= 1))
        # self.frames_bitmap = [list(self.read_bytes_iter(offset=self.seq_offset + self.seq_header['total_size']
        #                                                 + (self.header['version'] >= 1) + 4
        #                                                 + self.frames_header['count'] * 3 + i
        #                                                 * self.header['frame_size'],
        #                                                 num_bytes=self.header['frame_size'], byte_format='B'))
        #                       for i in range(self.frames_header['count'])]
        self.frames_bitmap = [self.read_bytes_raw(offset=self.seq_offset + self.seq_header['total_size']
                                                  + (self.header['version'] >= 1) + 4
                                                  + self.frames_header['count'] * 3 + i
                                                  * self.header['frame_size'],
                                                  num_bytes=self.header['frame_size'])
                              for i in range(self.frames_header['count'])]
        # [print(self.read_sequence(i)) for i in range(self.seq_header['seq_count'])]

    def read_extra_sprite_files(self, __offset):
        return {
            'size': max(6, self.read_4_bytes(offset=__offset)),
            'counts': self.read_2_bytes(offset=__offset+4),
            'files': self.read_stringlist_iso(offset=__offset+6,
                                              num_bytes=self.read_4_bytes(offset=__offset) - 6)[:-1]
        }

    def read_frames_header(self, __offset):
        return {
            'count': self.read_4_bytes(offset=__offset),
            'id': [self.read_2_bytes(offset=__offset + 4 + i * 2)
                   for i in range(self.read_4_bytes(offset=__offset))],
            'info': [self.read_1_byte(offset=__offset + 4 + self.read_4_bytes(offset=__offset) * 2 + i)
                     for i in range(self.read_4_bytes(offset=__offset))]
        }

    def read_sequence(self, __index):
        pointers = self.seq_directory[__index]
        name_offset = (pointers['name_offset'] + self.seq_header['header_size']
                       + self.seq_header['seq_count'] * 8 + self.seq_offset)
        seq_offset = (pointers['data_offset'] + self.seq_header['header_size']
                      + self.seq_header['seq_count'] * 8 + self.seq_offset)
        # print(hex(name_offset),hex(seq_offset))
        # seq_info = {
        #     'name': self.read_string(offset=name_offset, num_bytes=50),
        #     'sequence': self.read_string_iso(offset=seq_offset, num_bytes=4000)
        # }
        seq_info = {
            'name': self.read_string_null_terminated(offset=name_offset),
            'sequence': self.read_string_null_terminated_iso(offset=seq_offset)
        }
        # seq_info = {
        #     self.read_string_null_terminated(offset=name_offset): self.read_string_null_terminated_iso(offset=seq_offset)
        # }
        return seq_info

    def read_seq_directory(self, __offset):
        directory = []
        for i in range(self.seq_header['seq_count']):
            offset = __offset + i * 8
            sound_offset = {
                'id': i,
                'name_offset': self.read_4_bytes(offset),
                'data_offset': self.read_4_bytes(offset + 4)
            }
            directory.append(sound_offset)
        return directory

    def read_seq_header(self, __offset):
        return {
            'total_size': self.read_4_bytes(offset=__offset),
            'seq_count': self.read_4_bytes(offset=__offset + 4),
            'header_size': 8
        }

    def read_header(self):
        return {
            'name': self.read_string(offset=0, num_bytes=50),
            'version': self.read_2_bytes(offset=50),
            'first_frame': self.read_2_bytes(offset=52),
            'last_frame': self.read_2_bytes(offset=54),
            'width': self.read_4_bytes(offset=56, byte_format='i'),
            'height': self.read_4_bytes(offset=60, byte_format='i'),
            'frame_size': self.read_2_bytes(offset=64, byte_format='H'),
            'doublepal_count': self.read_2_bytes(offset=66),
            'header_size': 68
        }

    def read_1_byte(self, offset, byte_format='B'):
        # B - unsigned char, b - signed char
        return self.read_bytes(offset=offset, num_bytes=1, byte_format=byte_format)[0]

    def read_2_bytes(self, offset, byte_format='H'):
        # H - uint16, h - int16
        return self.read_bytes(offset=offset, num_bytes=2, byte_format=byte_format)[0]

    def read_4_bytes(self, offset, byte_format='i'):
        # I - uint32, i - int32
        return self.read_bytes(offset=offset, num_bytes=4, byte_format=byte_format)[0]

    def read_stringlist_iso(self, offset, num_bytes):
        # c - char
        return ''.join(b.decode('iso_8859_1') for b in
                       self.read_bytes(offset, num_bytes, byte_format='c' * num_bytes)
                       ).split('\x00')

    def read_string_null_terminated_iso(self, offset):
        # c - char
        i, result = 0, b''
        while True:
            b = self.read_bytes_raw(offset=offset + i, num_bytes=1)
            if (b == b'\x00') or (b == b''):
                break
            result += b
            i += 1
        return result.decode('iso_8859_1')

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

    def read_string_iso(self, offset, num_bytes):
        # c - char
        return ''.join(b.decode('iso_8859_1') for b in
                       self.read_bytes(offset, num_bytes, byte_format='c' * num_bytes)
                       ).split('\x00')[0]

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
        self.fas_file.seek(offset)
        buffer = self.fas_file.read(num_bytes)
        return struct.unpack(byte_format, buffer)

    def close(self):
        self.fas_file.close()
