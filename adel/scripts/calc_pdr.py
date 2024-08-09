import sys

def parse_log_file(filename):
    nodes_sent = {}
    nodes_received = {}
    active_sequences = {}

    with open(filename, 'r') as file:
        for line in file:
            # Debugging print
            print(f"Processing line: {line.strip()}")

            # Find and parse the timestamp
            timestamp_end = line.find('ID:')
            timestamp = float(line[:timestamp_end].strip())

            # Find and parse the node ID
            node_id_start = line.find('ID:') + 3
            node_id_end = line.find('[', node_id_start)
            node_id = int(line[node_id_start:node_id_end].strip())

            # Find and parse the info type
            info_type_start = line.find('[', node_id_end) + 1
            info_type_end = line.find(']', info_type_start)
            info_type = line[info_type_start:info_type_end].strip()

            # Extract the message
            message = line[info_type_end + 1:].strip()

            # Debugging print
            print(f"Parsed - Timestamp: {timestamp}, Node ID: {node_id}, Info Type: {info_type}, Message: {message}")

            if info_type == "INFO: TSCH" and "send packet" in message:
                seqno_start = message.find('seqno') + 6
                if seqno_start > 5:  # Ensure 'seqno' was found
                    seqno_end = message.find(',', seqno_start)
                    seqno = int(message[seqno_start:seqno_end].strip())
                    
                    if node_id not in active_sequences:
                        active_sequences[node_id] = set()
                    
                    if seqno not in active_sequences[node_id]:
                        if node_id not in nodes_sent:
                            nodes_sent[node_id] = 0
                        nodes_sent[node_id] += 1
                        active_sequences[node_id].add(seqno)

                        # Debugging print
                        print(f"Node {node_id} sent packet with seqno {seqno}. Total sent: {nodes_sent[node_id]}")

            if info_type == "INFO: TSCH" and "received from" in message and node_id == 1:
                seqno_start = message.find('seqno') + 6
                if seqno_start > 5:  # Ensure 'seqno' was found
                    seqno_end = message.find(',', seqno_start)
                    seqno = int(message[seqno_start:seqno_end].strip())

                    source_id_start = message.find('from LL-') + 8
                    source_id_end = message.find(' with seqno')
                    source_id = int(message[source_id_start:source_id_end].strip())

                    if source_id in active_sequences and seqno in active_sequences[source_id]:
                        if source_id not in nodes_received:
                            nodes_received[source_id] = 0
                        nodes_received[source_id] += 1
                        active_sequences[source_id].remove(seqno)

                        # Debugging print
                        print(f"Root node received packet with seqno {seqno} from Node {source_id}. Total received from Node {source_id}: {nodes_received[source_id]}")

    return nodes_sent, nodes_received

def calculate_pdr(nodes_sent, nodes_received):
    pdr = {}
    for node in nodes_sent:
        if node != 1:
            sent = nodes_sent.get(node, 0)
            received = nodes_received.get(node, 0)
            if sent > 0:
                pdr[node] = (received / sent) * 100
            else:
                pdr[node] = 0.0

            # Debugging print
            print(f"Node {node} - Sent: {sent}, Received: {received}, PDR: {pdr[node]:.2f}%")
    return pdr

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 script.py <logfile>")
        return

    logfile = sys.argv[1]
    nodes_sent, nodes_received = parse_log_file(logfile)

    # Debugging information
    print(f"Nodes sent: {nodes_sent}")
    print(f"Nodes received: {nodes_received}")

    pdr = calculate_pdr(nodes_sent, nodes_received)

    for node, ratio in sorted(pdr.items()):
        print(f"Node {node} PDR: {ratio:.2f}%")

if __name__ == "__main__":
    main()
