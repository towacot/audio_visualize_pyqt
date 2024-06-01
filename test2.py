import librosa
import numpy as np
import matplotlib.pyplot as plt

def plot_spectrogram(specs):
    plt.figure(figsize=(10, 4))
    plt.imshow(specs, aspect='auto', origin='lower', cmap='inferno')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')
    plt.xlabel('Time')
    plt.ylabel('Frequency')
    plt.show()

# wavファイルを読み込み
file_path = "test.wav"
y, sr = librosa.load(file_path, sr=None)
params = {
    "chunk": 1024,
    "step": 512,
    "sample_rate": sr
}
totals_specs = np.empty((0, params["chunk"] // 2 + 1))

window = np.hamming(params["chunk"])
for i in range(0, len(y) - params["chunk"], params["step"]):
    process_data = y[i:i + params["chunk"]] * window
    specs = np.abs(np.fft.rfft(process_data)) ** 2
    specs = librosa.amplitude_to_db(specs, ref=np.max)
    totals_specs = np.vstack((totals_specs, specs))

plot_spectrogram(totals_specs.T)
