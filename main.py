from audio_data import WASData
from animation_data import FASData
# from bit_reader import *
# import io
# import PIL
import pyaudio
import pygame as pg
from settings import *
import struct
import sys
# import tkinter
import wave
import os
import zlib


LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'


def pilImageToSurface(pilImage):
    return pg.image.frombytes(
        pilImage.tobytes(), pilImage.size, pilImage.mode).convert_alpha()

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


def debug_fas_tool(anim_path):
    return FASData(anim_path)


def fas_deflate(anim_path):
    anim_name = os.path.splitext(os.path.basename(anim_path))[0]
    anim_file = open(anim_path, 'rb')
    anim_data = anim_file.read()
    anim_file.close()
    faz_file = 0
    packed_data = zlib.compress(anim_data)
    try:
        faz_file = open(anim_name + '.FAZ', 'wb+')
        faz_file.write(struct.pack('i', len(anim_data)))
        faz_file.write(packed_data)
    finally:
        faz_file.close()


def faz_inflate(packed_path):
    anim_name = os.path.splitext(os.path.basename(packed_path))[0]
    packed_file = open(packed_path, 'rb')
    packed_file.seek(4)
    packed_data = packed_file.read()
    packed_file.close()
    anim_data = zlib.decompress(packed_data)
    anim_file = 0
    # if not (os.path.exists(anim_name + '.FAS')):
    try:
        anim_file = open(anim_name + '.FAS', 'wb+')
        anim_file.write(anim_data)
    finally:
        anim_file.close()


class SpriteUnit(pg.sprite.Sprite):
    def __init__(self, handler, x, y):
        self.handler = handler
        self.x, self.y = x, y
        super().__init__(handler.group)
        self.image_ind = frame_num
        self.image = self.handler.images[frame_num]
        self.rect = self.image.get_rect()

    def update(self):
        self.rect.center = self.x, self.y
        self.image = self.handler.images[self.image_ind]


class SpriteHandler:
    def __init__(self, app):
        self.app = app
        self.images = [pilImageToSurface(test_fas.get_frame_masked(i)) for i in range(test_fas.frames_header['count'])]
        # self.mask = pg.image.load(io.BytesIO(get_frame_bitmap(frame_num, True)))
        self.group = pg.sprite.Group()
        self.sprites = [SpriteUnit(self, WIDTH // 2, HEIGHT // 2)]

    def update(self):
        self.group.update()

    def draw(self):
        self.group.draw(self.app.screen)


class App:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WIN_SIZE)
        self.clock = pg.time.Clock()
        self.font = pg.freetype.SysFont('Courier New', FONT_SIZE)
        self.dt = 0.0
        self.sprite_handler = SpriteHandler(self)
        self.sprite_handler.sprites[0].sequence = 'ab'

    def update(self):
        pg.display.flip()
        self.sprite_handler.update()
        # self.dt = self.clock.tick() * 0.001
        self.dt = self.clock.tick(10)

    def draw(self):
        self.screen.fill('gray64')
        self.sprite_handler.draw()
        self.draw_fps()

    def draw_fps(self):
        fps_text = f'{self.clock.get_fps() :.0f} FPS'
        seq_text = f'Current sequence: {self.sprite_handler.sprites[0].sequence}'
        frame_text = f'Current frame: {test_fas.frames_header["id"][self.sprite_handler.sprites[0].image_ind]:04d}'
        self.font.render_to(self.screen, (8, 8), text=fps_text, fgcolor='black')
        self.font.render_to(self.screen, (8, 8+FONT_SIZE), text=seq_text, fgcolor='black')
        self.font.render_to(self.screen, (8, 8+FONT_SIZE*2), text=frame_text, fgcolor='black')

    def check_events(self):
        for e in pg.event.get():
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_RIGHT:
                    if self.sprite_handler.sprites[0].image_ind < test_fas.frames_header['count'] - 1:
                        self.sprite_handler.sprites[0].image_ind += 1
                elif e.key == pg.K_LEFT:
                    if self.sprite_handler.sprites[0].image_ind > 0:
                        self.sprite_handler.sprites[0].image_ind -= 1
                elif e.key == pg.K_HOME:
                    self.sprite_handler.sprites[0].image_ind = 0
                elif e.key == pg.K_END:
                    self.sprite_handler.sprites[0].image_ind = test_fas.frames_header['count'] - 1
            if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    # Regex: ,\s*(?![^()]*\))(?![^\[\]]*\])
    # left=min(pnt1[0],(pnt2.[0]-frame_width))
    # top=min(-pnt1[1],(-pnt2.[1]-frame_width))
    test_fas = FASData(r'TEST_FILE.FAS')
    # frame_num = test_fas.frames_header['count'] - 1
    # frame_id = 4000;
    # frame_num = test_fas.frames_header['id'].index(frame_id)
    frame_num = 0
    app = App()
    app.run()
    # root = tkinter.Tk()

    # if hasattr(test_fas, 'touch'):  # get hotspots
    #     touch_map = tkinter.PhotoImage(width=test_fas.header['width'], height=test_fas.header['height'])
    #     colors = len(test_fas.touch['colors'])
    #     if colors in range(1, 3):
    #         bpp = 1
    #     elif colors <= 4:
    #         bpp = 2
    #     elif colors <= 16:
    #         bpp = 4
    #     elif colors <= 256:
    #         bpp = 8
    #     else:
    #         bpp = 0
    #     # put pixels into hotspots map
    #     for i in range(test_fas.header['height']):
    #         for j in range(test_fas.header['width']):
    #             palette_num = read_bits_per_pixel(test_fas.touch['bitmap'][j // (8 // bpp)
    #                                               + i * test_fas.touch['width']], bpp)[j % (8 // bpp)]
    #             touch_map.put('#%02x%02x%02x' % read_rgb(test_fas.touch['colors'][palette_num], False),
    #                           (j, test_fas.header['height'] - i - 1))
    #     touch_canvas = tkinter.Canvas(root,
    #                                   width=test_fas.header['width'],
    #                                   height=test_fas.header['height'],
    #                                   highlightthickness=0)
    #     touch_canvas.pack()
    #     touch_canvas.create_image(0, 0, image=touch_map, anchor=tkinter.NW)
