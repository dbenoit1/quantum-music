#remember to:
#first install brew install portaudio
# pip install pyaudio
#then
# pip install PyQt5
import pyaudio
import numpy as np
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QSlider, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

#Rate and chunk size migth need changing if your machine is lagging or buffer times out
RATE = 44100
CHUNK = 128
SHOTS = 64  # don't push this too much unless you have a big CPU
MIX_RATIO = 0.75  # Initial mix ratio
USE_PAIRS = False  # Initial state: single noise simulation

p = pyaudio.PyAudio()

def simulate_quantum_noise(data, shots):
    """Simulates quantum noise on the audio data."""
    probs = np.cos(2 * data * np.pi)**2
    z_vals = np.array([np.random.choice([1, -1], p=[prob, 1 - prob], size=shots) for prob in probs]).T
    z_expectations = np.mean(z_vals, axis=0)
    return z_expectations

def simulate_quantum_noise_pairs(data, shots):
    """Generates noise with computed probabilities, optimized for speed """
    if len(data) % 2 != 0:
        raise ValueError("Data length must be even to process in pairs.")

    num_pairs = len(data) // 2
    data_pairs = data.reshape((num_pairs, 2))

    x, y = data_pairs[:, 0], data_pairs[:, 1]
    c1 = np.cos(x * 2 * np.pi)
    s1 = np.sin(x * 2 * np.pi)
    c2 = np.cos(y * 2 * np.pi)
    s2 = np.sin(y * 2 * np.pi)

    prob_minus_minus = (c1 * c2)**2
    prob_minus_plus = (c1 * s2)**2
    prob_plus_minus = (s1 * s2)**2
    prob_plus_plus = (s1 * c2)**2

    probs_pairs_all = np.stack([prob_minus_minus, prob_minus_plus, prob_plus_minus, prob_plus_plus], axis=1)

    pair_choices = np.array([np.random.choice(4, size=shots, p=probs) for probs in probs_pairs_all])

    pair_lookup = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]])

    z_vals = np.concatenate(pair_lookup[pair_choices], axis=1)

    z_expectations = np.mean(z_vals, axis=0)

    return z_expectations.flatten()

def audio_callback(in_data, frame_count, time_info, status):
    """Callback function for audio processing."""
    try:
        data = np.frombuffer(in_data, dtype=np.float32)
        mymax = np.max(np.abs(data))
        if mymax != 0:
            if USE_PAIRS:
                if len(data) % 2 != 0:
                    data = data[:-1] #ensure even length
                newdata = simulate_quantum_noise_pairs(data / mymax, SHOTS)
            else:
                newdata = simulate_quantum_noise(data / mymax, SHOTS)
        else:
            newdata = np.zeros(len(data))

        newdata = mymax * np.clip(newdata, -1.0, 1.0)

        mixed_data = (1 - MIX_RATIO) * data + MIX_RATIO * newdata

        out_data = mixed_data.astype(np.float32).tobytes()
        return (out_data, pyaudio.paContinue)
    except Exception as e:
        print(f"Callback error: {e}")
        return (None, pyaudio.paAbort)

class AudioMixer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initAudio()

    def initUI(self):
        self.mix_label = QLabel(f"Mix Ratio: {MIX_RATIO:.2f}", self)
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(MIX_RATIO * 100))
        self.slider.valueChanged.connect(self.update_mix_ratio)

        self.toggle_button = QPushButton("Pair entanglement", self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_pairs)

        layout = QVBoxLayout()
        layout.addWidget(self.mix_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.toggle_button)
        self.setLayout(layout)

        self.setWindowTitle('Quantum Noise Mixer')
        self.show()

    def initAudio(self):
        self.stream = p.open(format=pyaudio.paFloat32,
                            channels=1,
                            rate=RATE,
                            input=True,
                            output=True,
                            stream_callback=audio_callback,
                            frames_per_buffer=CHUNK)
        self.stream.start_stream()

    def update_mix_ratio(self, value):
        global MIX_RATIO
        MIX_RATIO = value / 100.0
        self.mix_label.setText(f"Mix Ratio: {MIX_RATIO:.2f}")

    def toggle_pairs(self):
        global USE_PAIRS
        USE_PAIRS = not USE_PAIRS

    def closeEvent(self, event):
        self.stream.stop_stream()
        self.stream.close()
        p.terminate()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mixer = AudioMixer()
    sys.exit(app.exec_())
