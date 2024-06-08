from src_copy.audio_input import AudioInputStream
from src_copy.gui import PQGMelSpectrogram


# PyAudioストリーム入力取得クラス
ais = AudioInputStream() #, input_device_keyword="Real")
# メルスペクトログラム用クラス
melspectrogram = PQGMelSpectrogram( ais.RATE, (ais.CHANNELS, ais.CHUNK) )

# AudioInputStreamは別スレッドで動かす
import threading
thread = threading.Thread(target=ais.run, args=(melspectrogram.callback_sigproc,))
thread.daemon=True
thread.start()

# スペクトログラム描画開始
melspectrogram.run_app()