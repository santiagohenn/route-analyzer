import os
import sys

def process_file(filename):
    input_folder = "results_client"
    output_folder = "time_series"
    os.makedirs(output_folder, exist_ok=True)
    if not filename.endswith(".txt"):
        input_file_path = os.path.join(input_folder, filename + ".txt")
    else:
        input_file_path = os.path.join(input_folder, filename)
    base_filename = filename.replace(".txt", "")
    processed_filename = os.path.join(output_folder, base_filename + "_ts.csv")

    sequence = []
    sender_relative_time = []
    receiver_relative_time = []
    sender_to_receiver_latency = []
    receiver_to_sender_latency = []
    experiment_starts_at = 0

    with open(input_file_path, 'r') as f:
        lines = f.readlines()
        if len(lines) > 0:
            # TODO : for absolute time, use the first line's timestamp
            experiment_starts_at = float(lines[0].split('|')[1])
        f.seek(0)

        for line in f:
            line = line.strip()
            if not line or line.startswith('sequence'):
                continue
            parts = line.split('|')
            if len(parts) < 5:
                continue

            seq = int(parts[0])
            start_ts = float(parts[1])
            bounce_ts = float(parts[3])
            received_ts = float(parts[4])

            sequence.append(seq)
            sender_relative_time.append((start_ts - experiment_starts_at) / 1e6)
            receiver_relative_time.append((bounce_ts - experiment_starts_at) / 1e6)
            sender_to_receiver_latency.append((bounce_ts - start_ts) / 1e6)
            receiver_to_sender_latency.append((received_ts - bounce_ts) / 1e6)

    with open(processed_filename, 'w') as f:
        f.write("sequence,sent_at,response_at,sender_to_receiver,receiver_to_sender\n")
        for seq, sent, res, bms, rmb in zip(sequence, sender_relative_time, receiver_relative_time, sender_to_receiver_latency, receiver_to_sender_latency):
            f.write(f"{seq},{sent},{res},{bms},{rmb}\n")

    print(f"Processed file saved to {processed_filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = input("Enter raw data filename: ")
    process_file(filename)