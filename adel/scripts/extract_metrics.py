import sys
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

def parse_log_file(file_path):
    data = defaultdict(list)
    with open(file_path, 'r') as file:
        for line in file:
            match = re.match(r'(?P<timestamp>\d+\.?\d*)\s+ID:(?P<id>\d+)\s+\[(?P<level>INFO|WARN|ERROR):\s*(?P<source>.*?)\s*\]\s*(?P<message>.*)', line)
            if match:
                data['timestamp'].append(float(match.group('timestamp')))
                data['id'].append(int(match.group('id')))
                data['level'].append(match.group('level'))
                data['source'].append(match.group('source').strip())
                data['message'].append(match.group('message').strip())
    return pd.DataFrame(data)

def calculate_metrics(df):
    nodes = df['id'].unique()
    metrics = defaultdict(dict)
    for node in nodes:
        node_df = df[df['id'] == node]
        metrics[node]['PDR'] = calculate_pdr(node_df)
        metrics[node]['Parent Changes'] = calculate_parent_changes(node_df)
        metrics[node]['Ack Rate'] = calculate_ack_rate(node_df)
        metrics[node]['RDC'] = calculate_rdc(node_df)
    metrics_df = pd.DataFrame(metrics).T
    metrics_df.index.name = 'Node'
    metrics_df = metrics_df.sort_index()
    return metrics_df

def calculate_pdr(df):
    sent_packets = df[df['message'].str.contains('Sending ICMPv6 packet')].shape[0]
    received_packets = df[df['message'].str.contains('packet received')].shape[0]
    return received_packets / sent_packets if sent_packets > 0 else 0

def calculate_parent_changes(df):
    parent_change_msgs = df[df['message'].str.contains('parent switch')].shape[0]
    return parent_change_msgs

def calculate_ack_rate(df):
    sent_packets = df[df['message'].str.contains('Sending ICMPv6 packet')].shape[0]
    ack_packets = df[df['message'].str.contains('received a unicast-DIO')].shape[0]
    return ack_packets / sent_packets if sent_packets > 0 else 0

def calculate_rdc(df):
    energest_df = df[df['message'].str.contains('Period summary')]
    rdc_sum = 0
    for index, row in energest_df.iterrows():
        match = re.search(r'Radio total\s*:\s*(\d+)/\s*(\d+)', row['message'])
        if match:
            radio_active_time = int(match.group(1))
            total_time = int(match.group(2))
            rdc_sum += (radio_active_time / total_time) if total_time > 0 else 0
    return rdc_sum / energest_df.shape[0] if energest_df.shape[0] > 0 else 0

def visualize_metrics(metrics_df, output_image_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    metrics_df['PDR'].plot(kind='bar', ax=axes[0, 0], title='End-to-end Packet Delivery Ratio (PDR)')
    metrics_df['Parent Changes'].plot(kind='bar', ax=axes[0, 1], title='Number of Routing Parent Changes')
    metrics_df['Ack Rate'].plot(kind='bar', ax=axes[1, 0], title='Packet Acknowledgement Rate')
    metrics_df['RDC'].plot(kind='bar', ax=axes[1, 1], title='Radio Duty Cycle (RDC)')
    
    for ax in axes.flat:
        ax.set_xlabel('Node ID')
        ax.set_ylabel('Value')
        ax.set_xticklabels(metrics_df.index, rotation=0)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.suptitle('Metrics per Node', fontsize=16)
    plt.subplots_adjust(top=0.92)
    plt.savefig(output_image_path)
    plt.show()

def save_metrics_summary(metrics_df, output_summary_path):
    with open(output_summary_path, 'w') as f:
        f.write("Metrics extracted from the log file:\n")
        f.write(metrics_df.to_string())

def main(file_path):
    df = parse_log_file(file_path)
    print("Parsed log data:")
    print(df.head())
    
    metrics_df = calculate_metrics(df)
    print("\nMetrics extracted from the log file:")
    print(metrics_df)
    
    log_dir = '/'.join(file_path.split('/')[:-1])
    output_image_path = f"{log_dir}/metrics_visualization.png"
    output_summary_path = f"{log_dir}/metrics_summary.txt"
    
    print("\nGenerating visualization and saving output...")
    visualize_metrics(metrics_df, output_image_path)
    save_metrics_summary(metrics_df, output_summary_path)
    print(f"Visualization saved to {output_image_path}")
    print(f"Summary saved to {output_summary_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 metrics_visualization_script.py path/to/file")
        sys.exit(1)
    file_path = sys.argv[1]
    main(file_path)
