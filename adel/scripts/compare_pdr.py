import sys
import matplotlib.pyplot as plt

def parse_log_file(file_path):
    packets_sent = {}
    packets_received = {}
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if 'Packet sent to' in line:
                    print(f"Parsing sent packet line: {line.strip()}")
                    node_id = int(line.split('ID:')[1].split()[0])
                    packets_sent[node_id] = packets_sent.get(node_id, 0) + 1
                elif 'Packet received from' in line:
                    print(f"Parsing received packet line: {line.strip()}")
                    node_id = int(line.split('ID:')[1].split()[0])
                    packets_received[node_id] = packets_received.get(node_id, 0) + 1
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)

    return packets_sent, packets_received

def calculate_pdr(packets_sent, packets_received):
    pdr = {}
    for node in packets_sent:
        sent = packets_sent.get(node, 0)
        received = packets_received.get(node, 0)
        if sent > 0:
            pdr[node] = (received / sent) * 100
        else:
            pdr[node] = 0
    return pdr

def plot_pdr(normal_pdr, attack_pdr, normal_filename, attack_filename):
    nodes = sorted(set(normal_pdr.keys()).union(set(attack_pdr.keys())))
    normal_values = [normal_pdr.get(node, 0) for node in nodes]
    attack_values = [attack_pdr.get(node, 0) for node in nodes]

    print(f"Nodes: {nodes}")
    print(f"Normal PDR Values: {normal_values}")
    print(f"Attack PDR Values: {attack_values}")

    if not nodes:
        print("No valid nodes found in the log files.")
        return

    plt.figure(figsize=(10, 6))
    bar_width = 0.35
    index = range(len(nodes))

    plt.bar(index, normal_values, bar_width, label=f'Normal ({normal_filename})')
    plt.bar([i + bar_width for i in index], attack_values, bar_width, label=f'Attack ({attack_filename})')

    plt.xlabel('Node')
    plt.ylabel('PDR (%)')
    plt.title('End-to-End Packet Delivery Ratio (PDR) Comparison')
    plt.xticks([i + bar_width / 2 for i in index], nodes)
    plt.legend()

    plt.tight_layout()
    plt.show()

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 script.py logfile1 logfile2")
        sys.exit(1)

    normal_log = sys.argv[1]
    attack_log = sys.argv[2]

    normal_packets_sent, normal_packets_received = parse_log_file(normal_log)
    attack_packets_sent, attack_packets_received = parse_log_file(attack_log)

    normal_pdr = calculate_pdr(normal_packets_sent, normal_packets_received)
    attack_pdr = calculate_pdr(attack_packets_sent, attack_packets_received)

    plot_pdr(normal_pdr, attack_pdr, normal_log, attack_log)

if __name__ == "__main__":
    main()
