from animation_reader import FASReader
import re
from ast import literal_eval


class FASData:
    def __init__(self, fas_path):
        self.reader = FASReader(fas_path)
        # if self.reader != 0:
        #     print('File read!')
        self.header = self.reader.header
        self.dib_headers = self.reader.dib_headers
        if hasattr(self.reader, 'touch'):
            self.touch = self.reader.touch
        self.sequences = {}
        for i in range(self.reader.seq_header['seq_count']):
            sequence = self.reader.read_sequence(i)
            self.sequences[sequence['name']] = sequence['sequence']
            # print(sequence['name'] + ':', self.sequences[sequence['name']])
            print(sequence['name'])
            print(sequence['sequence'])
            # print(sequence['name']+' (parsed): ', self.parse_sequence(seq=sequence['name']))
        self.frames_header = self.reader.frames_header
        self.frames_bitmap = self.reader.frames_bitmap

    def parse_sequence_part(self, __part):
        # print(__part.isnumeric())
        return __part

    def parse_sequence(self, seq):  # INCOMPLETE
        parts = re.split(r',(?![^()]*\))(?![^\[\]]*])(?![^{}]]*})(?![^\xA9]*\xA9)', self.sequences[seq])
        for x in parts:
            self.parse_sequence_part(x)
            # if re.match(r'\[([0-9\,\-]+)\]', x): #check if
            #     pos_offset = literal_eval(re.match(r'\[([0-9\,\-]+)\]', x).group(1))
            #     print(pos_offset)
            # print(x)
            pass
        return parts

    def __del__(self):
        self.header = {}
        self.dib_headers = {}
        self.touch = {}
        self.reader.close()
