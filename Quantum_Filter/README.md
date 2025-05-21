# overview

This python code implements a quantum filter that takes in an analog input from the mic/line in, encodes it into a set of Ry rotations for each qubit and outputs the results of the measurement to the audio out.

The quantum part can also contain pair-wise correlation between qubits after rotation.

it leverages pyaudio for input/output and PyQT5 for its UI. Most of the heavy lifting is done using numpy.
