from animation_reader import FASReader
from bit_reader import *
import io
from pygame import Vector2
import re
from settings import *
from PIL import Image, ImageOps, ImageFile
from ast import literal_eval

REGEX_ADD_SPRITE = r'#([#-]+)?(.+[^,])'  # places a temporary extra sprite
# (group #1: absolute/relative positioning; group #2: sequence)
# REGEX_FENCING = r'©(?:\[(-?\d+)\,(-?\d+)\])?(\d[lcr]\d[tmb])\,(?:\[(-?\d+)\,(-?\d+)\])?(\d[lcr]\d[tmb])©'
REGEX_FENCING = r'©(?:\[(-?\d+,-?\d+)\])?(\d[lcr]\d[tmb])\,(?:\[(-?\d+,-?\d+)\])?(\d[lcr]\d[tmb])©'
REGEX_FLOATING = r'§(\d)\/(\d)'
REGEX_FRAME_RANGE = r'(\d+)-(\d+)'
REGEX_GROUP = r'^\((.+)\)([^\*\@]*)?$'
REGEX_LOAD_FAS = r'_([^,]+)'  # load external FAS file
REGEX_OFFSET = r'\[(-?\d+,-?\d+)\](.*)?'
REGEX_RANDOM_CHOICES = r'{(.+?)}(.*)?'
REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED = r'(.+)%(\d+)'
REGEX_REPEAT = r'(\(.+?\)|\w+?|\d+?)\*(\d+)'  # Repeat the sequence X times
REGEX_REPEAT_TIMER = r'(\([.]+?\)|\w+?|\d+?)\@(\d+)'  # Repeat the sequence for X frames / X/10 seconds
# (the hardcoded frame rate is 10 frames per second)
REGEX_SOUND = r' !([^,]+)'  # Play sound effect (group #1: sound name)
REGEX_UNNAMED_FUNCTION = r'!([^,]+)'
REGEX_FLIP_HORIZONTAL = r'<(.*)?'
REGEX_FLIP_VERTICAL = r'\^(.*)?'
REGEX_MASKING = r'\xBD(.*)?'


def flatten(s):
    if not s:
        return s
    if isinstance(s[0], list):
        return flatten(s[0]) + flatten(s[1:])
    return s[:1] + flatten(s[1:])


class FASData:
    def __init__(self, fas_path, app, extra=False, load_sequences=False):
        self.app = app
        self.reader = FASReader(fas_path)
        # if self.reader != 0:
        #     print('File read!')
        self.header = self.reader.header
        self.bitmap_infos = self.reader.bitmap_infos
        if hasattr(self.reader, 'touch'):
            self.touch = self.reader.touch
            self.touch['bpp'] = get_bit_depth(len(self.touch['colors']) - 1)
            self.touch['height'] = len(self.touch['bitmap']) // self.touch['width']
            self.app.touch = self.touch

        if hasattr(self.reader, 'extra_sprite_files'):
            self.extra_files = []
            for i in self.reader.extra_sprite_files['files']:
                self.extra_files.append(app.data_directory + i + '.FAS')
                # FASData(app.data_directory + i + '.FAS', app, True)
        self.sequences = {}
        for i in range(self.reader.seq_header['seq_count']):
            sequence = self.reader.read_sequence(i)
            self.sequences[sequence['name'].casefold()] = sequence['sequence']
        self.reader.close()
        self.frames = {}
        for i in range(self.reader.frames_header['count']):
            self.frames[self.reader.frames_header['id'][i]] = self.get_frame_masked(i)
            # self.frames[self.reader.frames_header['id'][i]] = {
            #     'bitmap': self.reader.frames_bitmap[i],
            #     'info': self.reader.frames_header['info'][i]
            # }
        for i in self.frames:
            if extra:
                # self.app.frames_extra[i] = self.get_frame_masked(i)
                self.app.frames_extra[i] = self.frames[i]
            else:
                # self.app.frames[i] = self.get_frame_masked(i)
                self.app.frames[i] = self.frames[i]
        if load_sequences:
            if extra:
                # self.app.sequences_extra.update(self.sequences)
                self.app.sequences_extra.update(self.sequences)
            else:
                self.app.sequences.update(self.sequences)

    def get_frame_bitmap(self, __frame, mask):
        # bitmap_info = self.reader.bitmap_infos[self.frames[__frame]['info'] * 2 + int(mask)]
        # bitmap = self.frames[__frame]['bitmap']
        bitmap_info = self.reader.bitmap_infos[self.reader.frames_header['info'][__frame] * 2 + int(mask)]
        bitmap = self.reader.frames_bitmap[__frame]
        header = b'BM' + int(len(bitmap_info) + len(bitmap) + 14).to_bytes(length=4, byteorder='little', signed=False) \
            + (0).to_bytes(length=2, byteorder='little', signed=False) \
            + (0).to_bytes(length=2, byteorder='little', signed=False) \
            + int(len(bitmap_info) + 14).to_bytes(length=4, byteorder='little', signed=False)
        data = header + bitmap_info + bitmap
        return data

    def get_frame_masked(self, __frame):
        color = self.get_frame_bitmap(__frame, mask=False)
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        result = Image.open(io.BytesIO(color)).convert('RGBA')
        mask = ImageOps.invert(Image.open(io.BytesIO(self.get_frame_bitmap(__frame, mask=True))).convert('L'))
        result.putalpha(mask)
        return result

ALIGNMENT_TO_SCREEN = {
    'l': 0,  # horizontal
    'c': WIDTH // 2,
    'r': WIDTH,
    't': 0,  # vertical
    'm': HEIGHT // 2,
    'b': HEIGHT}


class AddTempSprite:
    def __init__(self, seq_data, flags):
        self.seq_data = seq_data
        self.flags = flags


class SetFenceRegion:
    def __init__(self, alignments, modes, offsets):
        self.alignments = alignments
        self.modes = modes
        self.offsets = offsets


class FloatRandomVelocity:
    def __init__(self, h, v):
        self.h = h
        self.v = v


class RandomSeqPicker:
    def __init__(self, sequences, weights):
        self.sequences = sequences
        self.weights = weights


class SeqRepeat:
    def __init__(self, seq, repeats):
        self.seq = seq
        self.repeats = repeats

    def __repr__(self):
        return repr(self.seq) + ' * ' + repr(self.repeats)


class SeqRepeatTimer:
    def __init__(self, seq, duration):
        self.seq = seq
        self.duration = duration

    def __repr__(self):
        return repr(self.seq)+'@'+repr(self.duration)


def parse_sequence_part(__part):  # INCOMPLETE
    __part = __part.replace(' !', '‡')
    __part = __part.strip()
    __part = __part.replace('‡', ' !')
    if re.match(REGEX_RANDOM_CHOICES, __part):
        choices_weighted = re.match(REGEX_RANDOM_CHOICES, __part).group(1).split('|')
        after = re.match(REGEX_RANDOM_CHOICES, __part).group(2)
        choices = []
        weights = []
        for i in choices_weighted:
            if re.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i):
                choices.append(re.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i).group(1))
                weights.append(int(re.match(REGEX_RANDOM_CHOICES_CHOICE_WEIGHTED, i).group(2)))
            else:
                choices.append('('+i+')')  # failsafe
                weights.append(1)
        result = [RandomSeqPicker(choices, weights)]
        if after != '':
            result.append(parse_sequence_part(after))
        return result
    elif re.match(REGEX_GROUP, __part):
        res0 = re.match(REGEX_GROUP, __part).group(1)
        res1 = re.match(REGEX_GROUP, __part).group(2)
        result = [parse_sequence(res0)]
        if res1 != '':
            result.append(parse_sequence_part(res1))
        return result
    elif re.match(REGEX_ADD_SPRITE, __part):
        groups = re.match(REGEX_ADD_SPRITE, __part).groups()
        temp_spr_flags = 0
        if groups[0]:
            for i in groups[0]:
                if i == '-':
                    temp_spr_flags |= 1  # one layer back
                elif i == '#':
                    temp_spr_flags |= 2  # attach to the parent sprite
        return AddTempSprite([parse_sequence_part(groups[1])], temp_spr_flags)
        pass
    elif re.match(REGEX_FLOATING, __part):
        groups = re.match(REGEX_FLOATING, __part).groups()
        return FloatRandomVelocity(int(groups[0]), int(groups[1]))
    elif re.match(REGEX_REPEAT_TIMER, __part):
        str_groups = re.match(REGEX_REPEAT_TIMER, __part).groups()
        return SeqRepeatTimer(parse_sequence_part(str_groups[0]), int(str_groups[1]))
    elif re.match(REGEX_REPEAT, __part):
        str_groups = re.match(REGEX_REPEAT, __part).groups()
        return SeqRepeat(parse_sequence_part(str_groups[0]), int(str_groups[1]))
    elif re.match(REGEX_FLIP_HORIZONTAL, __part):
        res1 = re.match(REGEX_FLIP_HORIZONTAL, __part).group(1)
        result = [{'toggle_flag': 1}]
        if res1 != '':
            result.append(parse_sequence_part(res1))
        return result
    elif re.match(REGEX_FLIP_VERTICAL, __part):
        res1 = re.match(REGEX_FLIP_VERTICAL, __part).group(1)
        result = [{'toggle_flag': 2}]
        if res1 != '':
            result.append(parse_sequence_part(res1))
        return result
    elif re.match(REGEX_MASKING, __part):
        res1 = re.match(REGEX_MASKING, __part).group(1)
        result = [{'toggle_flag': 4}]
        if res1 != '':
            result.append(parse_sequence_part(res1))
        return result
    elif re.match(REGEX_FRAME_RANGE, __part):
        frame_start, frame_end = int(re.match(REGEX_FRAME_RANGE, __part).groups()[0]),\
            int(re.match(REGEX_FRAME_RANGE, __part).groups()[1])
        frame_range = range(frame_start, (frame_end - 1) if (frame_end < frame_start) else (frame_end + 1),
                            -1 if (frame_end < frame_start) else 1)
        return frame_range
    elif re.match(REGEX_FENCING, __part):
        values = list(re.match(REGEX_FENCING, __part).groups())
        alignments = []
        modes = []
        offsets = []
        for i in range(4):
            if i % 2 == 1:
                for j, value in enumerate(values[i]):
                    if j % 2 == 0:
                        modes.append(int(value))
                    else:
                        alignments.append(value)
            else:
                offsets.append([])
                if values[i]:
                    offsets[i >> 1] = list(literal_eval(values[i]))
                    offsets[i >> 1][1] *= -1 # flipping the Y coordinate
                    offsets[i >> 1] = Vector2(offsets[i >> 1])
        return SetFenceRegion(alignments, modes, offsets)
    elif re.match(REGEX_OFFSET, __part):
        offset = list(literal_eval(re.match(REGEX_OFFSET, __part).group(1)))
        offset[1] *= -1 # flipping the Y coordinate
        part = re.match(REGEX_OFFSET, __part).group(2)
        return [{'offset': Vector2(offset)}, parse_sequence_part(part)]
    elif re.match(REGEX_SOUND, __part):
        return {'sound': re.match(REGEX_SOUND, __part).group(1)}
    elif re.match(REGEX_UNNAMED_FUNCTION, __part):
        pass # dummy function
    elif re.match(REGEX_LOAD_FAS, __part):
        return {'load_fas': re.match(REGEX_LOAD_FAS, __part).group(1)}
    elif __part.isnumeric():
        return int(__part)
    else:
        return __part


def parse_sequence(sequence):
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
        if level == 0:
            if cur_part:
                parts.append(cur_part)
            cur_part = i
    parts_parsed = []
    for x in parts:
        part_parsed = parse_sequence_part(x)
        parts_parsed.append(part_parsed)
    return parts_parsed


def get_sequence(seq, app):  # INCOMPLETE
    if seq.casefold() in list(app.sequences.keys()):
        sequence = app.sequences[seq.casefold()]
    elif seq.casefold() in list(app.sequences_extra.keys()):
        sequence = app.sequences_extra[seq.casefold()]
    else:
        print('Sequence "' + seq + '" not found.')
        return 0
    return parse_sequence(sequence)
