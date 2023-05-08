from audio_reader import WASReader
import pygame as pg


class WASData:
    def __init__(self, was_path, app, mp3):
        self.app = app
        self.reader = WASReader(was_path)
        self.sounds = []
        for i in range(self.reader.header['snd_count']):
            sound = self.get_sound(i)
            # self.sounds.append([sound['name'],sound['data']])
            self.sounds.append(sound)
            # print(sound)
        for i in self.sounds:
            name = i['name'].upper()
            self.app.sounds[i['name']] = pg.mixer.Sound(buffer=bytes(i['data']))
        # self.sounds = dict(self.sounds)
        # print(self.sounds)
        self.reader.close()

    def get_sound(self, index):
        sound_pointers = self.reader.directory[index]
        name_offset = sound_pointers['name_offset'] + self.reader.header['snd_count'] * 8 + 8
        data_offset = sound_pointers['data_offset'] + self.reader.header['snd_count'] * 8 + 8
        data_length = self.reader.read_4_bytes(data_offset)
        # wave_data = []
        # for i in range(data_length):
        #     wave_data.append(self.reader.read_1_byte(offset=data_offset + 4 + i))
        sound_info = {
            'name': self.reader.read_string_null_terminated(offset=name_offset),
            'data': self.reader.read_bytes_raw(offset=data_offset, num_bytes=data_length)
        }
        return sound_info
