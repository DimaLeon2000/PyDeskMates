from animation_reader import FASReader
import io
import re
from PIL import Image, ImageOps
from ast import literal_eval

REGEX_EXTRA_SPRITE = r'(#{1,2})(.+[^,])'  # places a temporary extra sprite
# (group #1: absolute/relative positioning; group #2: sequence)
REGEX_FENCING = r'©(?:\[(-?[0-9]+)\,(-?[0-9]+)\])?(\d[lcr]\d[tmb])\,(?:\[(-?[0-9]+)\,(-?[0-9]+)\])?(\d[lcr]\d[tmb])©'
REGEX_FRAME_RANGE = r'([0-9]+)-([0-9]+)'
REGEX_GROUP = r'\((.+?)\)'
REGEX_OFFSET = r'\[(-?[0-9]+,-?[0-9]+)\]'
REGEX_RANDOM_CHOICES = r'{(.+?)}'
REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED = r'(\(.+?\)|[a-zA-Z_0-9]+|[0-9]+)%([0-9]+)'
REGEX_FLOATING = r'§([0-9])\/([0-9])'
REGEX_REPEAT = r'(\(.+?\)|[a-zA-Z_0-9]+|[0-9]+)\*([0-9])+'  # Repeat the sequence X times
REGEX_REPEAT_TIMER = r'(\(.+?\)|[a-zA-Z_0-9]+|[0-9]+)\@([0-9])+'  # Repeat the sequence for X frames / X/10 seconds
# (the hardcoded frame rate is 10 frames per second)
REGEX_SOUND = r' !([^,]+)'  # Play sound effect (group #1: sound name)
REGEX_FLIP_HORIZONTAL = r'<'
REGEX_FLIP_VERTICAL = r'\^'
REGEX_MASKING = r'\xBD'


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
            print(sequence['name'] + ':', self.sequences[sequence['name']])
            print('== ' + sequence['name'] + ' (parsed) ==')
            self.parse_sequence(seq=sequence['name'])
        self.frames_header = self.reader.frames_header
        self.frames_bitmap = self.reader.frames_bitmap

    def parse_sequence_part(self, __part):  # INCOMPLETE
        if re.match(REGEX_GROUP, __part):
            return re.match(REGEX_GROUP, __part).group(0)
        elif re.match(REGEX_FENCING, __part):
            # print(__part, '(FENCING)')
            return 'FENCING'
        elif re.match(REGEX_OFFSET, __part):
            print(literal_eval(re.match(REGEX_OFFSET, __part).groups()[0]), 'OFFSET')
            return literal_eval(re.match(REGEX_OFFSET, __part).groups()[0])
        else:
            return __part

    def parse_sequence(self, seq):  # INCOMPLETE
        parts = re.findall(r'(?:\((?:[^()].*?)*\)|\[(?:[^[\]].*?)*]|{(?:[^{}].*?)*}|©(?:[^©].*?)*©|[^,])+',
                           self.sequences[seq])
        for x in parts:
            x = self.parse_sequence_part(x)
            print(x)
            # if re.match(r'\[([0-9\,\-]+)\]', x): #check if
            #     pos_offset = literal_eval(re.match(r'\[([0-9\,\-]+)\]', x).group(1))
            #     print(pos_offset)
            # print(x)
            # pass
        return parts

    def get_frame_bitmap(self, __frame, mask):
        bitmap_info = self.bitmap_infos[self.frames_header['info'][__frame] * 2 + int(mask)]
        bitmap = self.frames_bitmap[__frame]
        header = b'BM' + int(len(bitmap_info) + len(bitmap) + 14).to_bytes(length=4, byteorder='little', signed=False) \
            + (0).to_bytes(length=2, byteorder='little', signed=False) \
            + (0).to_bytes(length=2, byteorder='little', signed=False) \
            + int(len(bitmap_info) + 14).to_bytes(length=4, byteorder='little', signed=False)
        data = header + bitmap_info + bitmap
        return data

    def get_frame_masked(self, __frame):
        color = Image.open(io.BytesIO(self.get_frame_bitmap(__frame, mask=False))).convert('RGBA')
        mask = ImageOps.invert(Image.open(io.BytesIO(self.get_frame_bitmap(__frame, mask=True))).convert('L'))
        color.putalpha(mask)
        return color
