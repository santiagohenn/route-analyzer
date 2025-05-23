import sys
import numpy as np
import matplotlib.pyplot as plt

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = input("Enter filename: ")

    time_1 = []
    time_2 = []
    signal_1 = []
    signal_2 = []

    experiment_starts_at = 0
    with open(filename, 'r') as f:
        lines = f.readlines()
        if len(lines) > 0:
            experiment_starts_at = float(lines[0].split('|')[1])
        for line in lines:
            line = line.strip()
            if not line or line.startswith('sequence'):
                continue
            parts = line.split('|')
            if len(parts) < 5:
                continue
            t = (float(parts[1]) - experiment_starts_at) / 1e9  # ns -> s
            time_1.append(t)

            t = (float(parts[3]) - float(lines[0].split('|')[3])) / 1e9  # ns -> s
            time_2.append(t)

            # signal_1:
            end_timestamp = float(parts[3])
            start_timestamp = float(parts[1])
            y = (end_timestamp - start_timestamp) / 1e9  # ns -> s
            signal_1.append(y)

            # signal_2:
            end_timestamp = float(parts[4])
            start_timestamp = float(parts[3])
            y = (end_timestamp - start_timestamp) / 1e9  # ns -> s
            signal_2.append(y)

    # FFT UPLINK

    # Interpolate to regular time_1 intervals for FFT
    t_min, t_max = min(time_1), max(time_1)
    # print("time_1 interval: ", t_max - t_min)
    num_points = len(time_1)
    regular_time = np.linspace(t_min, t_max, num_points)
    interpolated_signal = np.interp(regular_time, time_1, signal_1)

    # Remove mean to focus on oscillations
    regular_signal = interpolated_signal - np.mean(interpolated_signal)

    fft_vals_uplink = np.fft.rfft(regular_signal)
    fft_freqs_uplink = np.fft.rfftfreq(num_points, d=(regular_time[1] - regular_time[0]))

    # FFT DOWNLINK

    t_min, t_max = min(time_2), max(time_2)
    num_points = len(time_2)
    regular_time = np.linspace(t_min, t_max, num_points)
    interpolated_signal = np.interp(regular_time, time_2, signal_2)
    regular_signal = interpolated_signal - np.mean(interpolated_signal)

    fft_vals_downlink = np.fft.rfft(regular_signal)
    fft_freqs_downlink = np.fft.rfftfreq(num_points, d=(regular_time[1] - regular_time[0]))

    # Plotting
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(time_1, np.array(signal_1) * 1e3, label='Lab -> SL -> Server', color='tab:blue', alpha=0.7, linewidth=0.8)
    plt.plot(time_1, np.array(signal_2) * 1e3, label='Server -> SL -> Lab', color='tab:orange', alpha=0.7, linewidth=0.8)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xlabel("Time [s]")
    plt.ylabel("Latency [ms]")
    plt.title("Packet Latency")
    plt.tight_layout()

    freq_min = 0
    freq_max = 1

    plt.subplot(1, 2, 2)
    plt.plot(fft_freqs_uplink, np.abs(fft_vals_uplink), label="FFT uplink", color='tab:blue', alpha=0.7, linewidth=1.2)
    #plt.plot(fft_freqs_downlink, np.abs(fft_vals_downlink), label="FFT downlink", color='tab:orange', alpha=0.7, linewidth=1.2)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Amplitude")
    plt.title("FFT Spectrum of Latencies")
    plt.xlim(freq_min, freq_max)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    [plt.axvline(i/15, color='darkblue', linestyle='--', linewidth=2, alpha=0.15) for i in range(1, 6)]
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()