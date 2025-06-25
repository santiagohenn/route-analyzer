import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
from scipy.signal import find_peaks
import seaborn as sns

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

# --- Event detection: find peaks in the signal ---
peaks, _ = find_peaks(signal, height=np.mean(signal) + 6 * np.std(signal), distance=1000)
event_indices = peaks

# --- Parameters: N points before, M points after each event ---
N = 500  # Number of points before peak
M = 500  # Number of points after peak

N_offset = 10  # How much before the peak to start the averaging window
M_offset = 10  # How after the peak to start the averaging window

M = M + M_offset
N = N + N_offset

means_before = []
means_after = []
peak_minus_before = []
peak_minus_after = []
peak_values = []

for idx in event_indices:
    if idx - N < 0:
        continue
    before = signal[idx - N:idx - N_offset]
    after = signal[idx + M_offset:min(idx + M, len(signal))]
    if len(after) < M - M_offset:
        continue
    peak_val = signal[idx]
    mean_before = np.mean(before)
    mean_after = np.mean(after)
    means_before.append(mean_before)
    means_after.append(mean_after)
    peak_values.append(peak_val)
    peak_minus_before.append(peak_val - mean_before)
    peak_minus_after.append(peak_val - mean_after)

# --- Plotting ---
plt.figure(figsize=(12,6))
plt.plot(t, signal, label='sender_to_receiver', marker='.', markersize=4, linewidth=1)
for idx in event_indices:
    if idx-N < 0 or idx+M > len(signal):
        continue
    plt.axvspan(t[idx-N], t[idx - N_offset], color='green', alpha=0.1)
    plt.axvspan(t[idx + M_offset], t[min(idx + M, len(t)-1)], color='blue', alpha=0.1)
plt.scatter(t[event_indices], signal[event_indices], color='red', label='Detected Events (Peaks)', s=20)
plt.xlabel('sent_at (s)')
plt.ylabel('sender_to_receiver')
plt.legend()
plt.title('Signal with Detected Events and Analysis Windows')
plt.show()

# --- Plot histograms (binned distributions) with publication-quality style ---

sns.set_context("paper")
sns.set_style("whitegrid")

plt.figure(figsize=(8, 4))
bins = np.linspace(
    min(min(peak_minus_before), min(peak_minus_after)),
    max(max(peak_minus_before), max(peak_minus_after)),
    20
)
sns.histplot(peak_minus_before, bins=bins, color='C0', alpha=0.7, label='Peak - Mean (Before)', kde=True, stat="count")
sns.histplot(peak_minus_after, bins=bins, color='C1', alpha=0.7, label='Peak - Mean (After)', kde=True, stat="count")

plt.xlabel('Latency Difference (ms)', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.legend(fontsize=11, frameon=True)
plt.title('Distribution of Latency Change Around Events', fontsize=13)
plt.tight_layout()
sns.despine()
plt.show()

# --- Print statistics ---
print(f"Peak - Mean(Before): mean={np.mean(peak_minus_before):.4f}, std={np.std(peak_minus_before):.4f}")
print(f"Peak - Mean(After):  mean={np.mean(peak_minus_after):.4f}, std={np.std(peak_minus_after):.4f}")