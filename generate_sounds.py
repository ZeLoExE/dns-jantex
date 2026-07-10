"""Generate custom sound effects for DNS Jantex."""
import wave, struct, math, os

SAMPLE_RATE = 44100

def generate_tone(freq, duration_ms, volume=0.4, fade_out=True):
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        val = volume * math.sin(2 * math.pi * freq * t)
        if fade_out:
            fade_start = int(n_samples * 0.8)
            if i > fade_start:
                val *= 1.0 - (i - fade_start) / (n_samples - fade_start)
        samples.append(int(val * 32767))
    return samples

def save_wav(filename, samples):
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

os.makedirs('assets/sounds', exist_ok=True)

# Success chime: ascending three-tone (C5 -> E5 -> G5)
samples = []
samples += generate_tone(523, 120, 0.35)
samples += generate_tone(659, 180, 0.35)
samples += [0] * int(SAMPLE_RATE * 0.03)
samples += generate_tone(784, 200, 0.3)
save_wav('assets/sounds/success.wav', samples)
print(f'Success chime: {len(samples)/SAMPLE_RATE:.2f}s')

# Flush blip: quick descending tone (A5 -> E5 -> A4)
samples = []
samples += generate_tone(880, 60, 0.3)
samples += generate_tone(660, 80, 0.25)
samples += generate_tone(440, 120, 0.2)
save_wav('assets/sounds/flush.wav', samples)
print(f'Flush blip: {len(samples)/SAMPLE_RATE:.2f}s')

print('Done!')
