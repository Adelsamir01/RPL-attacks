import pandas as pd
import re
import sys

def extract_packet_info(log_data):
    transmissions = []
    acks = []
    energy = []
    for line in log_data:
        parts = line.strip().split('\t', 2)
        if len(parts) == 3:
            timestamp, node_id, message = parts
            if "packet sent" in message:
                transmissions.append((timestamp, node_id, message))
            elif "packet received" in message or "DAO-ACK" in message:
                acks.append((timestamp, node_id, message))
            elif "Energest" in message:
                energy.append((timestamp, node_id, message))
    return transmissions, acks, energy

def extract_packet_id(message):
    match = re.search(r'LL-\d+', message)
    return match.group(0) if match else None

def calculate_packet_loss(transmissions, acks, time_window=1.0):
    matched_acks = 0
    for _, transmission in transmissions.iterrows():
        matched_ack = acks[(acks['node_id'] == transmission['node_id']) & 
                           (acks['timestamp'] >= transmission['timestamp']) & 
                           (acks['timestamp'] <= transmission['timestamp'] + time_window)]
        if not matched_ack.empty:
            matched_acks += 1
    total_transmissions = len(transmissions)
    packet_loss_rate = ((total_transmissions - matched_acks) / total_transmissions) * 100
    return packet_loss_rate

def calculate_throughput(transmissions, duration):
    total_packets = len(transmissions)
    throughput = total_packets / duration
    return throughput

def calculate_latency(transmissions, acks):
    latencies = []
    for _, transmission in transmissions.iterrows():
        ack = acks[(acks['node_id'] == transmission['node_id']) & 
                   (acks['timestamp'] >= transmission['timestamp']) & 
                   (acks['timestamp'] <= transmission['timestamp'] + 1.0)]
        if not ack.empty:
            latency = ack['timestamp'].min() - transmission['timestamp']
            latencies.append(latency)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    return avg_latency

def calculate_energy_consumption(energy_logs):
    total_energy = 0
    for log in energy_logs:
        match = re.search(r'CPU\s*:\s*(\d+)', log[2])
        if match:
            total_energy += int(match.group(1))
    return total_energy

def analyze_log_file(file_path):
    with open(file_path, 'r') as file:
        log_data = file.readlines()

    # Extract packet information
    transmissions_data, acks_data, energy_data = extract_packet_info(log_data)

    # Create DataFrames
    columns = ['timestamp', 'node_id', 'message']
    df_transmissions = pd.DataFrame(transmissions_data, columns=columns)
    df_acks = pd.DataFrame(acks_data, columns=columns)
    df_energy = pd.DataFrame(energy_data, columns=columns)

    # Convert timestamps to floats for accurate calculations
    df_transmissions['timestamp'] = df_transmissions['timestamp'].astype(float)
    df_acks['timestamp'] = df_acks['timestamp'].astype(float)
    df_energy['timestamp'] = df_energy['timestamp'].astype(float)

    # Calculate packet loss rate
    packet_loss_rate = calculate_packet_loss(df_transmissions, df_acks)

    # Calculate throughput
    duration = df_transmissions['timestamp'].max() - df_transmissions['timestamp'].min()
    throughput = calculate_throughput(df_transmissions, duration)

    # Calculate average latency
    avg_latency = calculate_latency(df_transmissions, df_acks)

    # Calculate total energy consumption
    total_energy_consumption = calculate_energy_consumption(energy_data)
    
    metrics = {
        'Packet Loss Rate': packet_loss_rate,
        'Throughput (packets/sec)': throughput,
        'Average Latency (sec)': avg_latency,
        'Total Energy Consumption (CPU cycles)': total_energy_consumption
    }
    
    return metrics

def generate_report(metrics, file_path):
    print("\nNetwork Performance Report")
    print("==========================\n")
    print(f"Log File: {file_path}")
    print("--------------------------")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.2f}")
    print("\n==========================\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    metrics = analyze_log_file(log_file)
    generate_report(metrics, log_file)
