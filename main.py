from audio_data import WASData
from animation_data import *
import pyaudio
import pygame as pg
import pygame.freetype as ft
import random
from settings import *
import struct
import sys
import wave
import os
import zlib


LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'


def pil_image_to_surface(pil_image, alpha=False):
    return pg.image.frombytes(
        pil_image.tobytes(), pil_image.size, pil_image.mode).convert_alpha() if alpha else pg.image.frombytes(
        pil_image.tobytes(), pil_image.size, pil_image.mode).convert()


def list_length_recursive(my_list):
    if my_list and (isinstance(my_list, list) or isinstance(my_list, int)):
        return 1 + list_length_recursive(my_list[1:])
    return 0


def flatten(s):
    if not s:
        return s
    if isinstance(s[0], list):
        return flatten(s[0]) + flatten(s[1:])
    return s[:1] + flatten(s[1:])


def sort_dict(my_dict):
    dict_keys = list(my_dict.keys())
    dict_keys.sort()
    return {i: my_dict[i] for i in dict_keys}


def debug_was_tool(audio_path):  # for reading .WAS files, that contain 16-bit PCM audio data
    chunk_length = 32  # for buffering
    sample_rate = 8000
    bit_depth = pyaudio.paInt16
    menu = {'1': 'Preview first 10 sounds',
            '2': 'Preview all sounds',
            '3': 'Extract all sounds to WAV',
            '4': 'Exit'}
    print('Loading WAS file...')
    audio_data = WASData(audio_path)
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print('File loaded:', audio_path + ';', '# of sounds:', len(audio_data.sounds))
        options = menu.keys()
        for entry in options:
            print(entry + '.', menu[entry])

        selection = input("Please Select: ")
        if (selection == '1') or (selection == '2'):
            p = pyaudio.PyAudio()
            stream = p.open(format=bit_depth,
                            channels=1,
                            rate=sample_rate,
                            output=True)
            for i in range(min(10 if selection == '1' else len(audio_data.sounds), len(audio_data.sounds))):
                cur_sound = audio_data.sounds[i]
                print('Now playing:', cur_sound['name'])
                j = 0
                while j < (len(cur_sound['data']) // chunk_length):  # buffering
                    stream.write(bytes(cur_sound['data'][j * chunk_length:(j + 1) * chunk_length]))
                    j += 1

                print(LINE_UP, end=LINE_CLEAR)

            stream.stop_stream()
            stream.close()
            p.terminate()
        elif selection == '3':
            for i in range(len(audio_data.sounds)):
                cur_sound = audio_data.sounds[i]
                print('Extracting', cur_sound['name'] + '...', end=' ')
                with wave.open(cur_sound['name'] + '.WAV', 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframesraw(bytes(cur_sound['data']))
                print('DONE!')

        elif selection == '4':
            break
        else:
            print("Unknown Option Selected!")


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
        faz_file = open(anim_name.upper() + '.FAZ', 'wb+')
        faz_file.write(struct.pack('i', len(anim_data)))
        faz_file.write(packed_data)
    finally:
        faz_file.close()


def faz_inflate(packed_path, save_to_file):
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
            anim_file = open(anim_name.upper() + '.FAS', 'wb+')
            anim_file.write(anim_data)
        finally:
            anim_file.close()
            return anim_name.upper() + '.FAS'
    else:
        return anim_data


class SpriteUnit(pg.sprite.Sprite):
    def __init__(self, handler, x, y):
        self.handler = handler
        self.x, self.y = x, y
        self.vel_x, self.vel_y = 0, 0
        super().__init__(handler.group)
        self.image_ind = 0
        self.image = self.handler.images[self.image_ind]
        self.rect = self.image.get_rect()
        self.rect.topleft = self.x, self.y
        self.fence_rect = pg.rect.Rect(0, 0, WIDTH, HEIGHT)
        self.flags = 0  # (1 - horizontal flip, 2 - vertical flip, 4 - masking)
        self.temporary = False
        self.parent_spr = None
        self.seq_name = ''
        self.seq_data = []
        self.seq_data_sub = []
        self.loop_count = 0
        self.timer_frames = 0
        self.repeats_highest_level = 0
        self.float_highest_level = 0

    def translate(self):
        self.x += self.vel_x
        self.y += self.vel_y
        if (self.x < self.fence_rect.left or (self.x + self.rect.width) > self.fence_rect.right)\
                and abs(self.vel_x) > 0:
            self.vel_x *= -1
            if self.x < self.fence_rect.left:
                self.x = self.fence_rect.left
            elif (self.x + self.rect.width) > self.fence_rect.right:
                self.x = self.fence_rect.right - self.rect.width
        if (self.y < self.fence_rect.top or (self.y + self.rect.height) > self.fence_rect.bottom)\
                and abs(self.vel_x) > 0:
            self.vel_y *= -1
            if self.y < self.fence_rect.top:
                self.y = self.fence_rect.top
            elif (self.y + self.rect.height) > self.fence_rect.bottom:
                self.y = self.fence_rect.bottom - self.rect.height

    def flip(self):
        if self.image_ind >= len(self.handler.images):
            temp_img = self.handler.images_extra[self.image_ind - len(self.handler.images)]
        else:
            temp_img = self.handler.images[self.image_ind]

        self.image = pg.transform.flip(temp_img, bool(self.flags & 1), bool(self.flags & 2))
        self.rect = self.image.get_rect()

    def update(self):
        x = None
        adding_sprite_data = None
        terminate_repeat = False
        if len(self.seq_data) > 0:
            while True:
                # print(len(self.seq_data))
                while not(self.seq_data[-1] or len(self.seq_data) <= 1):  # looping
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
                if (len(self.seq_data[-1])) > 0:
                    x = self.seq_data[-1].pop(0)
                    # print(self.seq_data)
                    if isinstance(x, list):  # grouping
                        if len(x) > 0:
                            self.seq_data.append(x)
                    elif isinstance(x, str):  # sequence shortcut
                        temp_seq = flatten(get_sequence(x, self.handler.app))
                        self.seq_data.append(temp_seq)
                    elif isinstance(x, AddTempSprite):  # adding co-sprites
                        adding_sprite_data = x
                    elif isinstance(x, FloatRandomVelocity):  # floating
                        self.float_highest_level = len(self.seq_data)
                        while self.vel_x == 0 and self.vel_y == 0:
                            self.vel_x = random.randrange(-x.h, x.h)
                            self.vel_y = random.randrange(-x.v, x.v)
                        # print(self.seq_data)
                    elif isinstance(x, RandomSeqPicker):
                        self.seq_data.append(flatten([parse_sequence_part(random.choices(x.sequences, x.weights,
                                                                                         k=1)[0])]))
                    elif isinstance(x, SeqRepeat):  # loop x times
                        self.loop_count = x.repeats
                        self.seq_data_sub = flatten([x.seq])
                        self.repeats_highest_level = len(self.seq_data) + 1
                        self.seq_data.append([])
                        # self.seq_data.append(self.seq_data_sub[:])
                    elif isinstance(x, SeqRepeatTimer):  # loop for X frames
                        self.seq_data_sub = flatten([x.seq])
                        self.timer_frames = x.duration
                        self.repeats_highest_level = len(self.seq_data)
                        self.seq_data.append([])
                    elif isinstance(x, dict):
                        if 'load_fas' in x:  # load external file
                            FASData(self.handler.app.work_dir + self.handler.app.work_dir.character + '\\Data\\'
                                    + x['load_fas'] + '.FAS', self.handler.app, True)
                            self.handler.images_extra = [pil_image_to_surface(self.handler.app.frames_extra[i], True)
                                                         for i in self.handler.app.frames_extra]
                        if 'toggle_flag' in x:  # sprite modification flags
                            self.flags ^= x['toggle_flag']
                        elif 'fence' in x:  # sprite fencing
                            self.fence_rect = x['fence']
                            self.x = min(max(self.x, self.fence_rect.left), (self.fence_rect.left
                                                                             + self.fence_rect.width
                                                                             - self.rect.width))
                            self.y = min(max(self.y, self.fence_rect.top), (self.fence_rect.top
                                                                            + self.fence_rect.height
                                                                            - self.rect.height))
                            # print(list(self.fence_rect))
                        elif 'sound' in x:  # playing sound (not functioning)
                            print(x)
                            # print(self.handler.app.sounds[x['sound'].upper()].get_raw()[:64])
                            # self.handler.app.sounds[x['sound'].upper()].play()
                        elif 'offset' in x:  # offsetting sprite
                            self.x += int(x['offset'].x)
                            self.y += int(x['offset'].y)
                            if len(self.handler.sprites) > 1:
                                for i in self.handler.sprites[1:]:
                                    if i.parent_spr == self:
                                        i.x += x['offset'].x
                                        i.y += x['offset'].y
                            if self.loop_count >= 1:  # terminate loop on colliding with the "fence"
                                if self.x < self.fence_rect.left or (self.x + self.rect.width) > self.fence_rect.right:
                                    if self.x < self.fence_rect.left:
                                        self.x = self.fence_rect.left
                                    elif (self.x + self.rect.width) > self.fence_rect.right:
                                        self.x = self.fence_rect.right - self.rect.width
                                    self.loop_count = 0
                                    terminate_repeat = True
                                if self.y < self.fence_rect.top or (self.y + self.rect.height) > self.fence_rect.bottom:
                                    if self.y < self.fence_rect.top:
                                        self.y = self.fence_rect.top
                                    elif (self.y + self.rect.height) > self.fence_rect.bottom:
                                        self.y = self.fence_rect.bottom - self.rect.height
                                    self.loop_count = 0
                                    terminate_repeat = True
                    elif isinstance(x, int):  # frame
                        # print(x, end='|')
                        if x in list(self.handler.app.frames_extra.keys()):
                            self.image_ind = list(self.handler.app.frames_extra.keys()).index(x)\
                                             + len(self.handler.app.frames)
                        else:
                            self.image_ind = list(self.handler.app.frames.keys()).index(x)
                        break
                else:
                    break

        if adding_sprite_data:
            if adding_sprite_data.flags & 1:
                temp_sprite = SpriteUnit(self.handler, WIDTH // 2, HEIGHT // 2)
            elif adding_sprite_data.flags & 2:
                temp_sprite = SpriteUnit(self.handler, self.x, self.y)
                temp_sprite.parent_spr = self
            else:
                temp_sprite = SpriteUnit(self.handler, 300, 300)
            temp_sprite.temporary = True
            # print(get_sequence(adding_sprite_data.seq_data[0], self.handler.app))
            temp_sprite.seq_data = [adding_sprite_data.seq_data]
            temp_sprite.update()
            if adding_sprite_data.flags & 1:
                temp_sprite.x -= (temp_sprite.rect.width // 2)
                temp_sprite.y -= (temp_sprite.rect.height // 2)
            self.handler.sprites.append(temp_sprite)
        if self.seq_data_sub:
            if self.loop_count == 0 and self.timer_frames == 0:
                self.seq_data_sub.clear()
                self.repeats_highest_level = 0
        if terminate_repeat:
            self.fence_rect = pg.rect.Rect(0, 0, WIDTH, HEIGHT)
            while len(self.seq_data) > self.repeats_highest_level:
                self.seq_data.pop()
        if len(self.seq_data) <= self.float_highest_level != 0:
            self.vel_x, self.vel_y = 0, 0
            self.float_highest_level = 0
        if self.timer_frames > 0:
            self.timer_frames -= 1

        self.translate()
        self.flip()
        self.rect.topleft = self.x, self.y
        if not self.seq_data:
            if self.temporary:
                # if self.ready_to_destroy:
                temp_sprite = self.handler.sprites.index(self)
                self.handler.sprites.pop(temp_sprite)
                self.kill()
                # else:
                #     self.ready_to_destroy = True
            else:
                # self.seq_name = 'idle'
                # self.seq_data = [get_sequence(self.seq_name, self.handler.app)]
                pass


class SpriteHandler:
    def __init__(self, app):
        self.app = app
        self.images = [pil_image_to_surface(app.frames[i], True)
                       for i in app.frames]
        self.images_extra = [pil_image_to_surface(app.frames_extra[i], True)
                             for i in app.frames_extra]
        self.group = pg.sprite.Group()
        self.sprites = []

    def add_sprite(self, x, y):
        self.sprites.append(SpriteUnit(handler=self, x=x, y=y))

    def update(self):
        self.group.update()

    def draw(self):
        self.group.draw(self.app.screen)


class App:
    def __init__(self):
        # pg.mixer.init(frequency=4000, size=-16, channels=1)
        pg.init()
        self.sequences = {}
        self.sequences_extra = {}
        self.frames = {}
        self.frames_extra = {}
        self.sounds = {}
        self.screen = pg.display.set_mode(WIN_SIZE)
        pg.display.set_caption('DeskMates sprite test')
        self.clock = pg.time.Clock()
        self.font = ft.SysFont('Courier New', FONT_SIZE)
        self.dt = 0.0
        loading_text_rect = self.font.get_rect('LOADING...', size=40)
        loading_text_rect.center = self.screen.get_rect().center
        self.font.render_to(self.screen, loading_text_rect, text='LOADING...', fgcolor='white',
                            style=ft.STYLE_STRONG + ft.STYLE_WIDE, rotation=0, size=40)
        pg.display.flip()
        self.work_dir = working_dir
        self.character = character
        FASData(file_name, self)
        # sort_dict(self.frames)
        self.sprite_handler = SpriteHandler(self)
        self.sprite_handler.images_extra = [pil_image_to_surface(self.frames_extra[i], True)
                                            for i in self.frames_extra]
        # self.sprite_handler.add_sprite(WIDTH // 2, HEIGHT // 2)
        self.sprite_handler.add_sprite(200, 200)
        self.sprite_handler.sprites[0].seq_name = 'do'
        self.sprite_handler.sprites[0].seq_data = [[self.sprite_handler.sprites[0].seq_name.upper()]]

    def update(self):
        pg.display.flip()
        if hasattr(self, 'sprite_handler'):
            self.sprite_handler.update()
        self.dt = self.clock.tick(10)

    def draw(self):
        self.screen.fill('gray64')
        if hasattr(self, 'sprite_handler'):
            for i in self.sprite_handler.sprites:
                self.sprite_handler.draw()
                # pg.draw.rect(self.screen, color='pink', rect=i.rect)
                pg.draw.lines(self.screen, color='red2', closed=True,
                              points=[i.fence_rect.topleft, i.fence_rect.topright,
                                      i.fence_rect.bottomright, i.fence_rect.bottomleft], width=1)  # fencing region
                pg.draw.lines(self.screen, color='green', closed=True,
                              points=[i.rect.topleft, i.rect.topright, i.rect.bottomright, i.rect.bottomleft],
                              width=1)
                self.font.render_to(self.screen, (i.rect.topleft[0] + 4, i.rect.topleft[1] + 4),
                                    text=f'{self.sprite_handler.sprites.index(i)}', fgcolor='white')
                self.font.render_to(self.screen, (i.rect.topleft[0] + 4, i.rect.topleft[1] + 4 + FONT_SIZE),
                                    text=f'X: {i.x}; Y: {i.y}', fgcolor='black', style=ft.STYLE_STRONG)
        # self.draw_fps()

    def draw_fps(self):
        fps_text = f'{self.clock.get_fps() :.0f} FPS'
        self.font.render_to(self.screen, (8, HEIGHT - 16), text=fps_text, fgcolor='black')
        if hasattr(self, 'sprite_handler'):
            seq_text = f'Current sequence: {self.sprite_handler.sprites[0].seq_name}'
            # frame_text = f'Current frame: {list(app.frames.keys())[self.sprite_handler.sprites[0].image_ind]:04d}'
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 2),
                                text=f'Sprites: {len(self.sprite_handler.sprites)}', fgcolor='black')
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 1), text=seq_text, fgcolor='black')
            # self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 1),
            #                     text='Repeated sequence level: '
            #                          + str(self.sprite_handler.sprites[0].repeats_highest_level),
            #                     fgcolor='black')
            # self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 2), text=frame_text, fgcolor='black')
        # self.font.render_to(self.screen, (8, HEIGHT - 16), text='Controls: ← - prev. frame; → - next frame; home - '
        #                                                         'first frame; end - last frame', fgcolor='black')

    def check_events(self):
        for e in pg.event.get():
            # if e.type == pg.KEYDOWN:
            #     if e.key == pg.K_RIGHT:
            #         if self.sprite_handler.sprites[0].image_ind < len(self.frames) - 1:
            #             self.sprite_handler.sprites[0].image_ind += 1
            #     elif e.key == pg.K_LEFT:
            #         if self.sprite_handler.sprites[0].image_ind > 0:
            #             self.sprite_handler.sprites[0].image_ind -= 1
            #     elif e.key == pg.K_HOME:
            #         self.sprite_handler.sprites[0].image_ind = 0
            #     elif e.key == pg.K_END:
            #         self.sprite_handler.sprites[0].image_ind = len(self.frames) - 1
            if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    frame_id = 3
    character = 'TestChar'
    working_dir = os.getcwd()
    file_name = 'TEST_FILE.FAS'
    app = App()
    app.run()
