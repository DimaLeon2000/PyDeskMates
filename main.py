from audio_data import WASData
from animation_data import FASData
from bit_reader import *
import pyaudio
import struct
import tkinter
import wave
import os
import zlib


WIN_SIZE = WIDTH, HEIGHT = 320, 240
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'


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
            print('You quitter...')
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


def draw_frame(__frame_num):
    if test_fas.frames_header['count'] >= 1:
        # print(__frame_num)
        image_frame.blank()
        palette_num = test_fas.frames_header['pal'][__frame_num]
        pal_color = test_fas.dib_headers[palette_num * 2]
        pal_mask = test_fas.dib_headers[1 + palette_num * 2]
        bpp = pal_color['bpp']
        stride = (bpp * test_fas.header['width']+31)//32*(32//bpp)
        i, j = 0, 0
        # stride formula: (bpp * test_fas.header['width']+31)//32*(32//bpp)
        # [print(read_bits_per_pixel(i[0],bpp), end='') for i in test_fas.reader.frames_bitmap[frame_num]]
        # print(len(list(test_fas.frames_bitmap[__frame_num])))
        for x in test_fas.frames_bitmap[__frame_num]:
            col = read_bits_per_pixel(x, bpp)
            for y in range(len(col)):
                image_frame.put('#%02x%02x%02x' % read_rgb(pal_color['colormap'][col[y]],
                                                           # + pal_mask['colormap'][col[y]]
                                                           False),
                                (j, test_fas.header['height'] - 1 - i))
                # image_frame.put('#%02x%02x%02x' % read_rgb(pal_mask['colormap'][col[y]], False),
                #                 (j + test_fas.header['width'], test_fas.header['height'] - 1 - i))
                j += 1
                if j >= stride:
                    i += 1
                    j -= stride
        frame_canvas.create_image(0, 0, image=image_frame, anchor=tkinter.NW)
        root.title('Frame #'+f"{test_fas.frames_header['id'][frame_num]:04d}")


def terminate(event):
    # print(event)
    global frame_num
    if event.keycode == 39:
        if frame_num < test_fas.frames_header['count']-1:
            frame_num += 1
            draw_frame(frame_num)
    elif event.keycode == 37:
        if frame_num > 0:
            frame_num -= 1
            draw_frame(frame_num)
    if event.keycode == 81:
        root.destroy()


def mouse_click(event):
    print(event)
    print(touch_map.get(event.x, event.y))


if __name__ == '__main__':
    # Regex: ,\s*(?![^()]*\))(?![^\[\]]*\])
    # left=min(pnt1[0],(pnt2.[0]-frame_width))
    # top=min(-pnt1[1],(-pnt2.[1]-frame_width))
    test_fas = debug_fas_tool(r'TEST_FILE.FAS')
    root = tkinter.Tk()
    if hasattr(test_fas, 'touch'):  # get hotspots
        touch_map = tkinter.PhotoImage(width=test_fas.header['width'], height=test_fas.header['height'])
        colors = len(test_fas.touch['colors'])
        if colors in range(1, 3):
            bpp = 1
        elif colors <= 4:
            bpp = 2
        elif colors <= 16:
            bpp = 4
        elif colors <= 256:
            bpp = 8
        else:
            bpp = 0
        # put pixels into hotspots map
        for i in range(test_fas.header['height']):
            for j in range(test_fas.header['width']):
                palette_num = read_bits_per_pixel(test_fas.touch['bitmap'][j // (8 // bpp)
                                                  + i * test_fas.touch['width']], bpp)[j % (8 // bpp)]
                touch_map.put('#%02x%02x%02x' % read_rgb(test_fas.touch['colors'][palette_num], False),
                              (j, test_fas.header['height'] - i - 1))
        touch_canvas = tkinter.Canvas(root,
                                      width=test_fas.header['width'],
                                      height=test_fas.header['height'],
                                      highlightthickness=0)
        touch_canvas.pack()
        touch_canvas.create_image(0, 0, image=touch_map, anchor=tkinter.NW)

    frame_canvas = tkinter.Canvas(root,
                                  width=test_fas.header['width'],
                                  height=test_fas.header['height'],
                                  highlightthickness=0)
    frame_canvas.pack()
    image_frame = tkinter.PhotoImage(width=test_fas.header['width'], height=test_fas.header['height'])
    # frame_num = test_fas.frames_header['count'] - 1
    frame_id = 4000
    frame_num = test_fas.frames_header['id'].index(frame_id)
    root.title('Rendering...')
    draw_frame(frame_num)
    # print(test_fas.frames_bitmap[frame_num])
    root.bind_all('<Key>', terminate)
    root.bind_all('<Button>', mouse_click)
    # root.configure(bg='black')
    root.mainloop()
    del test_fas
