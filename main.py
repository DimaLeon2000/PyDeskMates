import difflib

from audio_data import WASData
from animation_data import *
import configparser
import glob
from gui import *
import pygame as pg
import pygame.freetype as ft
import random
from settings import *
import struct
import sys
import os
import zlib


LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'
LOADING_TEXT = 'LOADING...'
ORIGINAL_FRAME_RATE = 10
TOUCH_STATES = ('up', 'down', 'start', 'loop', 'stop')
FAS_EXTENSION = '.fas'
FAZ_EXTENSION = '.faz'
FAS_WILDCARD = '*.fas'
FAZ_WILDCARD = '*.faz'
WAS_WILDCARD = '*.was'
WA3_WILDCARD = '*.wa3'
COMMON_FILENAME = 'common'
TOUCH_FILENAME = 'touch'
DEMO_SUFFIX = '_demo'
DEMAND_LOAD_ONLY_LIST_FILE = 'demand_load_only_list.txt'
NO_ALL_LIST_FILE = 'no_all_list.txt'
# FAS files that don't have the following sequences:
# "all", "all_demo", "all_fast", "all_fast_demo", "all_slow", and "all_slow_demo"
XTRA_LIST_FILE = 'xtra.txt'
# FAS/FAZ files that are exclusive to the Adult Mode


def pil_image_to_surface(pil_image, alpha=False):
    return pg.image.frombytes(
        pil_image.tobytes(), pil_image.size, pil_image.mode).convert_alpha() if alpha else pg.image.frombytes(
        pil_image.tobytes(), pil_image.size, pil_image.mode).convert()


def sort_dict(my_dict):
    dict_keys = list(my_dict.keys())
    dict_keys.sort()
    return {i: my_dict[i] for i in dict_keys}


# def debug_was_tool(audio_path):  # for reading .WAS files, that contain 16-bit PCM audio data
#     chunk_length = 32  # for buffering
#     sample_rate = 8000
#     bit_depth = pyaudio.paInt16
#     menu = {'1': 'Preview first 10 sounds',
#             '2': 'Preview all sounds',
#             '3': 'Extract all sounds to WAV',
#             '4': 'Exit'}
#     print('Loading WAS file...')
#     audio_data = WASData(audio_path)
#     while True:
#         os.system('cls' if os.name == 'nt' else 'clear')
#         print('File loaded:', audio_path + ';', '# of sounds:', len(audio_data.sounds))
#         options = menu.keys()
#         for entry in options:
#             print(entry + '.', menu[entry])
#
#         selection = input("Please Select: ")
#         if (selection == '1') or (selection == '2'):
#             p = pyaudio.PyAudio()
#             stream = p.open(format=bit_depth,
#                             channels=1,
#                             rate=sample_rate,
#                             output=True)
#             for i in range(min(10 if selection == '1' else len(audio_data.sounds), len(audio_data.sounds))):
#                 cur_sound = audio_data.sounds[i]
#                 print('Now playing:', cur_sound['name'])
#                 j = 0
#                 while j < (len(cur_sound['data']) // chunk_length):  # buffering
#                     stream.write(bytes(cur_sound['data'][j * chunk_length:(j + 1) * chunk_length]))
#                     j += 1
#
#                 print(LINE_UP, end=LINE_CLEAR)
#
#             stream.stop_stream()
#             stream.close()
#             p.terminate()
#         elif selection == '3':
#             for i in range(len(audio_data.sounds)):
#                 cur_sound = audio_data.sounds[i]
#                 print('Extracting', cur_sound['name'] + '...', end=' ')
#                 with wave.open(cur_sound['name'] + '.WAV', 'wb') as wf:
#                     wf.setnchannels(1)
#                     wf.setsampwidth(2)
#                     wf.setframerate(sample_rate)
#                     wf.writeframesraw(bytes(cur_sound['data']))
#                 print('DONE!')
#
#         elif selection == '4':
#             break
#         else:
#             print("Unknown Option Selected!")


def debug_fas_tool(anim_path, app):
    return FASData(anim_path, app, False)


def fas_deflate(anim_path):
    anim_name = os.path.splitext(os.path.basename(anim_path))[0]
    anim_file = open(anim_path, 'rb')
    anim_data = anim_file.read()
    anim_file.close()
    faz_file = 0
    packed_data = zlib.compress(anim_data)
    try:
        faz_file = open(anim_name.casefold() + FAZ_EXTENSION.casefold(), 'wb+')
        faz_file.write(struct.pack('i', len(anim_data)))
        faz_file.write(packed_data)
    finally:
        faz_file.close()


def faz_inflate(packed_path, save_to_file, save_location=''):
    anim_name = os.path.splitext(os.path.basename(packed_path))[0]
    packed_file = open(packed_path, 'rb')
    packed_file.seek(4)
    packed_data = packed_file.read()
    packed_file.close()
    anim_data = zlib.decompress(packed_data)
    anim_file = 0
    # if not (os.path.exists(anim_name + '.FAS')):
    if save_to_file:
        try:
            anim_file = open(save_location + anim_name.casefold().upper() + FAS_EXTENSION.upper(), 'wb+')
            anim_file.write(anim_data)
        finally:
            anim_file.close()
            return anim_name.casefold() + FAS_EXTENSION
    else:
        return anim_data


class SpriteUnit(pg.sprite.Sprite):
    def __init__(self, handler, x, y):
        self.handler = handler
        self.x, self.y = x, y
        self.vel_x, self.vel_y = 0, 0
        self.vel_max_x, self.vel_max_y = 0, 0
        super().__init__(handler.group)
        self.image_ind = [*self.handler.app.frames.keys()].index(3)
        self.image = self.handler.images[self.image_ind]
        self.rect = self.image.get_rect()
        self.rect.topleft = self.x, self.y
        self.fence_rect = None
        self.flags = 0  # (1 - horizontal flip, 2 - vertical flip, 4 - masking)
        self.temporary = False
        self.parent_spr = None
        self.anchored_to_parent = False
        # self.seq_name = ''
        self.seq_data = [[]]
        self.seq_data_sub = []
        self.touch_state = 0
        self.loop_count = 0
        self.terminate_repeat = False
        self.timer_frames = 0
        self.repeats_highest_level = 0
        self.float_highest_level = 0
        self.frame_delay = 0
        self.ready_to_load_sequences = False

    def translate(self):
        self.x += self.vel_x
        self.y += self.vel_y
        if self.fence_rect:
            if (self.x < self.fence_rect.left or (self.x + self.rect.width) > self.fence_rect.right)\
                    and self.vel_max_x > 0:
                if self.handler.app.settings['float_classic']:
                    if self.x < self.fence_rect.left:
                        self.x = self.fence_rect.left
                        self.vel_x = random.randrange(1, self.vel_max_x)
                        self.vel_y = random.randrange(-self.vel_max_y, self.vel_max_y)
                    elif (self.x + self.rect.width) > self.fence_rect.right:
                        self.x = self.fence_rect.right - self.rect.width
                        self.vel_x = random.randrange(-self.vel_max_x, -1)
                        self.vel_y = random.randrange(-self.vel_max_y, self.vel_max_y)
                else:
                    self.vel_x *= -1
                    if self.x < self.fence_rect.left:
                        self.x = self.fence_rect.left
                    elif (self.x + self.rect.width) > self.fence_rect.right:
                        self.x = self.fence_rect.right - self.rect.width
            if (self.y < self.fence_rect.top or (self.y + self.rect.height) > self.fence_rect.bottom)\
                    and self.vel_max_x > 0:
                if self.handler.app.settings['float_classic']:
                    if self.y < self.fence_rect.top:
                        self.y = self.fence_rect.top
                        self.vel_x = random.randrange(-self.vel_max_x, self.vel_max_x)
                        self.vel_y = random.randrange(1, self.vel_max_y)
                    elif (self.y + self.rect.height) > self.fence_rect.bottom:
                        self.y = self.fence_rect.bottom - self.rect.height
                        self.vel_x = random.randrange(-self.vel_max_x, self.vel_max_x)
                        self.vel_y = random.randrange(-self.vel_max_y, -1)
                else:
                    self.vel_y *= -1
                    if self.y < self.fence_rect.top:
                        self.y = self.fence_rect.top
                    elif (self.y + self.rect.height) > self.fence_rect.bottom:
                        self.y = self.fence_rect.bottom - self.rect.height

    def flip(self):
        # if self.image_ind >= len(self.handler.images):
        #     temp_img = self.handler.images_extra[self.image_ind - len(self.handler.images)]
        # else:
        try:
            temp_img = self.handler.images[self.image_ind]
        except IndexError:
            print(self.image_ind, '|',len(self.handler.images))
            self.image_ind = [*self.handler.app.frames.keys()].index(0)
            temp_img = self.handler.images[self.image_ind]
        self.image = pg.transform.flip(temp_img, bool(self.flags & 1), bool(self.flags & 2))
        self.rect = self.image.get_rect()
        self.rect.topleft = self.x, self.y

    def update(self):
        adding_sprite_data = None
        to_be_fenced = False
        if self.frame_delay > 0:
            # self.frame_delay -= self.handler.app.clock.tick(ORIGINAL_FRAME_RATE)
            self.frame_delay -= 1
            return False
        if len(self.seq_data) >= 1 and self.frame_delay <= 0:
            while True:
                # print(len(self.seq_data))
                while not self.seq_data[-1] and len(self.seq_data) > 1:  # looping
                    if self.timer_frames > 0 and len(self.seq_data) <= self.repeats_highest_level != 0:
                        # if len(self.seq_data) <= self.repeats_highest_level != 0:
                        if not self.seq_data[-1]:
                            self.seq_data[-1] = self.seq_data_sub[:]
                        break
                    elif self.loop_count > 0 and len(self.seq_data) <= self.repeats_highest_level != 0:
                        if not self.seq_data[-1]:
                            self.seq_data[-1] = self.seq_data_sub[:]
                        self.loop_count -= 1
                        break
                    else:
                        self.seq_data.pop()
                    if len(self.seq_data) <= self.float_highest_level != 0:
                        self.vel_x = 0
                        self.vel_y = 0
                        self.vel_max_x, self.vel_max_y = 0, 0
                        self.float_highest_level = 0
                if (len(self.seq_data[-1])) > 0:
                    x = self.seq_data[-1].pop(0)
                    # print(self.seq_data)
                    if isinstance(x, list):  # grouping
                        if len(x) > 0:
                            self.seq_data.append(flatten(x))
                    elif isinstance(x, str):  # sequence shortcut
                        x = x.casefold()
                        # print('Expected:', x)
                        if self.handler.app.settings['xtra'] and ((x + '_') in self.handler.app.sequences or
                                                                  (x + '_') in self.handler.app.sequences_extra):
                            # print('Got:', x + '_')
                            # print(get_sequence(x + '_', self.handler.app))
                            self.seq_data.append(get_sequence(x + '_', self.handler.app))
                        else:
                            # print('Got:', x)
                            # print(get_sequence(x, self.handler.app))
                            self.seq_data.append(get_sequence(x, self.handler.app))
                    elif isinstance(x, range):
                        j = 0
                        for i in x:
                            self.seq_data[-1].insert(j, i)
                            j += 1
                    elif isinstance(x, AddTempSprite):  # adding co-sprites
                        adding_sprite_data = x
                    elif isinstance(x, FloatRandomVelocity):  # floating
                        self.float_highest_level = len(self.seq_data) - 1
                        self.vel_max_x, self.vel_max_y = x.h, x.v
                        while self.vel_x == 0 and self.vel_y == 0:
                            self.vel_x = random.randrange(-self.vel_max_x, self.vel_max_x)
                            self.vel_y = random.randrange(-self.vel_max_y, self.vel_max_y)
                        # print(self.seq_data)
                    elif isinstance(x, RandomSeqPicker):
                        self.seq_data.append(flatten([parse_sequence_part(random.choices(x.sequences, x.weights,
                                                                                         k=1)[0])]))
                    elif isinstance(x, SetFenceRegion):
                        alignment_to_sprite_home = {
                            'l': self.handler.app.settings['home_pos'][0],  # horizontal
                            'c': self.handler.app.settings['home_pos'][0] + self.rect.width // 2,
                            'r': self.handler.app.settings['home_pos'][0] + self.rect.width,
                            't': self.handler.app.settings['home_pos'][1],  # vertical
                            'm': self.handler.app.settings['home_pos'][1] + self.rect.height // 2,
                            'b': self.handler.app.settings['home_pos'][1] + self.rect.height}
                        if not self.fence_rect:
                            self.fence_rect = pg.rect.Rect(0, 0, 0, 0)
                        if not x.offsets:
                            x.offsets = [pg.Vector2(0,0), pg.Vector2(0,0)]
                        for i in range(4):
                            if x.modes[i] == 1:
                                value = alignment_to_sprite_home[x.alignments[i]]
                                if len(x.offsets[i >> 1]) > 0:
                                    value += x.offsets[i >> 1][i % 2]
                            elif x.modes[i] == 3 and self.parent_spr:
                                alignment_to_sprite_parent = {
                                    'l': self.parent_spr.x,  # horizontal
                                    'c': self.parent_spr.x + self.rect.width // 2,
                                    'r': self.parent_spr.x + self.rect.width,
                                    't': self.parent_spr.y,  # vertical
                                    'm': self.parent_spr.y + self.rect.height // 2,
                                    'b': self.parent_spr.y + self.rect.height}
                                value = alignment_to_sprite_parent[x.alignments[i]]
                                if len(x.offsets[i >> 1]) > 0:
                                    value += x.offsets[i >> 1][i % 2]
                            else:
                                value = ALIGNMENT_TO_SCREEN[x.alignments[i]]
                                if len(x.offsets[i >> 1]) > 0:
                                    value += x.offsets[i >> 1][i % 2]
                                # print(value)
                            if i == 0:
                                self.fence_rect.left = value
                            elif i == 1:
                                self.fence_rect.top = value
                            elif i == 2:
                                self.fence_rect.width = value - self.fence_rect.left
                            elif i == 3:
                                self.fence_rect.height = value - self.fence_rect.top
                        if not self.fence_rect.contains(self.rect):
                            to_be_fenced = True
                    elif isinstance(x, SeqRepeat):  # loop x times
                        if x.repeats > self.loop_count:
                            self.loop_count = int(x.repeats)
                        self.seq_data_sub = flatten([x.seq][:])
                        self.repeats_highest_level = len(self.seq_data) + 1
                        self.seq_data.append([])
                        # self.seq_data.append(self.seq_data_sub[:])
                    elif isinstance(x, SeqRepeatTimer):  # loop for X frames
                        self.seq_data_sub = flatten([x.seq][:])
                        self.timer_frames = int(x.duration)
                        self.repeats_highest_level = len(self.seq_data) + 1
                        self.seq_data.append([])
                    elif isinstance(x, dict):
                        if 'load_fas' in x:  # load external file
                            if x['load_fas'].casefold()+FAS_EXTENSION in self.handler.app.demand_load_only_list:
                                FASData(self.handler.app.data_directory + x['load_fas'] + FAS_EXTENSION, self.handler.app,
                                    True, True)
                                self.handler.update_frames()
                        if 'toggle_flag' in x:  # sprite modification flags
                            self.flags ^= x['toggle_flag']
                        elif 'sound' in x:  # playing sound
                            # print(x)
                            if self.handler.app.settings['sound_on']:
                                if x['sound'].casefold() in self.handler.app.sounds:
                                    self.handler.app.sounds[x['sound'].casefold()].play()
                                else:
                                    for i in self.handler.app.sounds.keys():
                                        if difflib.SequenceMatcher(None, x['sound'].casefold(), i).ratio() >= 0.8:
                                            x['sound'] = i
                                            self.handler.app.sounds[x['sound'].casefold()].play()
                                            break
                        elif 'offset' in x:  # offsetting sprite
                            self.x += int(x['offset'].x)
                            self.y += int(x['offset'].y)
                            if len(self.handler.sprites) >= 1:
                                for i in self.handler.sprites:
                                    if i.parent_spr == self and i.anchored_to_parent:
                                        i.x += int(x['offset'].x)
                                        i.y += int(x['offset'].y)
                            if self.loop_count >= 1:  # terminate loop on colliding with the "fence"
                                if self.fence_rect:
                                    if not self.fence_rect.contains(self.rect):
                                        self.rect.clamp_ip(self.fence_rect)
                                        self.x, self.y = self.rect.left, self.rect.top
                                        for i in self.handler.sprites:
                                            i.terminate_repeat = True
                    elif isinstance(x, int):  # frame
                        # print(x, end='|')
                        if x in list(self.handler.app.frames_extra.keys()):
                            self.image_ind = list(self.handler.app.frames_extra.keys()).index(x) \
                                             + len(self.handler.app.frames)
                        elif x in list(self.handler.app.frames.keys()):
                            self.image_ind = list(self.handler.app.frames.keys()).index(x)
                        self.flip()
                        if to_be_fenced:
                            to_be_fenced = False
                            self.rect.clamp_ip(self.fence_rect)
                            # self.rect.topleft = self.fence_rect.topleft
                            # self.rect.left -= max(0, self.rect.width - self.fence_rect.width)
                            # self.rect.top  -= max(0, self.rect.height - self.fence_rect.height)
                            self.fence_rect = None
                        self.x, self.y = self.rect.left, self.rect.top
                        break
                else:
                    break
        if adding_sprite_data:
            # if adding_sprite_data.flags & 1:
            #     temp_sprite = SpriteUnit(self.handler, 0, 0)
            if adding_sprite_data.flags & 2:
                temp_sprite = SpriteUnit(self.handler, self.x, self.y)
                temp_sprite.anchored_to_parent = True
            else:
                temp_sprite = SpriteUnit(self.handler, 300, 300)
            temp_sprite.parent_spr = self
            temp_sprite.temporary = True
            temp_sprite.vel_x, temp_sprite.vel_y = self.vel_x, self.vel_y
            temp_sprite.vel_max_x, temp_sprite.vel_max_y = self.vel_max_x, self.vel_max_y
            # print(get_sequence(adding_sprite_data.seq_data[0], self.handler.app))
            temp_sprite.seq_data = [adding_sprite_data.seq_data]
            temp_sprite.update()
            if adding_sprite_data.flags & 1:  # adding the sprite behind is not working
                self.handler.sprites.insert(max(0, len(self.handler.sprites) - 1), temp_sprite)
            else:
                self.handler.sprites.append(temp_sprite)
        if self.terminate_repeat:
            self.loop_count = 0
            self.timer_frames = 0
            self.fence_rect = None
            while (len(self.seq_data) > 1) and len(self.seq_data) >= self.repeats_highest_level:
                self.seq_data.pop()
            self.terminate_repeat = False
            self.repeats_highest_level = 0
        if self.seq_data_sub:
            if self.loop_count == 0 and self.timer_frames == 0:
                self.seq_data_sub.clear()

        self.translate()
        if self.frame_delay <= 0:
            # self.frame_delay = 50
            self.frame_delay += max(0, (FRAME_RATE + ORIGINAL_FRAME_RATE / 2) // ORIGINAL_FRAME_RATE - 1,
                                    (self.handler.app.clock.get_fps() + ORIGINAL_FRAME_RATE / 2) //
                                    ORIGINAL_FRAME_RATE - 1)
        if self.ready_to_load_sequences:
            is_demo = self.handler.app.settings['simulate_demo']
            self.ready_to_load_sequences = False
            self.handler.app.remove_unpacks()
            self.handler.app.load_idle_sequence()
            if 'all' in self.handler.app.sequences_extra or 'all_demo' in self.handler.app.sequences_extra:
                self.seq_data[0].append(get_sequence('all_demo', self.handler.app)) \
                if is_demo and 'all_demo' in self.handler.app.sequences_extra \
                else self.seq_data[0].append(get_sequence('all', self.handler.app))
            elif 'all_slow' in self.handler.app.sequences_extra \
                or 'all_slow_demo' in self.handler.app.sequences_extra:
                self.seq_data[0].append(get_sequence('all_slow_demo', self.handler.app)) \
                if is_demo and 'all_slow_demo' in self.handler.app.sequences_extra\
                else self.seq_data[0].append(get_sequence('all_slow', self.handler.app))
        if len(self.seq_data) == 1 and (not self.seq_data[0]):
            if self.temporary:
                temp_sprite = self.handler.sprites.index(self)
                self.handler.sprites.pop(temp_sprite)
                self.kill()
            else:
                if self.touch_state == 1:
                    if self.handler.app.clicked_sprite == self:
                        self.touch_state = 2
                    else:
                        self.touch_state = 0
                    self.seq_data = [[self.handler.app.touch_color + TOUCH_STATES[self.touch_state]]]
                elif self.touch_state == 2:
                    if self.handler.app.clicked_sprite == self:
                        self.touch_state = 3
                    else:
                        self.touch_state = 4
                    self.seq_data = [[self.handler.app.touch_color + TOUCH_STATES[self.touch_state]]]
                    if self.touch_state == 4:
                        self.touch_state = 0
                elif self.touch_state == 3:
                    if not self.handler.app.clicked_sprite:
                        self.touch_state = 4
                    self.seq_data = [[self.handler.app.touch_color + TOUCH_STATES[self.touch_state]]]
                    if self.touch_state == 4:
                        self.touch_state = 0
                else:
                    # self.seq_name = 'idle'
                    is_demo = self.handler.app.settings['simulate_demo']
                    self.seq_data = [get_sequence('idle_demo', self.handler.app)
                                     if is_demo
                                     else get_sequence('idle', self.handler.app)]
                    self.ready_to_load_sequences = True
                # pass


class SpriteHandler:
    def __init__(self, app):
        self.app = app
        self.images = [pil_image_to_surface(app.frames[i], True)
                       for i in app.frames]
        self.group = pg.sprite.Group()
        self.sprites = []

    def add_sprite(self, x, y):
        self.sprites.append(SpriteUnit(handler=self, x=x, y=y))

    def update(self):
        self.group.update()
        for i in self.sprites:
            if not i.flags & 4:  # masking
                for j in self.sprites:
                    if j.parent_spr == i and j.flags & 4:
                        i.image.blit(source=j.image, dest=(j.x - i.x, j.y - i.y), special_flags=pg.BLEND_RGBA_SUB)

    def update_frames(self):
        self.images = [pil_image_to_surface(app.frames[i], True) for i in app.frames]
        if self.app.frames_extra:
            [self.images.append(pil_image_to_surface(app.frames_extra[i], True)) for i in app.frames_extra]

    def draw(self):
        for i in self.sprites:
            if not i.flags & 4:
                # pg.draw.rect(self.app.screen, color='pink', rect=i.rect)
                self.app.screen.blit(i.image, (i.rect.left, i.rect.top))
                if i.fence_rect:
                    pg.draw.rect(self.app.screen, color='red2', rect=i.fence_rect, width=1)
                #     pg.draw.lines(self.app.screen, color='red2', closed=True,
                #                   points=[i.fence_rect.topleft, i.fence_rect.topright,
                #                           i.fence_rect.bottomright, i.fence_rect.bottomleft], width=1)  # fencing region
                # pg.draw.lines(self.app.screen, color='green', closed=True,
                #               points=[i.rect.topleft, i.rect.topright, i.rect.bottomright, i.rect.bottomleft],
                #               width=1)
                # self.app.font.render_to(self.app.screen, (i.rect.topleft[0] + 4, i.rect.topleft[1] + 4),
                #                         text=f'{i.image_ind}', fgcolor='white')
                self.app.font.render_to(self.app.screen, (i.rect.topleft[0] + 4, i.rect.topleft[1] + 4),
                                        text=f'{self.sprites.index(i)}', fgcolor='white')
                self.app.font.render_to(self.app.screen, (i.rect.topleft[0] + 4, i.rect.topleft[1] + 4 + FONT_SIZE),
                                        text=f'X: {i.x}; Y: {i.y}', fgcolor='black')


class App:
    def __init__(self):
        self.sample_rate = 48000
        pg.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=1024)
        pg.init()
        self.sequences = {}
        self.sequences_extra = {}
        self.frames = {}
        self.frames_extra = {}
        self.sounds = {}
        self.clicked_sprite = None
        self.touch_color = ''
        self.demand_load_only_list = []
        self.no_all_list = []
        self.sequence_files = []
        self.adult_mode_list = []
        self.settings = {
            'home_pos': (WIDTH // 2, HEIGHT // 2),
            'float_classic': False,
            'limbo': False,
            'simulate_demo': False,
            'sound_on': True,
            'xtra': True
        }
        self.config = configparser.ConfigParser()
        if os.path.isfile(config_filename):
            self.config.read(config_filename)
            if 'MainSpritePos' in self.config['DEFAULT']:
                self.settings['home_pos'] = tuple(map(int,self.config['DEFAULT']['MainSpritePos'].split('|')))
            if 'ClassicFloat' in self.config['Compatibility']:
                self.settings['float_classic'] = bool(int(self.config['Compatibility']['ClassicFloat']))
            if 'Limbofy' in self.config['DEFAULT']:
                self.settings['limbo'] = bool(int(self.config['DEFAULT']['Limbofy']))
            if 'SimulateDemoVersion' in self.config['DEFAULT']:
                self.settings['simulate_demo'] = bool(int(self.config['DEFAULT']['SimulateDemoVersion']))
            if 'SoundOn' in self.config['DEFAULT']:
                self.settings['sound_on'] = bool(int(self.config['DEFAULT']['SoundOn']))
            if 'Xtra' in self.config['DEFAULT']:
                self.settings['xtra'] = bool(int(self.config['DEFAULT']['Xtra']))
        self.screen = pg.display.set_mode(WIN_SIZE)
        pg.display.set_caption('PyDeskMates [WORK IN PROGRESS]')
        self.clock = pg.time.Clock()
        self.font = ft.SysFont('Courier New', FONT_SIZE)
        self.dt = 0.0
        loading_text_rect = self.font.get_rect(LOADING_TEXT, size=FONT_SIZE * 4, style=ft.STYLE_STRONG)
        loading_text_rect.center = self.screen.get_rect().center
        self.font.render_to(self.screen, loading_text_rect, text=LOADING_TEXT, fgcolor='white',
                            rotation=0, size=FONT_SIZE * 4, style=ft.STYLE_STRONG)
        pg.display.flip()
        self.working_directory = working_directory
        self.character = character
        self.data_directory = working_directory + '\\' + character + '\\Data\\'
        self.load_character()
        # FASData(self.work_dir + self.character + '\\Data\\' + i, self)

        self.sprite_handler = SpriteHandler(self)
        self.sprite_handler.add_sprite(WIDTH // 2, HEIGHT // 2)
        # self.sprite_handler.sprites[0].seq_name =
        # self.sprite_handler.sprites[0].seq_name = 'all'
        # self.sprite_handler.sprites[0].temporary = True
        self.sprite_handler.sprites[0].seq_data = [['S_Deskmate_Enter'.casefold()]]
        # self.sprite_handler.sprites[0].seq_data = [['T0x404040DOWN','T0x404040START',
        #                                             SeqRepeat('T0x404040LOOP',10),'T0x404040STOP']]
        self.menu = ButtonMenu(self)
        # self.menu.add_button(text='Settings')
        # self.menu.add_button(text='Sound on', checkbox=True)
        # self.menu.buttons[1].checked = self.settings['sound_on']
        # self.menu.buttons[1].callback = self.toggle_sound_setting
        # self.menu.add_button(text='Classic floating', checkbox=True)
        # self.menu.buttons[2].checked = self.settings['float_classic']
        # self.menu.buttons[2].callback = self.toggle_float_setting
        # self.menu.add_button(text='Adult mode', checkbox=True)
        # self.menu.buttons[3].checked = self.settings['xtra']
        # self.menu.buttons[3].callback = self.toggle_adult_mode_setting
        # self.menu.set_position([i - j for i, j in zip(list(WIN_SIZE), self.menu.get_size())])
        self.running = True


    def load_character(self):
        for file in glob.glob(WAS_WILDCARD, root_dir = self.data_directory):
            was_file = WASData(self.data_directory + file, self, False)
            for i in was_file.sounds:
                self.sounds[i] = was_file.sounds[i]
            # del was_file
        for file in glob.glob(WA3_WILDCARD, root_dir = self.data_directory):
            was_file = WASData(self.data_directory + file, self, True)
            for i in was_file.sounds:
                self.sounds[i] = was_file.sounds[i]
            # del was_file
        if os.path.exists(self.data_directory + DEMAND_LOAD_ONLY_LIST_FILE)\
            and os.path.isfile(self.data_directory + DEMAND_LOAD_ONLY_LIST_FILE):
            self.demand_load_only_list = [i.strip('\n').casefold() for i in open(self.data_directory
                                                                            + DEMAND_LOAD_ONLY_LIST_FILE)]
            self.main_fas_files = [*filter(lambda load_only: not load_only.casefold() in self.demand_load_only_list,
                                        glob.glob(FAS_WILDCARD, root_dir = self.data_directory))]
        else:
            self.main_fas_files = [*glob.glob(FAS_WILDCARD, root_dir = self.data_directory)]
        if os.path.exists(self.data_directory + NO_ALL_LIST_FILE)\
                and os.path.isfile(self.data_directory + NO_ALL_LIST_FILE):
            self.no_all_list = [i.strip('\n').casefold() for i in open(self.data_directory
                                                                            + NO_ALL_LIST_FILE)]

        if os.path.exists(self.data_directory + XTRA_LIST_FILE)\
                and os.path.isfile(self.data_directory + XTRA_LIST_FILE):
            self.adult_mode_list = [i.strip('\n').casefold() for i in open(self.data_directory
                                                                            + XTRA_LIST_FILE)]
        self.sequence_files = [i.casefold() for i in glob.glob(FAZ_WILDCARD, root_dir = self.data_directory)]
        for file in self.main_fas_files.__reversed__():
            file_data = FASData(self.data_directory + file, self)
            if file.casefold().startswith(TOUCH_FILENAME):
                if not(file.casefold().endswith(DEMO_SUFFIX + FAS_EXTENSION)) != self.settings['simulate_demo']:
                        self.sequences.update(file_data.sequences)
            else:
                self.sequences.update(file_data.sequences)


    def load_idle_sequence(self):
        self.frames_extra.clear()
        self.sequences_extra.clear()
        self.sprite_handler.update_frames()
        seq_list = [*filter(lambda x: x != 'email.faz', self.sequence_files)]
        seq_list.extend([*filter(lambda x: not x in self.no_all_list, self.demand_load_only_list)])
        if not self.settings['xtra']:
            seq_list = [*filter(lambda x: not x.startswith(tuple(self.adult_mode_list)), seq_list)]
        seq_file = random.choice(seq_list)
        if seq_file.endswith(FAZ_EXTENSION):
            if not os.path.exists(self.working_directory + r'\unpack\\'):
                os.mkdir(self.working_directory + r'\unpack\\')
            seq_file = faz_inflate(self.data_directory + seq_file, True,
                                   save_location=self.working_directory + r'\unpack\\')
            FASData(self.working_directory + r'\unpack\\' + seq_file, self, True, True)
        elif seq_file.endswith(FAS_EXTENSION):
            FASData(self.data_directory + seq_file, self, True, True)
        self.sprite_handler.update_frames()


    def remove_unpacks(self):
        if not os.path.exists(self.working_directory + r'\unpack\\'):
            return
        folder = self.working_directory + r'\unpack\\'
        for file in os.listdir(folder):
            filepath = os.path.join(folder, file)
            try:
                if os.path.isfile(filepath) or os.path.islink(filepath):
                    os.unlink(filepath)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (filepath, e))

    def toggle_adult_mode_setting(self, sender):
        self.settings['xtra'] = sender.checked


    def toggle_float_setting(self, sender):
        self.settings['float_classic'] = sender.checked


    def toggle_sound_setting(self, sender):
        self.settings['sound_on'] = sender.checked


    def update(self):
        pg.display.flip()
        if hasattr(self, 'sprite_handler'):
            self.sprite_handler.update()
        self.dt = self.clock.tick(FRAME_RATE)

    def draw(self):
        self.screen.fill('gray64')
        if hasattr(self, 'sprite_handler'):
            self.sprite_handler.draw()
        self.draw_fps()
        # self.touch_image.draw(self.screen)
        self.menu.draw(self.screen)

    def draw_fps(self):
        fps_text = f'{self.clock.get_fps() :.0f} FPS'
        self.font.render_to(self.screen, (8, HEIGHT - 16), text=fps_text, fgcolor='black')
        if hasattr(self, 'sprite_handler'):
            # seq_text = f'Current sequence: {self.sprite_handler.sprites[0].seq_name}'
            # seq_text = f'Current sequence: {self.sprite_handler.sprites[0].seq_data[0][0]}'
            # frame_text = f'Current frame: {list(app.frames.keys())[self.sprite_handler.sprites[0].image_ind]:04d}'
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 4),
                                text=f'Simulate demo version: {str(self.settings["simulate_demo"])}', fgcolor='black')
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 3),
                                text=f'Sprites: {len(self.sprite_handler.group)}', fgcolor='black')
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 2),
                                text=f'Classic floating: {self.settings["float_classic"]}', fgcolor='black')
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 1),
                                text=f'Clicked sprite: {self.clicked_sprite}', fgcolor='black')
            # self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 2), text=seq_text, fgcolor='black')
            # self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 1),
            #                     text='Repeated sequence level: '
            #                          + str(self.sprite_handler.sprites[0].repeats_highest_level),
            #                     fgcolor='black')
            # self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 2), text=frame_text, fgcolor='black')
        # self.font.render_to(self.screen, (8, HEIGHT - 16), text='Controls: ← - prev. frame; → - next frame; home - '
        #                                                         'first frame; end - last frame', fgcolor='black')

    def check_events(self):
        for e in pg.event.get():
            mouse_pos = pg.mouse.get_pos()
            self.menu.check_events(e)
            if e.type == pg.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if hasattr(self, 'sprite_handler'):
                        for s in reversed(self.sprite_handler.sprites):
                            if s.rect.collidepoint(mouse_pos) and\
                                bool(s.image.get_at((mouse_pos[0] - s.x, mouse_pos[1] - s.y))[3] >> 7 % 2):
                                self.clicked_sprite = s
                                break
                        if self.clicked_sprite:
                            for i in self.sounds:
                                self.sounds[i].stop()
                            for i, sprite in enumerate(self.sprite_handler.group.sprites()):
                                if i == 0:
                                    sprite.x, sprite.y = self.clicked_sprite.x, self.clicked_sprite.y
                                    self.clicked_sprite = sprite
                                    if hasattr(self, 'touch'):  # "touch" reaction
                                        for j in range(self.touch['height']):
                                            for k in range(self.touch['width']):
                                                for l, value in enumerate(read_bits_per_pixel(self.touch['bitmap']
                                                                             [k + j * self.touch['width']],
                                                                             self.touch['bpp'])):
                                                    if (k * (8 // self.touch['bpp']) + l) ==\
                                                            min(max(0, mouse_pos[0] - sprite.x),
                                                                self.touch['width'] * (8 // self.touch['bpp']) - 1)\
                                                    and (self.touch['height'] - j - 1) ==\
                                                        min(max(0, (mouse_pos[1] - sprite.y)),
                                                            self.touch['height'] - 1):
                                                        if self.settings['limbo']:
                                                            self.touch_color = 'updaterequired_'
                                                        else:
                                                            self.touch_color = 'T' + read_rgb_to_hex(self.\
                                                                                                     touch['colors']\
                                                                                                         [value],
                                                                                                     True)
                                                        sprite.touch_state = 1
                                                        sprite.seq_data =[[0, self.touch_color
                                                                           + TOUCH_STATES[sprite.touch_state]]]
                                else:
                                    sprite.seq_data = [[]]
                                sprite.flags = 0
                                sprite.seq_data_sub = []
                                sprite.loop_count = 0
                                sprite.terminate_repeat = False
                                sprite.timer_frames = 0
                                sprite.repeats_highest_level = 0
                                sprite.float_highest_level = 0
                                sprite.frame_delay = 0
                                sprite.vel_x, sprite.vel_y = 0, 0
                                sprite.vel_max_x, self.vel_max_y = 0, 0
                                sprite.float_highest_level = 0
                                sprite.fence_rect = pg.rect.Rect(-sprite.rect.width, -sprite.rect.height,
                                                                 WIDTH + sprite.rect.width, HEIGHT + sprite.rect.height)
                                self.remove_unpacks()
                                self.frames_extra.clear()
                                self.sequences_extra.clear()
            elif e.type == pg.MOUSEMOTION:
                if self.clicked_sprite:
                    self.clicked_sprite.x += e.rel[0]
                    self.clicked_sprite.y += e.rel[1]
                    self.settings['home_pos'] = self.clicked_sprite.x, self.clicked_sprite.y
                    self.clicked_sprite.rect.topleft = self.clicked_sprite.x, self.clicked_sprite.y
            elif e.type == pg.MOUSEBUTTONUP:
                if e.button == 1:
                    if self.clicked_sprite:
                        self.settings['home_pos'] = self.clicked_sprite.x, self.clicked_sprite.y
                        self.clicked_sprite = None
            if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                self.running = False

    def run(self):
        while self.running:
            self.check_events()
            self.update()
            self.draw()
        self.config['DEFAULT'] = {'MainSpritePos': '|'.join(map(str,self.settings['home_pos'])),
                                  'Limbofy': str(int(self.settings['limbo'])),
                                  'SimulateDemoVersion': str(int(self.settings['simulate_demo'])),
                                  'SoundOn': str(int(self.settings['sound_on'])),
                                  'Xtra': str(int(self.settings['xtra']))}
        self.config['Compatibility'] = {'ClassicFloat': str(int(self.settings['float_classic']))}
        with open(config_filename, 'w') as saving_configfile:
            self.config.write(saving_configfile)
            saving_configfile.close()
        self.remove_unpacks()
        pg.quit()
        sys.exit()


if __name__ == '__main__':
    character = 'TestChar'
    working_directory = os.getcwd()
    config_filename = 'config.ini'
    app = App()
    app.run()
