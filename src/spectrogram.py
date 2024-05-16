import sys
import time
import numpy as np
import librosa
import threading


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
        #状態管理
        self.data_is_not_enough = False
        self.temp_is_full = False

        self.reading_condition=threading.Condition()
        self.readable = False
        #処理データ
        self.process_data = np.zeros(self.n_chunk)
        self.index_of_initial = 0
        
        #保存データ
        self.temp_data = np.array([])
        
        self.total_data = np.array([])

        self.specs     = np.zeros((self.n_freqs))

        self.window    = np.hamming(self.n_chunk)
        self.fft       = np.fft.rfft
    def set_readable_true(self):
        #データが読める状態にする
        with self.reading_condition:
            self.readable=True
            self.reading_condition.notify()

    def set_now_reading(self):
        #データ読んでるから今は読めないよ！
        with self.reading_condition:
            self.readable=False

    def wait_for_readable(self):   
        #データが読めるまで待機
        with self.reading_condition:
            while not self.readable:
                self.reading_condition.wait()

    def get_process_data(self):
        #データが読めるまで待機
        self.wait_for_readable()
        #データを読むよ！
        self.set_now_reading()
        #--------------------------------
        # initialからn_chunk分のデータを取得するためにデータの長さを確認
        if self.index_of_initial + self.n_chunk > len(self.total_data):
            # データが不足している場合
            self.data_is_not_enough = True
        else:
            #initialからn_chunk分のデータを取得
            self.process_data = self.total_data[self.index_of_initial:self.index_of_initial + self.n_chunk]
            #次の処理データの開始位置を更新
            self.index_of_initial += self.step_width
            #データ不足状態を解除
            self.data_is_not_enough = False
        #--------------------------------
        self.set_readable_true()#データ読み終わったよ！

    def calc(self,get_new_sp):
        #得られたtotal_dataから指定された範囲のデータを取得
        self.get_process_data()
        #データが不足している場合は何もしない
        if self.data_is_not_enough:
            return
        else:
            #窓関数をかける
            self.process_data[:]=self.process_data[:]*self.window
            #FFTをかける
            self.specs[:] = (self.fft(self.process_data))**2
            #スペクトログラムをGUIに渡す
            get_new_sp(self.specs)

    def callback(self, buffer):
        #データを追加
        with self.reading_condition:
            if self.readable==False:
                #一時的にデータを保管して、reading=Falseになったらtotal_dataに追加
                self.temp_data = np.append(self.temp_data, buffer)
                self.temp_is_full = True

            else:
                #total_dataにデータを追加
                self.set_now_reading()#データ読んでるから今は読めないよ！
                #---------------------------
                if self.temp_is_full:
                    #一時的に保管していたデータをtotal_dataに追加
                    self.total_data = np.append(self.total_data, self.temp_data)
                    #一時的なデータを削除
                    self.temp_data = np.array([])
                    self.temp_is_full = False
                #新しいデータを追加
                self.total_data = np.append(self.total_data, buffer)
                #---------------------------
                self.set_readable_true()#データ読み終わったよ！