from audio_reader import WASReader


class WASData:
    def __init__(self, was_path):
        self.reader = WASReader(was_path)
        self.sounds = []
        for i in range(self.reader.header['snd_count']):
            sound = self.get_sound(i)
            # self.sounds.append([sound['name'],sound['data']])
            self.sounds.append(sound)
        # self.sounds = dict(self.sounds)
        # print(self.sounds)
        self.reader.close()

    def get_sound(self, index):
        sound_pointers = self.reader.directory[index]
        name_offset = sound_pointers['name_offset'] + self.reader.header['snd_count'] * 8 + 8
        data_offset = sound_pointers['data_offset'] + self.reader.header['snd_count'] * 8 + 8
        data_length = self.reader.read_4_bytes(data_offset)
        wave_data = []
        for i in range(data_length):
            wave_data.append(self.reader.read_1_byte(offset=data_offset + 4 + i))
        sound_info = {
            'name': self.reader.read_string(offset=name_offset, num_bytes=50),
            'data': wave_data
        }
        return sound_info
