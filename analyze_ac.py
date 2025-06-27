import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
from scipy.signal import find_peaks

# --- Argument parsing for experiment number ---
input_folder = "results_client"

series_number = "1"
if len(sys.argv) == 2:
    exp_number = sys.argv[1]
elif len(sys.argv) == 3:
    exp_number = sys.argv[1]
    series_number = sys.argv[2]
else:
    exp_number = input("Enter experiment number: ").strip()
    series_number = input("Enter series number: ").strip()

filename = "series_" + series_number + "_processed.csv"
processed_file_path = os.path.join(input_folder, "exp_" + exp_number, filename)

# --- Load data ---
df = pd.read_csv(processed_file_path)
t = df["sent_at"].values / 1000.0  # convert ms to seconds
signal = df["sender_to_receiver"].values
# signal = df["receiver_to_sender"].values

# --- Autocorrelation to estimate period ---
signal_demean = signal - np.mean(signal)
autocorr = np.correlate(signal_demean, signal_demean, mode='full')
autocorr = autocorr[autocorr.size // 2:]  # keep only positive lags

lags = np.arange(len(autocorr)) * np.median(np.diff(t))
peaks, _ = find_peaks(autocorr[1:], height=np.mean(autocorr[1:]) + 6 * np.std(signal), distance=1000)
if len(peaks) > 0:
    period_idx = peaks[0] + 1
    estimated_period = lags[period_idx]
else:
    estimated_period = 15  # fallback if no peak found

# Force period if desired
estimated_period = 15

print(f"Estimated period: {estimated_period:.2f} seconds")

# --- Slotting ---
slot_length = int(round(estimated_period / np.median(np.diff(t))))
print(f"Slot length in samples: {slot_length}")
n_slots = len(signal) // slot_length
slots = [signal[i*slot_length:(i+1)*slot_length] for i in range(n_slots) if len(signal[i*slot_length:(i+1)*slot_length]) == slot_length]

# --- Stack windows centered on the peak of each slot ---
W = 350  # points before and after the peak (window size = 2*W+1)
stacked = []
for slot in slots:
    peak_idx = np.argmax(slot)
    # Ensure window fits within slot
    if peak_idx - W < 0 or peak_idx + W >= len(slot):
        continue
    window = slot[peak_idx - W : peak_idx + W + 1]
    stacked.append(window)

stacked = np.array(stacked)
print(f"Number of slots/windows stacked: {len(stacked)}")

if stacked.shape[0] == 0:
    print("No valid slots/windows found for stacking. Try reducing W or check your data.")
    sys.exit(1)

mean_stacked = np.mean(stacked, axis=0)
std_stacked = np.std(stacked, axis=0)
max_stacked = np.max(stacked, axis=0)
center_time = (np.arange(-W, W+1)) * np.median(np.diff(t))

# Ensure lengths match before plotting
if len(center_time) != len(mean_stacked):
    print(f"Shape mismatch: center_time ({len(center_time)}), mean_stacked ({len(mean_stacked)})")
    sys.exit(1)

plt.figure(figsize=(10, 5))
# plt.axvline(0, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='Peak center')
plt.plot(center_time, mean_stacked, linestyle='-', marker='o', markersize=1, color='C0', label='Mean')
plt.fill_between(center_time, mean_stacked - std_stacked, mean_stacked + std_stacked, color='C0', alpha=0.2, label='±1 std')
plt.plot(center_time, max_stacked, color='C3', alpha=0.6, label='max')
plt.xlabel('Time relative reconf. peak (s)', fontsize=12)
plt.ylabel('Uplink latency (ms)', fontsize=12)
plt.title('Stacked Slots (centered on reconfiguration)', fontsize=14)
plt.legend(fontsize=11)
plt.grid(True, which='both', linestyle=':', linewidth=0.7, alpha=0.7)
plt.tight_layout()
plt.show()