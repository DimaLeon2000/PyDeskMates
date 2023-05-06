from animation_reader import FASReader
import io
from pygame import Vector2, rect
import random
import re
from settings import *
from PIL import Image, ImageOps, ImageFile
from ast import literal_eval

REGEX_ADD_SPRITE = r'(#{1,2})(.+[^,])'  # places a temporary extra sprite
# (group #1: absolute/relative positioning; group #2: sequence)
REGEX_FENCING = r'©(?:\[(-?\d+)\,(-?\d+)\])?(\d[lcr]\d[tmb])\,(?:\[(-?\d+)\,(-?\d+)\])?(\d[lcr]\d[tmb])©'
REGEX_FRAME_RANGE = r'(\d+)-(\d+)'
REGEX_GROUP = r'\((.+)\)([^\*\@]*)?'
REGEX_LOAD_FAS = r'_([^,]+)'  # load external FAS file
REGEX_OFFSET = r'\[(-?\d+,-?\d+)\](.*)?'
REGEX_RANDOM_CHOICES = r'{(.+?)}'
REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED = r'(\(.+?\)|[a-zA-Z_0-9]+|\d+)%(\d+)'
REGEX_FLOATING = r'§(\d)\/(\d)'
REGEX_REPEAT = r'(.+?)\*(\d+)'  # Repeat the sequence X times
REGEX_REPEAT_TIMER = r'(.+)\@(\d+)'  # Repeat the sequence for X frames / X/10 seconds
# (the hardcoded frame rate is 10 frames per second)
REGEX_SOUND = r' !([^,]+)'  # Play sound effect (group #1: sound name)
REGEX_FLIP_HORIZONTAL = r'<(.*)?'
REGEX_FLIP_VERTICAL = r'\^(.*)?'
REGEX_MASKING = r'\xBD(.*)?'

alignment = {
    'l': 0,  # horizontal
    'c': WIDTH // 2,
    'r': WIDTH,
    't': 0,  # vertical
    'm': HEIGHT // 2,
    'b': HEIGHT}


class FASData:
    def __init__(self, fas_path, app, extra=False):
        self.app = app
        self.reader = FASReader(fas_path)
        # if self.reader != 0:
        #     print('File read!')
        self.header = self.reader.header
        self.bitmap_infos = self.reader.bitmap_infos
        if hasattr(self.reader, 'touch'):
            self.touch = self.reader.touch
        for i in range(self.reader.seq_header['seq_count']):
            sequence = self.reader.read_sequence(i)
            if extra:
                self.app.sequences_extra[sequence['name'].upper()] = sequence['sequence']
            else:
                self.app.sequences[sequence['name'].upper()] = sequence['sequence']
            # print(sequence['name'] + ':', self.app.sequences[sequence['name']])
            # print('== ' + sequence['name'] + ' (parsed) ==')
            # print(self.get_sequence(seq=sequence['name']))
        self.frames = {}
        for i in range(self.reader.frames_header['count']):
            self.frames[self.reader.frames_header['id'][i]] = {
                'bitmap': self.reader.frames_bitmap[i],
                'info': self.reader.frames_header['info'][i]
            }
        for i in self.frames:
            if extra:
                self.app.frames_extra[i] = self.get_frame_masked(i)
            else:
                self.app.frames[i] = self.get_frame_masked(i)
        self.reader.close()
        # self.app.frames_header = self.reader.frames_header
        # self.app.frames_bitmap = self.reader.frames_bitmap

    def get_frame_bitmap(self, __frame, mask):
        bitmap_info = self.bitmap_infos[self.frames[__frame]['info'] * 2 + int(mask)]
        bitmap = self.frames[__frame]['bitmap']
        header = b'BM' + int(len(bitmap_info) + len(bitmap) + 14).to_bytes(length=4, byteorder='little', signed=False) \
            + (0).to_bytes(length=2, byteorder='little', signed=False) \
            + (0).to_bytes(length=2, byteorder='little', signed=False) \
            + int(len(bitmap_info) + 14).to_bytes(length=4, byteorder='little', signed=False)
        data = header + bitmap_info + bitmap
        return data

    def get_frame_masked(self, __frame):
        color_data = self.get_frame_bitmap(__frame, mask=False)
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        color = Image.open(io.BytesIO(color_data)).convert('RGBA')
        mask = ImageOps.invert(Image.open(io.BytesIO(self.get_frame_bitmap(__frame, mask=True))).convert('L'))
        color.putalpha(mask)
        return color


def parse_sequence_part(__part, app):  # INCOMPLETE
    if not(__part.__contains__(' !')):
        __part = __part.strip()
    if re.match(REGEX_RANDOM_CHOICES, __part):
        choices_weighted = re.match(REGEX_RANDOM_CHOICES, __part).group(1).split('|')
        choices = []
        weights = []
        for i in choices_weighted:
            if re.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i):
                choices.append(re.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i).group(1))
                weights.append(int(re.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i).group(2)))
            else:
                choices.append(i)
                weights.append(1)
        result = random.choices(choices, weights)[0]
        return parse_sequence_part(result, app)
    elif re.match(REGEX_GROUP, __part):
        res0 = re.match(REGEX_GROUP, __part).group(1)
        res1 = re.match(REGEX_GROUP, __part).group(2)
        # print(res0, res1)
        result = [parse_sequence(res0, app)]
        if res1 != '':
            result.append(parse_sequence_part(res1, app))
        return result
    elif re.match(REGEX_REPEAT_TIMER, __part):
        str_groups = re.match(REGEX_REPEAT_TIMER, __part).groups()
        # return SeqRepeatTimer(parse_sequence_part(str_groups[0], app), int(str_groups[1]))
        return {'timer_frames': int(str_groups[1]), 'seq': parse_sequence_part(str_groups[0], app)}
    elif re.match(REGEX_REPEAT, __part):
        str_groups = re.match(REGEX_REPEAT, __part).groups()
        # print(str_groups)
        # return SeqRepeat(parse_sequence_part(str_groups[0], app), int(str_groups[1]))
        return {'repeats': int(str_groups[1]), 'seq': parse_sequence_part(str_groups[0], app)}
    elif re.match(REGEX_FLIP_HORIZONTAL, __part):
        # print(re.match(REGEX_FLIP_HORIZONTAL, __part).group(1))
        res1 = re.match(REGEX_FLIP_HORIZONTAL, __part).group(1)
        result = [{'toggle_flag': 1}]
        if res1 != '':
            result.append(parse_sequence_part(res1, app))
        return result
    elif re.match(REGEX_FLIP_VERTICAL, __part):
        res1 = re.match(REGEX_FLIP_VERTICAL, __part).group(1)
        result = [{'toggle_flag': 2}]
        if res1 != '':
            result.append(parse_sequence_part(res1, app))
        return result
    elif re.match(REGEX_MASKING, __part):
        res1 = re.match(REGEX_MASKING, __part).group(1)
        result = [{'toggle_flag': 4}]
        if res1 != '':
            result.append(parse_sequence_part(res1, app))
        return result
    elif re.match(REGEX_FRAME_RANGE, __part):
        frame_start, frame_end = int(re.match(REGEX_FRAME_RANGE, __part).groups()[0]),\
            int(re.match(REGEX_FRAME_RANGE, __part).groups()[1])
        frame_range = range(frame_start, (frame_end - 1) if (frame_end < frame_start) else (frame_end + 1),
                            -1 if (frame_end < frame_start) else 1)
        return [parse_sequence_part(str(i), app) for i in frame_range]
    elif re.match(REGEX_FENCING, __part):
        values = list(re.match(REGEX_FENCING, __part).groups())
        rectangle = rect.Rect(alignment[values[2][1]] + (int(values[0]) if values[0] else 0),
                              alignment[values[2][3]] - (int(values[1]) if values[1] else 0),
                              alignment[values[5][1]] + (int(values[3]) if values[3] else 0)
                              - alignment[values[2][1]] - (int(values[0]) if values[0] else 0),
                              alignment[values[5][3]] - (int(values[4]) if values[4] else 0)
                              - alignment[values[2][3]] + (int(values[1]) if values[1] else 0))
        # print(__part, '(FENCING)')
        return {'fence': rectangle}
        # return 'FENCING'
    elif re.match(REGEX_OFFSET, __part):
        offset = list(literal_eval(re.match(REGEX_OFFSET, __part).group(1)))
        offset[1] *= -1
        part = re.match(REGEX_OFFSET, __part).group(2)
        return [{'offset': Vector2(offset)}, parse_sequence_part(part, app)]
    elif re.match(REGEX_SOUND, __part):
        return {'sound': re.match(REGEX_SOUND, __part).group(1)}
    elif re.match(REGEX_LOAD_FAS, __part):
        return {'load_fas': re.match(REGEX_LOAD_FAS, __part).group(1)}
    elif __part.isnumeric():
        # print(__part)
        return int(__part)
    else:
        # print(get_sequence(__part, app))
        # return get_sequence(__part, app)
        return __part


def parse_sequence(sequence, app):
    level = 0
    fence_open_close = 0  # 0 - open; 1 - close
    parts_orig = sequence.split(sep=',')  # old-school method
    parts = []
    cur_part = ''
    for i in parts_orig:
        if level > 0:
            cur_part = cur_part + ',' + i
        else:
            cur_part = i
        level += i.count('(') + i.count('[') + i.count('{')
        level -= i.count(')') + i.count(']') + i.count('}')
        if i.count('\xA9') >= 1:
            if fence_open_close == 1:
                level -= i.count('\xA9')
                fence_open_close = 0
            else:
                level += i.count('\xA9')
                fence_open_close = 1
        # print(level, end=' ')
        # cur_part = cur_part + ',' + i
        if level == 0:
            parts.append(cur_part)
            cur_part = i
    parts_parsed = []
    for x in parts:
        part_parsed = parse_sequence_part(x, app)
        # if isinstance(part_parsed, list):
        #     [parts_parsed.append(part_parsed[i]) for i in range(len(part_parsed))]
        # else:
        parts_parsed.append(part_parsed)
        # if re.match(r'\[([0-9\,\-]+)\]', x): #check if
        #     pos_offset = literal_eval(re.match(r'\[([0-9\,\-]+)\]', x).group(1))
        #     print(pos_offset)
        # print(x)
        # pass
    # print('PARSED PARTS:', parts_parsed)
    # return [parts_parsed[i] for i in range(len(parts_parsed))]
    return parts_parsed


def get_sequence(seq, app):  # INCOMPLETE
    if seq.upper() in list(app.sequences_extra.keys()):
        sequence = app.sequences_extra[seq.upper()]
    else:
        sequence = app.sequences[seq.upper()]
    return parse_sequence(sequence, app)
