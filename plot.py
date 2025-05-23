import sys
import matplotlib.pyplot as plt

def main():
    # Get filename from user input or command line
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = input("Enter filename: ")

    sequence = []
    bounce_minus_start = []
    received_minus_bounce = []
    experiment_starts_at = 0

    with open(filename, 'r') as f:

        lines = f.readlines()
        if len(lines) > 0:
            experiment_starts_at = float(lines[0].split('|')[1])
        f.seek(0)  # Reset file pointer to start for the main loop

        for line in f:
            line = line.strip()
            if not line or line.startswith('sequence'):
                continue  # skip header or empty lines
            parts = line.split('|')
            if len(parts) < 5:
                continue  # skip malformed lines

            # seq = int(parts[0])

            # Using time:
            seq = (float(parts[1]) - experiment_starts_at) / 1e9

            start_ts = float(parts[1])
            # payload = parts[2]  # not used
            bounce_ts = float(parts[3])
            received_ts = float(parts[4])

            sequence.append(seq)
            bounce_minus_start.append((bounce_ts - start_ts) / 1e6)
            received_minus_bounce.append((received_ts - bounce_ts) / 1e6)

    plt.figure(figsize=(10, 6))
    plt.plot(sequence, bounce_minus_start, label='Lab -> SL -> Server')
    # plt.plot(sequence, received_minus_bounce, label='Server -> SL -> Lab')
    plt.xlabel('Time')
    plt.ylabel('Latency [ms]')
    plt.title('')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()