# route-analyzer

## Overview

This project provides a UDP-based client and server for network route analysis, with configurable parameters via a shared `config.ini` file. The client sends timestamped packets to the server, which echoes them back, enabling latency and jitter analysis.

---

## Requirements

- Python 3.x
- `chrony` (for clock synchronization, optional but recommended)
- `matplotlib`, `numpy` (for plotting scripts)
- Linux (for `chronyc` usage)

---

## Configuration

Edit `config.ini` to set parameters for both server and client. Only relevant options will be pulled by the scripts. Example:

```ini
[server]
host = ::
port = 2230
timeout = 60
batch_size = 100
max_lines = 10000

[client]
server_host = ::1
server_port = 2230
send_interval_ms = 100
total_packets = 500
response_timeout = 5
random_length = 20
batch_size = 100
max_lines = 10000
```

---

## Usage

### 1. Start the Server

```bash
python3 server.py --config config.ini
```

You can override any config value via command-line arguments, e.g.:

```bash
python3 server.py --config config.ini --port 9999
```

---

### 2. Run the Client

```bash
python3 client.py --config config.ini
```

### 3. Time sync (Recommended):

Sync the system clock, run the script, sync again and log the clock metrics. If you need to be really precise with time keeping, you'll have the metrics to compensate the clock if needed (not implemented).

For Linux:

```bash
#!/bin/bash

# Sync system clock
sudo chronyc -a makestep

# Run the Python client with config.ini
python3 server.py --config config.ini

# (optional) Sync and log time tracking metrics
# sudo chronyc -a makestep
# chronyc tracking > time_logs/chronyc_tracking_$(date +%Y%m%d_%H%M%S).log
```

For Windows, [Meinberg](https://www.meinbergglobal.com/english/sw/ntp.htm) gives you precise time synchronization.

Make the bash executable:

```bash
chmod +x run_server.sh
chmod +x run_client.sh
```

Run server:

```bash
./run_server.sh
```


Run client (bash is analogous to the server):
```bash
./run_client.sh
```

---

## Help

Type --help as arg on server/client to get information on configurations. These override config.ini if provided.

| Command              | Description                                |
|----------------------|--------------------------------------------|
| `--config`           | Path to config file (INI format)           |
| `--server-host`      | Server host/IP                             |
| `--server-port`      | Server port                                |
| `--send-interval`    | Interval between packets (ms)              |
| `--total-packets`    | Total packets to send                      |
| `--response-timeout` | Wait time for responses (s)                |
| `--random-length`    | Random string length                       |
| `--batch-size`       | Batch size for saving responses            |
| `--max-lines`        | Max lines per file                         |

## Notes

- You may need `sudo` for `chronyc`.
- Adjust the path to `client.py`, `server.py`, and `config.ini` if needed.
- Make sure you have Python 3 and chrony installed.
- Output files are saved in `client_responses/` and `server_packets/`.

---

## Plotting and Analysis

See `plot.py` and `fft_plot.py` for scripts to analyze and visualize the collected data.

---