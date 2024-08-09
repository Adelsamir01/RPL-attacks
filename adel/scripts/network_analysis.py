import os
import pandas as pd
import re
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

def extract_packet_info(log_data):
    transmissions = []
    acks = []
    control_msgs = defaultdict(lambda: {'DIS': 0, 'DIO': 0, 'DAO': 0, 'rejoin': 0, 'parent_changes': 0, 'ack_rate': 0, 'rdc': 0})
    parent_changes = defaultdict(int)
    for line in log_data:
        parts = line.strip().split('\t', 2)
        if len(parts) == 3:
            timestamp, node_id_str, message = parts
            node_id = int(re.search(r'\d+', node_id_str).group())
            if "packet sent" in message:
                transmissions.append((timestamp, node_id, message))
            elif "packet received" in message or "DAO-ACK" in message:
                acks.append((timestamp, node_id, message))
            elif "sending a DIS" in message:
                control_msgs[node_id]['DIS'] += 1
            elif "sending a DIO" in message:
                control_msgs[node_id]['DIO'] += 1
            elif "sending a DAO" in message:
                control_msgs[node_id]['DAO'] += 1
            elif "rejoined the DODAG" in message:
                control_msgs[node_id]['rejoin'] += 1
            elif "routing parent change" in message:
                control_msgs[node_id]['parent_changes'] += 1
            elif "ack received from parent" in message:
                control_msgs[node_id]['ack_rate'] += 1
            elif "radio duty cycle" in message:
                # Extract RDC percentage from message
                rdc_match = re.search(r'(\d+(\.\d+)?)%', message)
                if rdc_match:
                    control_msgs[node_id]['rdc'] = float(rdc_match.group(1))
    return transmissions, acks, control_msgs

def calculate_packet_delivery_ratio(transmissions, acks, time_window=1.0):
    matched_acks = 0
    for _, transmission in transmissions.iterrows():
        matched_ack = acks[(acks['node_id'] == transmission['node_id']) & 
                           (acks['timestamp'] >= transmission['timestamp']) & 
                           (acks['timestamp'] <= transmission['timestamp'] + time_window)]
        if not matched_ack.empty:
            matched_acks += 1
    total_transmissions = len(transmissions)
    packet_delivery_ratio = (matched_acks / total_transmissions) * 100
    return packet_delivery_ratio

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

def analyze_node_behavior(df_transmissions, df_acks, control_msgs):
    nodes = sorted(df_transmissions['node_id'].unique())
    node_metrics = {}
    for node in nodes:
        node_transmissions = df_transmissions[df_transmissions['node_id'] == node]
        node_acks = df_acks[df_acks['node_id'] == node]
        
        packet_delivery_ratio = calculate_packet_delivery_ratio(node_transmissions, node_acks)
        duration = node_transmissions['timestamp'].max() - node_transmissions['timestamp'].min()
        throughput = calculate_throughput(node_transmissions, duration)
        avg_latency = calculate_latency(node_transmissions, node_acks)
        control_msg_counts = control_msgs[node]
        
        node_metrics[node] = {
            'Packet Delivery Ratio': packet_delivery_ratio,
            'Throughput (packets/sec)': throughput,
            'Average Latency (sec)': avg_latency,
            'Control Messages': control_msg_counts,
            'Rejoins': control_msgs[node]['rejoin'],
            'Parent Changes': control_msgs[node]['parent_changes'],
            'Ack Rate': control_msgs[node]['ack_rate'],
            'RDC (%)': control_msgs[node]['rdc']
        }
    return node_metrics

def analyze_log_file(file_path):
    print(f"Analyzing log file: {file_path}")
    with open(file_path, 'r') as file:
        log_data = file.readlines()

    # Extract packet information
    transmissions_data, acks_data, control_msgs = extract_packet_info(log_data)

    # Create DataFrames
    columns = ['timestamp', 'node_id', 'message']
    df_transmissions = pd.DataFrame(transmissions_data, columns=columns)
    df_acks = pd.DataFrame(acks_data, columns=columns)

    # Convert timestamps to floats for accurate calculations
    df_transmissions['timestamp'] = df_transmissions['timestamp'].astype(float)
    df_acks['timestamp'] = df_acks['timestamp'].astype(float)

    # Calculate overall metrics
    packet_delivery_ratio = calculate_packet_delivery_ratio(df_transmissions, df_acks)
    duration = df_transmissions['timestamp'].max() - df_transmissions['timestamp'].min()
    throughput = calculate_throughput(df_transmissions, duration)
    avg_latency = calculate_latency(df_transmissions, df_acks)
    
    overall_metrics = {
        'Packet Delivery Ratio': packet_delivery_ratio,
        'Throughput (packets/sec)': throughput,
        'Average Latency (sec)': avg_latency
    }

    # Calculate per-node metrics
    node_metrics = analyze_node_behavior(df_transmissions, df_acks, control_msgs)
    
    return overall_metrics, node_metrics

def generate_report(overall_metrics, node_metrics, output_folder, attack_name):
    print(f"Generating report for: {attack_name}")
    os.makedirs(output_folder, exist_ok=True)
    log_file_path = os.path.join(output_folder, f'{attack_name}_metrics.txt')
    with open(log_file_path, 'w') as log_file:
        log_file.write("\nNetwork Performance Report\n")
        log_file.write("==========================\n\n")
        log_file.write(f"Log File: {os.path.basename(output_folder)}\n")
        log_file.write("\nOverall Metrics:\n")
        log_file.write("--------------------------\n")
        for metric, value in overall_metrics.items():
            log_file.write(f"{metric}: {value:.2f}\n")
        
        log_file.write("\nNode-specific Metrics:\n")
        log_file.write("--------------------------\n")
        ranked_nodes = sorted(node_metrics.items())
        for node, metrics in ranked_nodes:
            log_file.write(f"\nNode {node}:\n")
            for metric, value in metrics.items():
                if isinstance(value, dict):
                    log_file.write(f"  {metric}:\n")
                    for msg_type, count in value.items():
                        log_file.write(f"    {msg_type}: {count}\n")
                else:
                    log_file.write(f"  {metric}: {value:.2f}\n")
    
    return log_file_path

def generate_comparison_visualizations(node_metrics_no_attack, node_metrics_attack, attack_name, output_folder):
    print(f"Generating comparison visualizations for: {attack_name}")
    nodes = sorted(node_metrics_no_attack.keys())
    packet_delivery_ratios_no_attack = [node_metrics_no_attack[node]['Packet Delivery Ratio'] for node in nodes]
    throughputs_no_attack = [node_metrics_no_attack[node]['Throughput (packets/sec)'] for node in nodes]
    latencies_no_attack = [node_metrics_no_attack[node]['Average Latency (sec)'] for node in nodes]
    control_messages_no_attack = {msg_type: [node_metrics_no_attack[node]['Control Messages'][msg_type] for node in nodes] for msg_type in ['DIS', 'DIO', 'DAO']}
    rejoins_no_attack = [node_metrics_no_attack[node]['Rejoins'] for node in nodes]
    parent_changes_no_attack = [node_metrics_no_attack[node]['Parent Changes'] for node in nodes]
    ack_rate_no_attack = [node_metrics_no_attack[node]['Ack Rate'] for node in nodes]
    rdc_no_attack = [node_metrics_no_attack[node]['RDC (%)'] for node in nodes]
    
    packet_delivery_ratios_attack = [node_metrics_attack[node]['Packet Delivery Ratio'] for node in nodes]
    throughputs_attack = [node_metrics_attack[node]['Throughput (packets/sec)'] for node in nodes]
    latencies_attack = [node_metrics_attack[node]['Average Latency (sec)'] for node in nodes]
    control_messages_attack = {msg_type: [node_metrics_attack[node]['Control Messages'][msg_type] for node in nodes] for msg_type in ['DIS', 'DIO', 'DAO']}
    rejoins_attack = [node_metrics_attack[node]['Rejoins'] for node in nodes]
    parent_changes_attack = [node_metrics_attack[node]['Parent Changes'] for node in nodes]
    ack_rate_attack = [node_metrics_attack[node]['Ack Rate'] for node in nodes]
    rdc_attack = [node_metrics_attack[node]['RDC (%)'] for node in nodes]
    
    # Packet Delivery Ratio comparison
    plt.figure(figsize=(10, 6))
    plt.bar(nodes, packet_delivery_ratios_no_attack, width=0.4, label='No Attack', align='center')
    plt.bar(nodes, packet_delivery_ratios_attack, width=0.4, label=attack_name, align='edge')
    plt.xlabel('Node')
    plt.ylabel('Packet Delivery Ratio (%)')
    plt.title('Packet Delivery Ratio Comparison')
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'packet_delivery_ratio_comparison_{attack_name}.png'))
    
    # Throughput comparison
    plt.figure(figsize=(10, 6))
    plt.bar(nodes, throughputs_no_attack, width=0.4, label='No Attack', align='center')
    plt.bar(nodes, throughputs_attack, width=0.4, label=attack_name, align='edge')
    plt.xlabel('Node')
    plt.ylabel('Throughput (packets/sec)')
    plt.title('Throughput Comparison')
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'throughput_comparison_{attack_name}.png'))
    
    # Average Latency comparison
    plt.figure(figsize=(10, 6))
    plt.bar(nodes, latencies_no_attack, width=0.4, label='No Attack', align='center')
    plt.bar(nodes, latencies_attack, width=0.4, label=attack_name, align='edge')
    plt.xlabel('Node')
    plt.ylabel('Average Latency (sec)')
    plt.title('Average Latency Comparison')
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'latency_comparison_{attack_name}.png'))
    
    # Control Messages comparison
    plt.figure(figsize=(10, 6))
    bar_width = 0.25
    index = range(len(nodes))
    
    plt.bar(index, control_messages_no_attack['DIS'], bar_width, label='DIS No Attack', color='purple')
    plt.bar([i + bar_width for i in index], control_messages_attack['DIS'], bar_width, label=f'DIS {attack_name}', color='orange')
    plt.bar([i + 2 * bar_width for i in index], control_messages_no_attack['DIO'], bar_width, label='DIO No Attack', color='cyan')
    plt.bar([i + 3 * bar_width for i in index], control_messages_attack['DIO'], bar_width, label=f'DIO {attack_name}', color='green')
    plt.bar([i + 4 * bar_width for i in index], control_messages_no_attack['DAO'], bar_width, label='DAO No Attack', color='blue')
    plt.bar([i + 5 * bar_width for i in index], control_messages_attack['DAO'], bar_width, label=f'DAO {attack_name}', color='red')
    
    plt.xlabel('Node')
    plt.ylabel('Number of Control Messages')
    plt.title('Control Messages Comparison')
    plt.xticks([i + 2.5 * bar_width for i in index], nodes, rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'control_messages_comparison_{attack_name}.png'))
    
    # Rejoins comparison
    plt.figure(figsize=(10, 6))
    plt.bar(nodes, rejoins_no_attack, width=0.4, label='No Attack', align='center')
    plt.bar(nodes, rejoins_attack, width=0.4, label=attack_name, align='edge')
    plt.xlabel('Node')
    plt.ylabel('Number of Rejoins')
    plt.title('Rejoins Comparison')
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'rejoins_comparison_{attack_name}.png'))
    
    # Parent Changes comparison
    plt.figure(figsize=(10, 6))
    plt.bar(nodes, parent_changes_no_attack, width=0.4, label='No Attack', align='center')
    plt.bar(nodes, parent_changes_attack, width=0.4, label=attack_name, align='edge')
    plt.xlabel('Node')
    plt.ylabel('Number of Parent Changes')
    plt.title('Parent Changes Comparison')
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'parent_changes_comparison_{attack_name}.png'))
    
    # Ack Rate comparison
    plt.figure(figsize=(10, 6))
    plt.bar(nodes, ack_rate_no_attack, width=0.4, label='No Attack', align='center')
    plt.bar(nodes, ack_rate_attack, width=0.4, label=attack_name, align='edge')
    plt.xlabel('Node')
    plt.ylabel('Ack Rate')
    plt.title('Ack Rate Comparison')
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'ack_rate_comparison_{attack_name}.png'))
    
    # RDC comparison
    plt.figure(figsize=(10, 6))
    plt.bar(nodes, rdc_no_attack, width=0.4, label='No Attack', align='center')
    plt.bar(nodes, rdc_attack, width=0.4, label=attack_name, align='edge')
    plt.xlabel('Node')
    plt.ylabel('RDC (%)')
    plt.title('RDC Comparison')
    plt.legend()
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'rdc_comparison_{attack_name}.png'))

def process_files_in_directory(directory):
    no_attack_file = os.path.join(directory, 'normal.txt')
    overall_metrics_no_attack, node_metrics_no_attack = analyze_log_file(no_attack_file)
    
    for file_name in os.listdir(directory):
        if file_name.endswith('.txt') and file_name != 'normal.txt':
            file_path = os.path.join(directory, file_name)
            base_name = os.path.splitext(file_name)[0]
            output_folder = os.path.join(directory, f'no_attack_&_{base_name}')
            overall_metrics_attack, node_metrics_attack = analyze_log_file(file_path)
            generate_report(overall_metrics_attack, node_metrics_attack, output_folder, base_name)
            generate_comparison_visualizations(node_metrics_no_attack, node_metrics_attack, base_name, output_folder)
            print(f"Processed {file_name}, output saved in {output_folder}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_files_directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    process_files_in_directory(directory)

