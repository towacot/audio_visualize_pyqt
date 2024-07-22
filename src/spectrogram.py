import sys
import time
import numpy as np
import librosa
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

class Spectrogram:
    def __init__(self,
                params,Playstate,SpectrogramQueue,InputDataQueue,paramsqueue
            ):
        # スペクトログラム算出用パラメタ
        self.n_chunk   = params["chunk"]
        self.step_width = params["step"]
        self.paramsqueue=paramsqueue
        ##一つのスペクトルに対して、描画時間幅は中心時刻から前後に
        ##step_width/2
        self.n_freqs   = self.n_chunk // 2 + 1
        
        self.sample_rate = params["sample_rate"]
        self.dt=1.0/self.sample_rate
        #状態管理
        self.data_is_not_enough = False
        self.temp_is_full = False
        self.playstate=Playstate

        self.reading_condition=threading.Condition()
        self.readable = True
        #処理データ
        self.process_data = np.zeros(self.n_chunk)
        self.index_of_initial = 0
        #保存データ
        self.spectrogramqueue = SpectrogramQueue
        self.inputdataqueue = InputDataQueue
        self.temp_data = np.array([],dtype=np.float32)
        
        self.total_data = np.array([],dtype=np.float32)
        
        self.specs     = np.zeros((self.n_freqs))

        self.window    = np.hamming(self.n_chunk)
        self.fft       = np.fft.rfft
        self.maxvolume = 1.0
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def set_readable_true(self):
        #データが読める状態にする
        with self.reading_condition:
            self.readable=True
            self.reading_condition.notify_all()

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
    def calc_spectrogram(self, data):
        windowed_data = data * self.window
        specs = np.abs(np.fft.rfft(windowed_data))**2
        return specs
    def calc(self):
        self.callback()
        #得られたtotal_dataから指定された範囲のデータを取得
        self.get_process_data()
        start=time.time()
        #データが不足している場合は何もしない
        if self.data_is_not_enough:
            return
        else:
            # # self.specs[:]=np.sqrt(np.abs(self.fft(self.window * self.process_data)))
            # self.process_data = self.process_data * self.window
            # specs = np.abs(np.fft.rfft(self.process_data))**2
            # if np.max(specs) > self.maxvolume:
            #     self.maxvolume = np.max(specs)
            # specs = librosa.power_to_db(specs, ref=self.maxvolume)
            # #print(specs)
            # self.spectrogramqueue.append(specs)
            # #スペクトログラムをGUIに渡す
        
            # 並列でスペクトログラムを計算 GPT 効果不明
            future = self.executor.submit(self.calc_spectrogram, self.process_data)
            specs = future.result()  # 計算結果を取得
            if np.max(specs) > self.maxvolume:
                self.maxvolume = np.max(specs)
            
            specs = librosa.power_to_db(specs, ref=100000)
            self.spectrogramqueue.append(specs)
        finish=time.time()
        sys.stdout.write("\rcalc time : {}".format(finish-start ))
        sys.stdout.flush()
    def resetparams(self):
        new_params = self.paramsqueue.get()
        self.n_chunk   = new_params["chunk"]
        self.step_width = new_params["step"]
        self.n_freqs   = self.n_chunk // 2 + 1
        self.specs     = np.zeros((self.n_freqs))
        self.window    = np.hamming(self.n_chunk)
        self.total_data = np.array([],dtype=np.float32)
        self.index_of_initial = 0
        

    def run(self):
        activated=0
        while True:
            if not self.playstate.empty():
                if activated==0:
                    activated=1
                    self.resetparams()
                #print("calc run")
                #print(self.testo)
                self.calc()
            else:
                time.sleep(0.01)
                activated=0

    def callback(self):
        #データを追加
        if len(self.inputdataqueue) == 0:
            return
        buffer = self.inputdataqueue.popleft()
        self.total_data = np.append(self.total_data, buffer)
