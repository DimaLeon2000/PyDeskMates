from audio_reader import WASReader
import audioop
import pygame as pg
from io import BytesIO


def read_wav_data(data):
    buf = b''
    for i in range(len(data) >> 1):
        bytes_slice = data[i << 1:(i+1) << 1]
        buf += bytes_slice * 2
    return buf


class WASData:
    def __init__(self, was_path, app, mp3):
        self.app = app
        self.reader = WASReader(was_path)
        self.sounds = {}
        for i, sound_info in enumerate(self.reader.directory):
            sound = self.get_sound(i)
            if mp3:
                self.sounds[sound['name'].upper()] = pg.mixer.Sound(file=BytesIO(sound['data']))
            else:
                self.sounds[sound['name'].upper()] = pg.mixer.Sound(buffer=audioop.ratecv(sound['data'], 2, 1, 8000,
                                                                                  app.sample_rate*2, None)[0])
            # self.sounds[sound['name']] = sound['data']
        # for i in self.sounds:
        #     name = i.upper()
        #     if mp3:
        #         self.app.sounds[name] = pg.mixer.Sound(file=BytesIO(self.sounds[i]))
        #     else:
        #         # self.app.sounds[name] = pg.mixer.Sound(buffer=read_wav_data(self.sounds[i]))
        #         self.app.sounds[name] = pg.mixer.Sound(buffer=audioop.ratecv(self.sounds[i], 2, 1, 8000,
        #                                                                      app.sample_rate*2, None)[0])
        self.reader.close()

    def get_sound(self, index):
        sound_pointers = self.reader.directory[index]
        name_offset = sound_pointers['name_offset'] + self.reader.header['snd_count'] * 8 + 8
        data_offset = sound_pointers['data_offset'] + self.reader.header['snd_count'] * 8 + 8
        data_length = self.reader.read_4_bytes(data_offset)
        sound_info = {
            'name': self.reader.read_string_null_terminated(offset=name_offset),
            'data': self.reader.read_bytes_raw(offset=data_offset + 4, num_bytes=data_length)
        }
        return sound_info
