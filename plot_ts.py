import sys
import os
import matplotlib.pyplot as plt

def main():
    # Get filename from user input or command line
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = input("Enter experiment: ")

    if filename.endswith(".txt"):
        filename = filename[:-4]
    
    if "exp" not in filename:
        filename = "exp_" + filename

    processed_filename = os.path.join("time_series", filename + ".csv")

    sender_sent_at_relative = []
    receiver_sent_at_relative = []
    sender_to_receiver = []
    receiver_to_sender = []

    experiment_starts_at = 0

    with open(processed_filename, 'r') as f:

        for line in f:
            line = line.strip()
            if not line or line.startswith('sequence'):
                continue  # skip header or empty lines
            parts = line.split(',')
            if len(parts) < 3:
                continue  # skip malformed lines

            sender_sent_at_relative.append(float(parts[1]) * 1e-3)
            receiver_sent_at_relative.append(float(parts[2]) * 1e-3)
            sender_to_receiver.append(float(parts[3]))
            receiver_to_sender.append(float(parts[4]))

    plt.figure(figsize=(10, 6))
    plt.plot(sender_sent_at_relative, sender_to_receiver, label='Lab -> SL -> Server', alpha=0.5, marker='o', markersize=2)
    plt.plot(receiver_sent_at_relative, receiver_to_sender, label='Server -> SL -> Lab', alpha=0.5, marker='o', markersize=2)
    plt.xlabel('Time [s]')
    plt.ylabel('Latency [ms]')
    plt.title('Processed Latency Data')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()