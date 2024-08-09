import pandas as pd
import re

def extract_packet_info(log_data):
    transmissions = []
    acks = []
    for line in log_data:
        parts = line.strip().split('\t', 2)
        if len(parts) == 3:
            timestamp, node_id, message = parts
            if "packet sent" in message:
                transmissions.append((timestamp, node_id, message))
            elif "packet received" in message or "DAO-ACK" in message:
                acks.append((timestamp, node_id, message))
    return transmissions, acks

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

def analyze_log_file(file_path):
    with open(file_path, 'r') as file:
        log_data = file.readlines()

    # Extract packet information
    transmissions_data, acks_data = extract_packet_info(log_data)

    # Create DataFrames
    columns = ['timestamp', 'node_id', 'message']
    df_transmissions = pd.DataFrame(transmissions_data, columns=columns)
    df_acks = pd.DataFrame(acks_data, columns=columns)

    # Convert timestamps to floats for accurate calculations
    df_transmissions['timestamp'] = df_transmissions['timestamp'].astype(float)
    df_acks['timestamp'] = df_acks['timestamp'].astype(float)

    # Calculate packet loss rate
    packet_loss_rate = calculate_packet_loss(df_transmissions, df_acks)
    
    return packet_loss_rate

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    packet_loss_rate = analyze_log_file(log_file)
    print(f"Packet Loss Rate: {packet_loss_rate:.2f}%")
