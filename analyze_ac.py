import numpy as np
import json
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
from scipy.signal import find_peaks

# --- Argument parsing for experiment and series number ---
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

# --- Autocorrelation to estimate period ---
signal_demean = signal - np.mean(signal)
autocorr = np.correlate(signal_demean, signal_demean, mode='full')
autocorr = autocorr[autocorr.size // 2:]  # keep only positive lags

lags = np.arange(len(autocorr)) * np.median(np.diff(t))
peaks, _ = find_peaks(autocorr[1:], height=np.mean(autocorr[1:]) + 4 * np.std(signal), distance=1000)
if len(peaks) > 0:
    period_idx = peaks[0] + 1
    estimated_period = lags[period_idx]
else:
    estimated_period = 15  # fallback if no peak found

# Force period if desired
estimated_period = 15

print(f"Estimated period: {estimated_period:.2f} seconds")
print(f"Peaks detected: {len(peaks)}")

# --- Slotting ---
slot_length = int(round(estimated_period / np.median(np.diff(t))))
print(f"Slot length in samples: {slot_length}")
n_slots = len(signal) // slot_length
slots = [signal[i*slot_length:(i+1)*slot_length] for i in range(n_slots) if len(signal[i*slot_length:(i+1)*slot_length]) == slot_length]

print(f"Number of slots with peaks: {len(slots)}")

# --- Stack windows centered on the peak of each slot ---
W = 150  # points before and after the peak (window size = 2*W+1)
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

# Store the gap between the last value before the peak and the peak value for each slot
gaps = []
for i, slot in enumerate(slots):
    peak_idx = np.argmax(slot)
    if peak_idx - W < 0 or peak_idx + W >= len(slot):
        continue
    before_peak_idx = peak_idx - 1
    if before_peak_idx < 0:
        continue
    gap = slot[peak_idx] - slot[before_peak_idx]
    if gap < 20: # Ignore gaps that are too small
        continue
    gaps.append(gap)

mean_stacked = np.mean(stacked, axis=0)
std_stacked = np.std(stacked, axis=0)
max_stacked = np.max(stacked, axis=0)
min_stacked = np.min(stacked, axis=0)
center_time = (np.arange(-W, W+1)) * np.median(np.diff(t))

# Ensure lengths match before plotting
if len(center_time) != len(mean_stacked):
    print(f"Shape mismatch: center_time ({len(center_time)}), mean_stacked ({len(mean_stacked)})")
    sys.exit(1)

# Prepare directory for saving figures and stats
stats_dir = os.path.join(input_folder, f"exp_{exp_number}")
os.makedirs(stats_dir, exist_ok=True)

# Plot and save stacked slot figure
plt.figure(figsize=(10, 5))
plt.plot(center_time, mean_stacked, linestyle='-', marker='o', markersize=1, color='C0', label='Mean')
plt.fill_between(center_time, mean_stacked - std_stacked, mean_stacked + std_stacked, color='C0', alpha=0.2, label='±1 std')
plt.plot(center_time, max_stacked, color='C3', alpha=0.2, label='max')
plt.plot(center_time, min_stacked, color='green', alpha=0.2, label='min')
plt.xlabel('Time relative reconf. peak (s)', fontsize=12)
plt.ylabel('Uplink latency (ms)', fontsize=12)
plt.title('Stacked Slots (centered on reconfiguration)', fontsize=14)
plt.legend(fontsize=11)
plt.grid(True, which='both', linestyle=':', linewidth=0.7, alpha=0.7)
plt.tight_layout()
stacked_fig_path = os.path.join(stats_dir, f"stacked_slots_series_{series_number}.png")
plt.savefig(stacked_fig_path)
plt.show()

# Statistics on the gaps
if gaps:
    gaps = np.array(gaps)
    gap_stats = {
        "mean": float(np.mean(gaps)),
        "std": float(np.std(gaps)),
        "min": float(np.min(gaps)),
        "max": float(np.max(gaps)),
        "count": int(len(gaps))
    }
    
    print(f"Gap statistics (peak - last before peak):")
    print(f"  Mean: {gap_stats['mean']:.4f}")
    print(f"  Std:  {gap_stats['std']:.4f}")
    print(f"  Min:  {gap_stats['min']:.4f}")
    print(f"  Max:  {gap_stats['max']:.4f}")

    # Save statistics as JSON
    stats_path = os.path.join(stats_dir, f"gap_stats_series_{series_number}.json")
    with open(stats_path, "w") as f:
        json.dump(gap_stats, f, indent=4)

    # Plot and save histogram of gaps
    plt.figure(figsize=(7,4))
    plt.hist(gaps, bins=20, color='C2', alpha=0.75)
    plt.xlabel('Gap (peak - last before peak) [ms]')
    plt.ylabel('Count')
    plt.title('Distribution of Gap Values (Peak - Last Before Peak)')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    hist_fig_path = os.path.join(stats_dir, f"gap_hist_series_{series_number}.png")
    plt.savefig(hist_fig_path)
    plt.show()

else:
    print("No valid gaps found for statistics or plotting.")