from src.audio_input import AudioInput
from src.spectrogram import Spectrogram
from src.gui import MainWindow
import queue
from collections import deque
import threading
# パラメタ設定
params = {
    "chunk": 2048,
    "step": 1200,
    "sample_rate": 44100,
}

Playstate=queue.Queue(maxsize=1)#空なら停止、満杯なら再生
InputDataQueue = deque()
SpectrogramQueue = deque()
# PyAudioストリーム入力取得クラス
input = AudioInput(chunk=1024,InputDataQueue=InputDataQueue)
# スペクトログラム用クラス
spectrogram = Spectrogram(params,Playstate,SpectrogramQueue,InputDataQueue)
# GUI用クラス
Main = MainWindow(params,Playstate,SpectrogramQueue)

# 別スレッドで入力取得開始

InputThread = threading.Thread(target=input.run, args=(Main.indicater,))
CalcThread = threading.Thread(target=spectrogram.run, args=())
InputThread.daemon=True
CalcThread.daemon=True
InputThread.start()
CalcThread.start()

#GUI実行開始
Main.run()