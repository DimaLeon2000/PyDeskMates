from animation_reader import FASReader
import io
from pygame import Vector2
import random
import regex
from PIL import Image, ImageOps, ImageFile
from ast import literal_eval

REGEX_COMMA_SEPARATION = r'(?> ( \( (?> [^()]*(?1)?)* \) ) | ( \[ (?> [^\[\]]*(?2)?)* \] ) | ( { (?> [^{}]*(?3)?)* }' \
                         r') | ( © (?> [^©]*(?4)?)* © ) | [^,()\[\]{}]+ | (?P<error>[()\[\]]+) )+'
# a wonky comma separation regular expression, for Python 3.11+
REGEX_EXTRA_SPRITE = r'(#{1,2})(.+[^,])'  # places a temporary extra sprite
# (group #1: absolute/relative positioning; group #2: sequence)
REGEX_FENCING = r'©(?:\[(-?\d+)\,(-?\d+)\])?(\d[lcr]\d[tmb])\,(?:\[(-?\d+)\,(-?\d+)\])?(\d[lcr]\d[tmb])©'
REGEX_FRAME_RANGE = r'(\d+)-(\d+)'
REGEX_GROUP = r'\((.+)\)(.*)?'
REGEX_OFFSET = r'\[(-?\d+,-?\d+)\](.*)?'
REGEX_RANDOM_CHOICES = r'{(.+?)}'
REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED = r'(\(.+?\)|[a-zA-Z_0-9]+|\d+)%(\d+)'
REGEX_FLOATING = r'§(\d)\/(\d)'
REGEX_REPEAT = r'(\(.+?\)|[a-zA-Z_0-9]+|\d+)\*(\d+)'  # Repeat the sequence X times
REGEX_REPEAT_TIMER = r'(\(.+?\)|[a-zA-Z_0-9]+|[0-9]+)\@(\d+)'  # Repeat the sequence for X frames / X/10 seconds
# (the hardcoded frame rate is 10 frames per second)
REGEX_SOUND = r' !([^,]+)'  # Play sound effect (group #1: sound name)
REGEX_FLIP_HORIZONTAL = r'<(.*)?'
REGEX_FLIP_VERTICAL = r'\^(.*)?'
REGEX_MASKING = r'\xBD'


class FASData:
    def __init__(self, fas_path, app):
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
            self.app.sequences[sequence['name']] = sequence['sequence']
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
    if regex.match(REGEX_RANDOM_CHOICES, __part):
        choices_weighted = regex.match(REGEX_RANDOM_CHOICES, __part).group(1).split('|')
        choices = []
        weights = []
        for i in choices_weighted:
            if regex.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i):
                choices.append(regex.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i).group(1))
                weights.append(int(regex.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i).group(2)))
            else:
                choices.append(i)
                weights.append(1)
        result = random.choices(choices, weights)[0]
        return parse_sequence_part(result, app)
    elif regex.match(REGEX_REPEAT, __part):
        str_groups = regex.match(REGEX_REPEAT, __part).groups()
        return [parse_sequence_part(str_groups[0], app) for i in range(int(str_groups[1]))]
    elif regex.match(REGEX_GROUP, __part):
        res0 = regex.match(REGEX_GROUP, __part).group(1)
        res1 = regex.match(REGEX_GROUP, __part).group(2)
        # print('LVL 1 GROUP:', __part)
        # print('LVL 2 GROUP:', regex.match(REGEX_GROUP, __part).group(1))
        result = [parse_sequence(res0, app)]
        if res1 != '':
            result.append(parse_sequence_part(res1, app))
        return result
    elif regex.match(REGEX_FLIP_HORIZONTAL, __part):
        # print(regex.match(REGEX_FLIP_HORIZONTAL, __part).group(1))
        res1 = regex.match(REGEX_FLIP_HORIZONTAL, __part).group(1)
        result =['FLIP_H']
        if res1 != '':
            result.append(parse_sequence_part(res1, app))
        return result
    elif regex.match(REGEX_FLIP_VERTICAL, __part):
        res1 = regex.match(REGEX_FLIP_VERTICAL, __part).group(1)
        result =['FLIP_V']
        if res1 != '':
            result.append(parse_sequence_part(res1, app))
        return result
    elif regex.match(REGEX_FRAME_RANGE, __part):
        frame_start, frame_end = int(regex.match(REGEX_FRAME_RANGE, __part).groups()[0]),\
            int(regex.match(REGEX_FRAME_RANGE, __part).groups()[1])
        frame_range = range(frame_start, (frame_end - 1) if (frame_end < frame_start) else (frame_end + 1),
                            -1 if (frame_end < frame_start) else 1)
        return [parse_sequence_part(str(i), app) for i in frame_range]
    elif regex.match(REGEX_FENCING, __part):
        # print(regex.match(REGEX_FENCING, __part))
        # print(__part, '(FENCING)')
        return 'FENCING'
    elif regex.match(REGEX_OFFSET, __part):
        offset = list(literal_eval(regex.match(REGEX_OFFSET, __part).group(1)))
        offset[1] *= -1
        part = regex.match(REGEX_OFFSET, __part).group(2)
        return [{'offset': Vector2(offset)}, parse_sequence_part(part, app)]
    elif regex.match(REGEX_SOUND, __part):
        return {'sound': regex.match(REGEX_SOUND, __part).group(1)}
    elif __part.isnumeric():
        # print(__part)
        return int(__part)
    else:
        # print(get_sequence(__part, app))
        return get_sequence(__part, app)
        # return __part


def parse_sequence(sequence, app):
    level = 0
    fence_open_close = 0  # 0 - open; 1 - close
    parts_orig = sequence.split(sep=',')  # old-school method
    # print(parts_orig)
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
    # print('')
    # print('PARTS:', parts)
    # parts = regex.findall(REGEX_COMMA_SEPARATION, sequence)
    # print('ORIG:',sequence,'\nPARTS:',parts)
    parts_parsed = []
    for x in parts:
        part_parsed = parse_sequence_part(x, app)
        if isinstance(part_parsed, list):
            [parts_parsed.append(part_parsed[i]) for i in range(len(part_parsed))]
        else:
            parts_parsed.append(part_parsed)
        # if regex.match(r'\[([0-9\,\-]+)\]', x): #check if
        #     pos_offset = literal_eval(regex.match(r'\[([0-9\,\-]+)\]', x).group(1))
        #     print(pos_offset)
        # print(x)
        # pass
    # print('PARSED PARTS:', parts_parsed)
    # return [parts_parsed[i] for i in range(len(parts_parsed))]
    return parts_parsed


def get_sequence(seq, app):  # INCOMPLETE
    sequence = app.sequences[seq]
    return parse_sequence(sequence, app)
