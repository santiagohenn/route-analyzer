import sys
import os
import matplotlib.pyplot as plt

def main():
    # Get filename from user input or command line
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = input("Enter experiment: ")

    processed_filename = os.path.join("time_series", filename + "_processed.csv")

    sequence = []
    sender_to_receiver = []
    receiver_to_sender = []

    with open(processed_filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('sequence'):
                continue  # skip header or empty lines
            parts = line.split(',')
            if len(parts) < 3:
                continue  # skip malformed lines

            sequence.append(float(parts[0])) # Replace with absolute time
            sender_to_receiver.append(float(parts[2]))
            receiver_to_sender.append(float(parts[3]))

    plt.figure(figsize=(10, 6))
    plt.plot(sequence, sender_to_receiver, label='Lab -> SL -> Server', alpha=0.5, marker='o', markersize=2)
    plt.plot(sequence, receiver_to_sender, label='Server -> SL -> Lab', alpha=0.5, marker='o', markersize=2)
    plt.xlabel('Time')
    plt.ylabel('Latency [ms]')
    plt.title('Processed Latency Data')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()