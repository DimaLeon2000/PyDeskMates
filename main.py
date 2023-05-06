from audio_data import WASData
from animation_data import *
# from bit_reader import *
# from PIL import ImageGrab
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


def pil_image_to_surface(pil_image, alpha=False):
    return pg.image.frombytes(
        pil_image.tobytes(), pil_image.size, pil_image.mode).convert_alpha() if alpha else pg.image.frombytes(
        pil_image.tobytes(), pil_image.size, pil_image.mode).convert()


def list_length_recursive(my_list):
    if my_list and (isinstance(my_list, list) or isinstance(my_list, int)):
        return 1 + list_length_recursive(my_list[1:])
    return 0


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
    def __init__(self, handler, x, y, temp):
        self.handler = handler
        self.x, self.y = x, y
        super().__init__(handler.group)
        self.image_ind = 0
        self.image = self.handler.images[self.image_ind]
        self.rect = self.image.get_rect()
        self.rect.center = self.x, self.y
        self.fence_rect = pg.rect.Rect(0, 0, WIDTH, HEIGHT)
        self.flags = 0  # (1 - horizontal flip, 2 - vertical flip, 4 - masking)
        self.temporary = temp
        # print(self.rect)
        self.seq_name = ''
        self.seq_data = [[]]
        self.seq_data_sub = ''
        self.repeats = 0
        self.timer_frames = 0
        self.repeats_highest_level = 0

    def flip(self):
        self.image = pg.transform.flip(self.handler.images[self.image_ind], bool(self.flags & 1), bool(self.flags & 2))
        self.rect = self.image.get_rect()

    def update(self):
        x = ''
        while not(isinstance(x, int)):
            if (len(self.seq_data[-1])) > 0:
                x = self.seq_data[-1].pop(0)
                if isinstance(x, list):  # grouping
                    self.seq_data.append(x)
                elif isinstance(x, str):  # sprite modifications
                    self.seq_data.append(get_sequence(x, self.handler.app))
                elif isinstance(x, dict):
                    if 'toggle_flag' in x:  # sprite modification flags
                        self.flags ^= x['toggle_flag']
                    elif 'repeats' in x and 'seq' in x:
                        # self.seq_data_sub = x['seq']
                        # self.repeats = x['repeats']
                        self.repeats_highest_level = len(self.seq_data)
                        self.seq_data.append([x['seq']] * x['repeats'])
                    elif 'timer_frames' in x and 'seq' in x:  # WIP
                        self.seq_data_sub = x['seq']
                        self.timer_frames = x['timer_frames']
                        self.repeats_highest_level = len(self.seq_data)
                        self.seq_data.append([])
                    elif 'fence' in x:  # sprite fencing
                        self.fence_rect = x['fence']
                        self.x = min(max(self.x, self.fence_rect.left), (self.fence_rect.left + self.fence_rect.width
                                                                         - self.rect.width))
                        self.y = min(max(self.y, self.fence_rect.top), (self.fence_rect.top + self.fence_rect.height
                                                                        - self.rect.height))
                        # print(list(self.fence_rect))
                    elif 'sound' in x:  # playing sound (not functioning)
                        print(x)
                        # print(self.handler.app.sounds[x['sound'].upper()].get_raw()[:64])
                        # self.handler.app.sounds[x['sound'].upper()].play()
                    elif 'offset' in x:  # offsetting sprite
                        self.x += x['offset'].x
                        self.y += x['offset'].y
                elif isinstance(x, int):
                    self.image_ind = list(self.handler.app.frames.keys()).index(x)
            else:
                if len(self.seq_data) >= 2:
                    self.seq_data.pop()
                else:
                    if self.temporary:
                        self.handler.sprites.pop(self.handler.sprites.index(self))
                        self.kill()
                    else:
                        self.seq_name = 'idle'
                        self.seq_data[0] = get_sequence(self.seq_name, self.handler.app)
                        # pass
        # print(self.seq_data_sub)
        # if (len(self.seq_data) < self.repeats_highest_level) and (self.repeats > 0 or self.timer_frames > 0):
        #     temp_seq = self.seq_data_sub
        #     self.seq_data.append([temp_seq])
        #     if self.repeats > 0:
        #         self.repeats -= 1
        # if ((self.repeats > 0) and ((len(self.seq_data)) <= self.repeats_highest_level)):
        #     self.seq_data.append(self.seq_data_sub)
        #     print(self.seq_data_sub)
        #     self.repeats -= 1
        # print(self.repeats)
        if self.timer_frames > 0:
            self.timer_frames -= 1
        self.flip()
        self.rect.topleft = self.x, self.y


class SpriteHandler:
    def __init__(self, app):
        self.app = app
        self.images = [pil_image_to_surface(app.frames[i], True)
                       for i in app.frames]
        self.images_extra = []
        self.group = pg.sprite.Group()
        self.sprites = []

    def add_sprite(self, x, y, temp):
        self.sprites.append(SpriteUnit(handler=self, x=x, y=y, temp=temp))

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
        FASData(workDir + curChar + '\\Data\\common_demo.FAS', self)
        FASData(workDir + curChar + '\\Data\\common_enter_demo.FAS', self)
        FASData(workDir + curChar + '\\Data\\touch_demo.FAS', self)
        FASData(workDir + curChar + '\\Data\\common.FAS', self)
        FASData(workDir + curChar + '\\Data\\common_enter.FAS', self)
        FASData(workDir + curChar + '\\Data\\touch.FAS', self)
        # FASData('CARD.FAS', self)
        # WASData(workDir + curChar + '\\Data\\Deskmate.WAS', self)
        sort_dict(self.frames)
        self.frame_num = list(self.frames.keys()).index(frame_id)
        self.sprite_handler = SpriteHandler(self)
        self.sprite_handler.add_sprite(WIDTH // 2, HEIGHT // 2, False)
        # self.sprite_handler.sprites[0].seq_name = 'do'
        self.sprite_handler.sprites[0].seq_name = 'common_sword_training_long_flipped'
        self.sprite_handler.sprites[0].temporary = False
        self.sprite_handler.sprites[0].seq_data = [[self.sprite_handler.sprites[0].seq_name.upper()]]
        # print(get_sequence(self.sprite_handler.sprites[0].seq_name.upper(), self))
        # print(self.sprite_handler.sprites[0].seq_data)

    def update(self):
        pg.display.flip()
        # self.background = pil_image_to_surface(ImageGrab.grab())
        if hasattr(self, 'sprite_handler'):
            self.sprite_handler.update()
        self.dt = self.clock.tick(10)

    def draw(self):
        self.screen.fill('gray64')
        # self.screen.blit(self.background, (0,0))
        if hasattr(self, 'sprite_handler'):
            for i in self.sprite_handler.sprites:
                self.sprite_handler.draw()
                # pg.draw.rect(self.screen, color='pink', rect=i.rect)
                pg.draw.lines(self.screen, color='red2', closed=True,
                              points=[i.fence_rect.topleft, i.fence_rect.topright,
                                      i.fence_rect.bottomright, i.fence_rect.bottomleft], width=1)  # fencing region
                pg.draw.lines(self.screen, color='green', closed=True,
                              points=[i.rect.topleft, i.rect.topright, i.rect.bottomright, i.rect.bottomleft], width=1)
                self.font.render_to(self.screen, (i.rect.topleft[0] + 4, i.rect.topleft[1] + 3),
                                    text=f'{self.sprite_handler.sprites.index(i)}', fgcolor='black')
                self.font.render_to(self.screen, (i.rect.topleft[0] + 3, i.rect.topleft[1] + 4),
                                    text=f'{self.sprite_handler.sprites.index(i)}', fgcolor='black')
                self.font.render_to(self.screen, (i.rect.topleft[0] + 5, i.rect.topleft[1] + 4),
                                    text=f'{self.sprite_handler.sprites.index(i)}', fgcolor='black')
                self.font.render_to(self.screen, (i.rect.topleft[0] + 4, i.rect.topleft[1] + 5),
                                    text=f'{self.sprite_handler.sprites.index(i)}', fgcolor='black')
                self.font.render_to(self.screen, (i.rect.topleft[0] + 4, i.rect.topleft[1] + 4),
                                    text=f'{self.sprite_handler.sprites.index(i)}', fgcolor='white')
        # self.draw_fps()

    def draw_fps(self):
        fps_text = f'{self.clock.get_fps() :.0f} FPS'
        self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE), text=fps_text, fgcolor='black')
        if hasattr(self, 'sprite_handler'):
            seq_text = f'Current sequence: {self.sprite_handler.sprites[0].seq_name}'
            frame_text = f'Current frame: {list(app.frames.keys())[self.sprite_handler.sprites[0].image_ind]:04d}'
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 5),
                                text=f'Sprites: {len(self.sprite_handler.sprites)}', fgcolor='black')
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 4), text=seq_text, fgcolor='black')
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 3),
                                text='Sequence level: '+str(self.sprite_handler.sprites[0].seq_level), fgcolor='black')
            self.font.render_to(self.screen, (8, HEIGHT - 16 - FONT_SIZE * 2), text=frame_text, fgcolor='black')
        self.font.render_to(self.screen, (8, HEIGHT - 16), text='Controls: ← - prev. frame; → - next frame; home - '
                                                                'first frame; end - last frame', fgcolor='black')

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
    # left=min(pnt1[0],(pnt2.[0]-frame_width))
    # top=min(-pnt1[1],(-pnt2.[1]-frame_width))
    frame_id = 3
    curChar = 'Maeka'
    workDir = 'E:\\DeskMates\\'
    # fileName = 'T20.FAS'
    app = App()
    app.run()
