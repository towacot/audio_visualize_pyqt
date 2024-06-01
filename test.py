import sys
import time
import numpy as np
import librosa
import matplotlib.pyplot as plt
import threading

class Spectrogram:
    def __init__(self, params):
        # スペクトログラム算出用パラメタ
        self.n_chunk = params["chunk"]
        self.step_width = params["step"]
        self.n_freqs = self.n_chunk // 2 + 1
        self.sample_rate = params["sample_rate"]
        self.dt = 1.0 / self.sample_rate
        # 状態管理
        self.data_is_not_enough = False
        self.temp_is_full = False

        self.reading_condition = threading.Condition()
        self.readable = True
        # 処理データ
        self.process_data = np.zeros(self.n_chunk)
        self.index_of_initial = 0
        self.testo = 0
        # 保存データ
        self.temp_data = np.array([])
        self.total_data = np.array([])

        self.specs = np.zeros((self.n_freqs))

        self.window = np.hamming(self.n_chunk)
        self.fft = np.fft.rfft

    def reload_params(self, params):
        self.n_chunk = params["chunk"]
        self.step_width = params["step"]
        self.n_freqs = self.n_chunk // 2 + 1
        self.sample_rate = params["sample_rate"]
        self.dt = 1.0 / self.sample_rate

    def set_readable_true(self):
        # データが読める状態にする
        with self.reading_condition:
            self.readable = True
            self.reading_condition.notify()

    def set_now_reading(self):
        # データ読んでるから今は読めないよ！
        with self.reading_condition:
            self.readable = False

    def wait_for_readable(self):
        # データが読めるまで待機
        with self.reading_condition:
            while not self.readable:
                self.reading_condition.wait()

    def get_process_data(self):
        # データが読めるまで待機
        self.wait_for_readable()
        # データを読むよ！
        self.set_now_reading()
        # initialからn_chunk分のデータを取得するためにデータの長さを確認
        if self.index_of_initial + self.n_chunk > len(self.total_data):
            # データが不足している場合
            self.data_is_not_enough = True
        else:
            # initialからn_chunk分のデータを取得
            self.process_data = self.total_data[self.index_of_initial:self.index_of_initial + self.n_chunk]
            # 次の処理データの開始位置を更新
            self.index_of_initial += self.step_width
            print(self.index_of_initial)
            # データ不足状態を解除
            self.data_is_not_enough = False
        # データ読み終わったよ！
        self.set_readable_true()

    def calc(self, get_new_sp):
        # 得られたtotal_dataから指定された範囲のデータを取得
        self.get_process_data()
        # データが不足している場合は何もしない
        if self.data_is_not_enough:
            return
        else:
            self.process_data = self.process_data * self.window
            self.specs[:] = np.abs(self.fft(self.process_data) ** 2)
            self.specs = librosa.amplitude_to_db(self.specs, ref=np.max)
            get_new_sp(self.specs)

    def run(self, get_new_sp, playstate):
        while True:
            if 1:
                self.calc(get_new_sp)
            else:
                time.sleep(0.01)

    def callback(self, buffer):
        # データを追加
        buffer = np.array(buffer, dtype=np.int16)

        with self.reading_condition:
            if not self.readable:
                # 一時的にデータを保管して、reading=Falseになったらtotal_dataに追加
                self.temp_data = np.append(self.temp_data, buffer)
                self.temp_is_full = True
                self.testo = 2
            else:
                # total_dataにデータを追加
                self.set_now_reading()
                if self.temp_is_full:
                    # 一時的に保管していたデータをtotal_dataに追加
                    self.total_data = np.append(self.total_data, self.temp_data)
                    # 一時的なデータを削除
                    self.temp_data = np.array([])
                    self.temp_is_full = False
                # 新しいデータを追加
                self.total_data = np.append(self.total_data, buffer)
                self.set_readable_true()

def plot_spectrogram(specs):
    plt.figure(figsize=(10, 4))
    plt.imshow(specs, aspect='auto', origin='lower', cmap='inferno')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')
    plt.xlabel('Time')
    plt.ylabel('Frequency')
    plt.show()

def load_wav_and_create_spectrogram(file_path):
    # wavファイルを読み込み
    y, sr = librosa.load(file_path, sr=None)
    params = {
        "chunk": 2048,
        "step": 512,
        "sample_rate": sr
    }
    spec = Spectrogram(params)
    spec.total_data = y
    spec.run(plot_spectrogram, threading.Event())

# テスト実行
if __name__ == "__main__":
    wav_file_path = 'test.wav'  # ここにwavファイルのパスを指定
    load_wav_and_create_spectrogram(wav_file_path)
