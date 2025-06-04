import os

def process_file(filename):
    output_folder = "time_series"
    os.makedirs(output_folder, exist_ok=True)
    processed_filename = os.path.join(output_folder, filename + "_processed.csv")

    sequence = []
    bounce_minus_start = []
    received_minus_bounce = []
    experiment_starts_at = 0

    with open(filename, 'r') as f:
        lines = f.readlines()
        if len(lines) > 0:
            experiment_starts_at = float(lines[0].split('|')[1])
        f.seek(0)

        for line in f:
            line = line.strip()
            if not line or line.startswith('sequence'):
                continue
            parts = line.split('|')
            if len(parts) < 5:
                continue

            seq = (float(parts[1]) - experiment_starts_at) / 1e9
            start_ts = float(parts[1])
            bounce_ts = float(parts[3])
            received_ts = float(parts[4])

            sequence.append(seq)
            bounce_minus_start.append((bounce_ts - start_ts) / 1e6)
            received_minus_bounce.append((received_ts - bounce_ts) / 1e6)

    with open(processed_filename, 'w') as f:
        f.write("sequence,bounce_minus_start,received_minus_bounce\n")
        for seq, bms, rmb in zip(sequence, bounce_minus_start, received_minus_bounce):
            f.write(f"{seq},{bms},{rmb}\n")

    print(f"Processed file saved to {processed_filename}")

if __name__ == "__main__":
    filename = input("Enter raw data filename: ")
    process_file(filename)