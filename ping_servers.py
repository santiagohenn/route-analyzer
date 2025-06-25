from ping3 import ping

def ping_host(ip, count=5, timeout=1.0):
    latencies = []
    for _ in range(count):
        try:
            latency = ping(ip, timeout=timeout, unit='ms')
            latencies.append(latency if latency is not None else None)
        except Exception:
            latencies.append(None)
    valid_latencies = [l for l in latencies if l is not None]
    avg_latency = sum(valid_latencies) / len(valid_latencies) if valid_latencies else None
    return avg_latency, latencies

if __name__ == "__main__":
    targets = [
        "54.37.158.224",
        "208.83.226.9",
        "89.187.143.26",
    ]

    count = 5

    for ip in targets:
        avg, all_lat = ping_host(ip, count)
        if avg is not None:
            print(f"{ip} - Avg latency: {avg:.2f} ms ({[f'{l:.2f}' if l else 'fail' for l in all_lat]})")
        else:
            print(f"{ip} - All attempts failed")