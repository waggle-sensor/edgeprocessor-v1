import pyaudio
import numpy as np

# constants for audio recording
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5

audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=9)
#stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

frames = []
audioop_frames = b''

# Recording audio from the input device
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(np.frombuffer(data, dtype=np.int16))
    audioop_frames += data

# Change data format from audio to np.array
numpydata = np.hstack(frames)
times = np.arange(len(numpydata))/float(RATE)

N = numpydata.shape[0] # the total number of samples: 10 sec * 44100 sampling rate
T = 1.0 / RATE # a unit time for each sample: 44100 samples per a second

yf = np.fft.fftn(numpydata) # the n-dimensional FFT
xf = np.linspace(0.0, 1.0/(2.0*T), N//2) # 1.0/(2.0*T) = RATE / 2

octave = {}
avg = []
medium = [31, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000] # Medium? of octave, hearable frequency

for i in range(10):
    octave[i] = []

val = yf[0:N//2]

for idx in range(len(xf)):
    if xf[idx] > 20 and xf[idx] < 44:
        octave[0].append(val[idx])
    elif xf[idx] > 43 and xf[idx] < 88:
        octave[1].append(val[idx])
    elif xf[idx] > 87 and xf[idx] < 176:
        octave[2].append(val[idx])
    elif xf[idx] > 175 and xf[idx] < 353:
        octave[3].append(val[idx])
    elif xf[idx] > 352 and xf[idx] < 707:
        octave[4].append(val[idx])
    elif xf[idx] > 706 and xf[idx] < 1414:
        octave[5].append(val[idx])
    elif xf[idx] > 1413 and xf[idx] < 2825:
        octave[6].append(val[idx])
    elif xf[idx] > 2824 and xf[idx] < 5650:
        octave[7].append(val[idx])
    elif xf[idx] > 5649 and xf[idx] < 11300:
        octave[8].append(val[idx])
    elif xf[idx] > 11299:
        octave[9].append(val[idx])

for di in range(len(octave)):
    avg.append(sum(octave[di])/len(octave[di]))

avg = np.asarray(avg)
avgdb = 10*np.log10(np.abs(avg))

a = []
b = 0,
for ia in range(len(avg)):
    a.append(10**(avgdb[ia]/10))
    b = b + a[ia]

sdb = 10*np.log10(b)

# sdb --> addtion of SPL, avgdb --> average of each octave
