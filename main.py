from audio_data import WASData
from animation_data import *
# from bit_reader import *
# import PIL
import pyaudio
import pygame as pg
import pygame.freetype as ft
from settings import *
import struct
import sys
# import tkinter
import wave
import os
import zlib


LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'


def pil_image_to_surface(pil_image):
    return pg.image.frombytes(
        pil_image.tobytes(), pil_image.size, pil_image.mode).convert_alpha()


def flatten(spam):
    for x in spam:
        if hasattr(x, '__iter__') and not isinstance(x, str) and not isinstance(x, dict):
            for y in flatten(x):
                yield y
        else:
            if x != '':
                yield x


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
    return FASData(anim_path, app)


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
        super().__init__(handler.group)
        self.image_ind = handler.app.frame_num
        self.image = self.handler.images[handler.app.frame_num]
        self.rect = self.image.get_rect()
        self.flips = 0
        # print(self.rect)
        self.seq_name = ''
        self.seq_data = []
        self.seq_level = 0

    def flip(self):
        self.image = pg.transform.flip(self.handler.images[self.image_ind], bool(self.flips & 1), bool(self.flips & 2))
        self.rect = self.image.get_rect()

    def update(self):
        x = ''
        if (len(self.seq_data[self.seq_level])) > 0:
            while not(isinstance(x, int)):
                x = self.seq_data[self.seq_level].pop(0)
                if isinstance(x, list):
                    self.seq_level += 1
                    self.seq_data.append(x)
                if isinstance(x, str):
                    if x == 'FLIP_H':
                        self.flips ^= 1
                    if x == 'FLIP_V':
                        self.flips ^= 2
                if isinstance(x, dict):
                    if 'sound' in x:
                        print(x)
                        # print(self.handler.app.sounds[x['sound'].upper()].get_raw()[:64])
                        # self.handler.app.sounds[x['sound'].upper()].play()
                    if 'offset' in x:
                        self.x += x['offset'].x
                        self.y += x['offset'].y
                if isinstance(x, int):
                    self.image_ind = list(self.handler.app.frames.keys()).index(x)
        self.flip()
        self.rect.center = self.x, self.y
        if not self.seq_data[self.seq_level]:
            if self.seq_level >= 1:
                self.seq_level -= 1
                self.seq_data.pop()
            else:
                # self.seq_name = 'idle'
                # self.seq_data[0] = get_sequence(
                #     self.seq_name, self.handler.app)
                pass


class SpriteHandler:
    def __init__(self, app):
        self.app = app
        self.images = [pil_image_to_surface(app.frames[i])
                       for i in app.frames]
        self.group = pg.sprite.Group()
        self.sprites = [SpriteUnit(self, WIDTH // 2, HEIGHT // 2)]

    def update(self):
        self.group.update()

    def draw(self):
        self.group.draw(self.app.screen)


class App:
    def __init__(self):
        pg.mixer.init(frequency=4000, size=-16, channels=1)
        pg.init()
        self.sequences = {}
        self.frames = {}
        self.sounds = {}
        self.screen = pg.display.set_mode(WIN_SIZE)
        pg.display.set_caption('DeskMates sprite test')
        self.clock = pg.time.Clock()
        self.font = ft.SysFont('Courier New', FONT_SIZE)
        self.dt = 0.0
        FASData('TEST_FILE.FAS', self)
        # WASData(workDir + curChar + '\\Data\\Deskmate.WAS', self)
        sort_dict(self.frames)
        self.frame_num = list(self.frames.keys()).index(frame_id)
        self.sprite_handler = SpriteHandler(self)
        self.sprite_handler.sprites[0].seq_name = 'do'
        self.sprite_handler.sprites[0].seq_data = [get_sequence(self.sprite_handler.sprites[0].seq_name, self)]

    def update(self):
        pg.display.flip()
        self.sprite_handler.update()
        self.dt = self.clock.tick(10)

    def draw(self):
        self.screen.fill('gray64')
        self.sprite_handler.draw()
        self.draw_fps()

    def draw_fps(self):
        fps_text = f'{self.clock.get_fps() :.0f} FPS'
        seq_text = f'Current sequence: {self.sprite_handler.sprites[0].seq_name}'
        frame_text = f'Current frame: {list(app.frames.keys())[self.sprite_handler.sprites[0].image_ind]:04d}'
        self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 4), text=fps_text, fgcolor='black')
        self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 3), text=seq_text, fgcolor='black')
        self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 2),
                            text='Sequence level: '+str(self.sprite_handler.sprites[0].seq_level), fgcolor='black')
        self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE), text=frame_text, fgcolor='black')
        self.font.render_to(self.screen, (8, HEIGHT - 16), text='Controls: ← - prev. frame; → - next frame; home - '
                                                                'first frame; end - last frame', fgcolor='black')

    @staticmethod
    def check_events():
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
    # left=min(pnt1[0],(pnt2.[0]-frame_width))
    # top=min(-pnt1[1],(-pnt2.[1]-frame_width))
    frame_id = 3
    curChar = 'Kahli'
    workDir = 'E:\\DeskMates\\'
    # fileName = 'CARD.FAS'
    app = App()
    app.run()
