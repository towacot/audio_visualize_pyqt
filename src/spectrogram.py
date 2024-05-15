import sys
import time
import numpy as np
import librosa



class Spectrogram:
    def __init__(self,
                chunk,
                step,
                sample_rate,
            ):
        # スペクトログラム算出用パラメタ
        self.n_chunk   = chunk
        self.step_width = step
        ##一つのスペクトルに対して、描画時間幅は中心時刻から前後に
        ##step_width/2
        self.n_freqs   = self.n_chunk // 2 + 1
        
        self.sample_rate = sample_rate
        self.dt=1.0/self.sample_rate
        self.data = np.zeros(self.n_chunk)
        self.specs     = np.zeros((self.n_freqs))

        self.window    = np.hamming(self.n_chunk)
        self.fft       = np.fft.rfft

        
        
    def calc(self,get_new_sp):
        self.data[:]=self.data[:]*self.window
        self.specs[:] = (self.fft(self.data))**2
        get_new_sp(self.specs)

    def callback(self, data):
        self.data[:]=data