from animation_reader import FASReader
import re
from ast import literal_eval


class FASData:
    def __init__(self, fas_path):
        self.reader = FASReader(fas_path)
        # if self.reader != 0:
        #     print('File read!')
        self.header = self.reader.header
        self.bitmap_infos = self.reader.bitmap_infos
        if hasattr(self.reader, 'touch'):
            self.touch = self.reader.touch
        self.sequences = {}
        for i in range(self.reader.seq_header['seq_count']):
            sequence = self.reader.read_sequence(i)
            self.sequences[sequence['name']] = sequence['sequence']
            # print(sequence['name'] + ':', self.sequences[sequence['name']])
            print(sequence['name']+':', sequence['sequence'])
            # print(sequence['name']+' (parsed): ', self.parse_sequence(seq=sequence['name']))
        self.frames_header = self.reader.frames_header
        self.frames_bitmap = self.reader.frames_bitmap

    def parse_sequence_part(self, __part):
        # print(__part.isnumeric())
        return __part

    def parse_sequence(self, seq):  # INCOMPLETE
        parts = re.split(r',(?![^()]*\))(?![^\[\]]*])(?![^{}]]*})(?![^\xA9]*\xA9)', self.sequences[seq])
        for x in parts:
            self.parse_sequence_part(x)
            # if re.match(r'\[([0-9\,\-]+)\]', x): #check if
            #     pos_offset = literal_eval(re.match(r'\[([0-9\,\-]+)\]', x).group(1))
            #     print(pos_offset)
            # print(x)
            pass
        return parts

    def get_frame_bitmap(self, __frame, mask=bool):
        bitmap_info = self.bitmap_infos[self.frames_header['info'][__frame] * 2 + int(mask)]
        bitmap = self.frames_bitmap[__frame]
        header = b'BM' + int(len(bitmap_info) + len(bitmap) + 14).to_bytes(length=4,byteorder='little', signed=False) \
        + (0).to_bytes(length=2, byteorder='little', signed=False) \
        + (0).to_bytes(length=2, byteorder='little', signed=False) \
        + int(len(bitmap_info) + 14).to_bytes(length=4, byteorder='little', signed=False)
        data = header + bitmap_info + bitmap
        return data
