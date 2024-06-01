from src.audio_input import AudioInput
from src.spectrogram import Spectrogram
from src.gui import MainWindow
import queue
# パラメタ設定
params = {
    "chunk": 2048,
    "step": 1024,
    "sample_rate": 44100,
}
Playstate=queue.Queue()#空なら停止、満杯なら再生
SpectrogramQueue = queue.Queue()
# PyAudioストリーム入力取得クラス
input = AudioInput(chunk=1024)
# スペクトログラム用クラス
spectrogram = Spectrogram(params)
# GUI用クラス
Main = MainWindow(params,Playstate,SpectrogramQueue)

# 別スレッドで入力取得開始
import threading
InputThread = threading.Thread(target=input.run, args=(spectrogram.callback,Main.indicater,))
CalcThread = threading.Thread(target=spectrogram.run, args=(Playstate,SpectrogramQueue,))
InputThread.daemon=True
CalcThread.daemon=True
InputThread.start()
CalcThread.start()

#GUI実行開始
Main.run()