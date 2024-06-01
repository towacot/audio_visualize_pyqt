import time

import numpy as np
import pyaudio as pa
import sys

class AudioInput:
    def __init__(self,format=pa.paFloat32, 
                 chunk=512, 
                 sample_rate=44100, 
                 channels=1, 
                 use_device_index=7):
        
        self.chunk = chunk
        self.format = format
        self.sample_rate = sample_rate
        self.channels = channels
        self.use_device_index = use_device_index
        self.p_in = pa.PyAudio()
        if format is pa.paFloat32:
            self.dtype = np.float32
        elif format is pa.paInt16:
            self.dtype = np.int16
        self.open_stream()

    def open_stream(self):
        self.stream = self.p_in.open(format=self.format,
                                     channels=self.channels,
                                     rate=self.sample_rate,
                                     input=True,
                                     output=False,
                                     frames_per_buffer=self.chunk,
                                     input_device_index=self.use_device_index)
        return self

    def run(self,callback,indicater):
        while self.stream.is_active():
            input_buff = self.stream.read(self.chunk)
            data = np.frombuffer(input_buff, dtype=self.dtype)
            # print("input")
            # print(data)
            callback(data)
            #indicater(data)
        self.__terminate()
        
    def __terminate(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p_in.terminate()