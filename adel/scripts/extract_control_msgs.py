import os
import pandas as pd
import re
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

def extract_packet_info(log_data):
    control_msgs = defaultdict(lambda: {'DIS': 0, 'DIO': 0, 'DAO': 0})
    for line in log_data:
        parts = line.strip().split('\t', 2)
        if len(parts) == 3:
            timestamp, node_id_str, message = parts
            node_id = int(re.search(r'\d+', node_id_str).group())
            if "sending a DIS" in message:
                control_msgs[node_id]['DIS'] += 1
            elif "sending a DIO" in message:
                control_msgs[node_id]['DIO'] += 1
            elif "sending a DAO" in message:
                control_msgs[node_id]['DAO'] += 1
    return control_msgs

def analyze_log_file(file_path):
    print(f"Analyzing log file: {file_path}")
    with open(file_path, 'r') as file:
        log_data = file.readlines()

    # Extract control message information
    control_msgs = extract_packet_info(log_data)

    return control_msgs

def generate_control_message_visualization(control_msgs_file1, control_msgs_file2, file1, file2, output_folder):
    print(f"Generating control message visualizations")
    nodes = sorted(set(control_msgs_file1.keys()).union(set(control_msgs_file2.keys())))
    control_messages_file1 = {msg_type: [control_msgs_file1[node][msg_type] if node in control_msgs_file1 else 0 for node in nodes] for msg_type in ['DIS', 'DIO', 'DAO']}
    control_messages_file2 = {msg_type: [control_msgs_file2[node][msg_type] if node in control_msgs_file2 else 0 for node in nodes] for msg_type in ['DIS', 'DIO', 'DAO']}
    
    plt.figure(figsize=(10, 6))
    bar_width = 0.25
    index = range(len(nodes))
    
    plt.bar(index, control_messages_file1['DIS'], bar_width, label=f'DIS {os.path.basename(file1)}', color='purple')
    plt.bar([i + bar_width for i in index], control_messages_file2['DIS'], bar_width, label=f'DIS {os.path.basename(file2)}', color='orange')
    plt.bar([i + 2 * bar_width for i in index], control_messages_file1['DIO'], bar_width, label=f'DIO {os.path.basename(file1)}', color='cyan')
    plt.bar([i + 3 * bar_width for i in index], control_messages_file2['DIO'], bar_width, label=f'DIO {os.path.basename(file2)}', color='green')
    plt.bar([i + 4 * bar_width for i in index], control_messages_file1['DAO'], bar_width, label=f'DAO {os.path.basename(file1)}', color='blue')
    plt.bar([i + 5 * bar_width for i in index], control_messages_file2['DAO'], bar_width, label=f'DAO {os.path.basename(file2)}', color='red')
    
    plt.xlabel('Node')
    plt.ylabel('Number of Control Messages')
    plt.title('Control Messages Comparison')
    plt.xticks([i + 2.5 * bar_width for i in index], nodes, rotation=90)
    plt.legend()
    plt.tight_layout()
    output_path = os.path.join(output_folder, 'control_messages_comparison.png')
    plt.savefig(output_path)
    plt.show()  # Open the visual
    print(f"Visualization saved in {output_path}")

def main(file1, file2):
    control_msgs_file1 = analyze_log_file(file1)
    control_msgs_file2 = analyze_log_file(file2)
    
    output_folder = os.path.dirname(file1)
    generate_control_message_visualization(control_msgs_file1, control_msgs_file2, file1, file2, output_folder)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 script.py <log_file1> <log_file2>")
        sys.exit(1)
    
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    main(file1, file2)
