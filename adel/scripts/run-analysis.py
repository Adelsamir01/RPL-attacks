#!/usr/bin/env python3

import os
import sys
import time
import matplotlib.pyplot as pl
import re

###########################################

# If set to true, all nodes are plotted, even those with no valid data
PLOT_ALL_NODES = True

###########################################

LOG_FILE = 'DFA52021_log.txt'

COORDINATOR_ID = 1

# for charge calculations
CC2650_MHZ = 48
CC2650_RADIO_TX_CURRENT_MA = 9.100  # at 5 dBm, from CC2650 datasheet
CC2650_RADIO_RX_CURRENT_MA = 5.900  # from CC2650 datasheet
CC2650_RADIO_CPU_ON_CURRENT = 0.061 * CC2650_MHZ  # from CC2650 datasheet
CC2650_RADIO_CPU_SLEEP_CURRENT = 1.335  # empirical
CC2650_RADIO_CPU_DEEP_SLEEP_CURRENT = 0.010  # empirical

###########################################

# for testbed: mapping between the node ID (Contiki_NG) and device ID (testbed)
node_id_to_device_id = {}

###########################################

class NodeStats:
    def __init__(self, id):
        self.id = id

        # intermediate metrics
        self.is_valid = False
        self.is_tsch_joined = False
        self.tsch_join_time_sec = None
        self.rpl_join_time_sec = None
        self.tsch_time_source = None
        self.rpl_parent = None
        self.max_seqnum_sent = 0
        self.seqnums_received_on_root = set()
        self.parent_packets_tx = 0
        self.parent_packets_ack = 0
        self.parent_packets_queue_dropped = 0
        self.energest_cpu_on = 0
        self.energest_cpu_sleep = 0
        self.energest_cpu_deep_sleep = 0
        self.energest_radio_tx = 0
        self.energest_radio_rx = 0
        self.energest_radio_rx_joined = 0
        self.energest_total = 0
        self.energest_total_joined = 0
        self.energest_ticks_per_second = 1
        self.energest_joined = False
        self.energest_period_seconds = 60

        # final metrics (uninitialized)
        self.pdr = 0.0
        self.rpl_parent_changes = 0
        self.par = 0.0
        self.rdc = None
        self.rdc_joined = None
        self.charge = None

    # calculate the final metrics
    def calc(self):
        if self.energest_total:
            radio_on = self.energest_radio_tx + self.energest_radio_rx
            self.rdc = 100.0 * radio_on / self.energest_total

            cpu_on_sec = self.energest_cpu_on / self.energest_ticks_per_second
            cpu_sleep_sec = self.energest_cpu_sleep / self.energest_ticks_per_second
            cpu_deep_sleep_sec = self.energest_cpu_deep_sleep / self.energest_ticks_per_second
            radio_tx_sec = self.energest_radio_tx / self.energest_ticks_per_second
            radio_rx_sec = self.energest_radio_rx / self.energest_ticks_per_second

            self.charge = CC2650_RADIO_TX_CURRENT_MA * radio_tx_sec \
                + CC2650_RADIO_RX_CURRENT_MA * radio_rx_sec \
                + CC2650_RADIO_CPU_ON_CURRENT * cpu_on_sec \
                + CC2650_RADIO_CPU_SLEEP_CURRENT * cpu_sleep_sec \
                + CC2650_RADIO_CPU_DEEP_SLEEP_CURRENT * cpu_deep_sleep_sec

        else:
            print("warning: no energest results for {}".format(self.id))
            self.rdc = 0.0
            self.charge = 0.0

        if self.energest_total_joined:
            radio_on_joined = self.energest_radio_tx + self.energest_radio_rx_joined
            self.rdc_joined = 100.0 * radio_on_joined / self.energest_total_joined
        else:
            self.rdc_joined = 0

        if self.tsch_join_time_sec is None:
            print("node {} never associated TSCH".format(self.id))
            return 0, 0, 0, 0, 0

        if self.rpl_join_time_sec is None:
            print("node {} never joined RPL DAG".format(self.id))
            return 0, 0, 0, 0, 0

        if self.max_seqnum_sent == 0:
            print("node {} never sent any data packets".format(self.id))
            return 0, 0, 0, 0, 0

        self.is_valid = True

        if self.parent_packets_tx:
            self.par = 100.0 * self.parent_packets_ack / self.parent_packets_tx
        else:
            self.par = 0.0

        expected = self.max_seqnum_sent
        actual = len(self.seqnums_received_on_root)
        if expected:
            self.pdr = 100.0 * actual / expected
        else:
            self.pdr = 0.0

        return self.parent_packets_tx, \
            self.parent_packets_ack, \
            self.parent_packets_queue_dropped, \
            self.max_seqnum_sent, \
            len(self.seqnums_received_on_root)

###########################################

def extract_macaddr(s):
    if "NULL" in s:
        return None
    return s

def extract_ipaddr(s):
    if "NULL" in s:
        return None
    return s

def extract_ipaddr_pair(fields):
    s = " ".join(fields)
    fields = s.split(" -> ")
    if len(fields) < 2:
        print(f"Warning: unexpected IP address pair format: {fields}")
        return None, None
    return extract_ipaddr(fields[0]), extract_ipaddr(fields[1])

def addr_to_id(addr):
    return int(addr.split(":")[-1], 16)

###########################################
# Parse a log file

def parse_log_line(line):
    match = re.match(r'(\d+\.\d+)\s+ID:(\d+)\s+\[(\w+):\s+(\w+)\s*\]\s+(.*)', line)
    if match:
        timestamp, node_id, log_level, module, message = match.groups()
        return {
            'timestamp': float(timestamp),
            'node_id': int(node_id),
            'log_level': log_level,
            'module': module,
            'message': message
        }
    else:
        print(f"Warning: Failed to parse line: {line}")
        return None

def analyze_results(filename):
    nodes = {}
    start_ts_unix = None

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            entry = parse_log_line(line)
            if entry:
                ts = entry['timestamp']
                node = entry['node_id']
                message = entry['message']

                if node not in nodes:
                    nodes[node] = NodeStats(node)

                if "association done" in message:
                    if nodes[node].tsch_join_time_sec is None:
                        nodes[node].tsch_join_time_sec = ts / 1000
                    nodes[node].is_tsch_joined = True
                    continue

                if "leaving the network" in message:
                    nodes[node].is_tsch_joined = False
                    nodes[node].energest_joined = False
                    continue

                if "update time source" in message:
                    nodes[node].tsch_time_source = extract_macaddr(message.split(" -> ")[1])
                    continue

                if "rpl_set_preferred_parent" in message:
                    nodes[node].rpl_parent_changes += 1
                    nodes[node].rpl_parent = extract_ipaddr(message.split("used to be ")[1])
                    if nodes[node].rpl_join_time_sec is None:
                        nodes[node].rpl_join_time_sec = ts / 1000
                    continue

                if "parent switch: " in message:
                    nodes[node].rpl_parent_changes += 1
                    old_parent, new_parent = extract_ipaddr_pair(message.split()[3:])
                    nodes[node].rpl_parent = new_parent
                    if nodes[node].rpl_join_time_sec is None:
                        nodes[node].rpl_join_time_sec = ts / 1000
                    continue

                if "app generate packet" in message:
                    seqnum = int(message.split("seqnum=")[1])
                    nodes[node].max_seqnum_sent = max(nodes[node].max_seqnum_sent, seqnum)
                    continue

                if "app receive packet" in message:
                    seqnum = int(message.split("seqnum=")[1])
                    fromaddr = message.split("from=")[1]
                    from_node = addr_to_id(fromaddr)
                    if from_node not in nodes:
                        nodes[from_node] = NodeStats(from_node)
                    nodes[from_node].seqnums_received_on_root.add(seqnum)
                    continue

                if "num packets" in message:
                    parts = message.split()
                    tx = int(parts[2].split("=")[1])
                    ack = int(parts[3].split("=")[1])
                    queue_drops = int(parts[4].split("=")[1])
                    to_addr = parts[5].split("=")[1]
                    if nodes[node].tsch_time_source == to_addr:
                        nodes[node].parent_packets_tx += tx
                        nodes[node].parent_packets_ack += ack
                        nodes[node].parent_packets_queue_dropped += queue_drops
                    continue

                if "INFO: Energest" in message:
                    if "Period" in message:
                        nodes[node].energest_period_seconds = int(message.split()[2])
                    elif "Total time" in message:
                        total = int(message.split()[3])
                        nodes[node].energest_total += total
                        nodes[node].energest_ticks_per_second = total / nodes[node].energest_period_seconds
                        if nodes[node].energest_joined:
                            nodes[node].energest_total_joined += total
                    else:
                        ticks = int(message.split()[3])
                        if "CPU" in message:
                            nodes[node].energest_cpu_on += ticks
                        elif "Deep LPM" in message:
                            nodes[node].energest_cpu_sleep += ticks
                        elif "LPM" in message:
                            nodes[node].energest_cpu_deep_sleep += ticks
                        elif "Radio Tx" in message:
                            nodes[node].energest_radio_tx += ticks
                        elif "Radio Rx" in message:
                            nodes[node].energest_radio_rx += ticks
                            if nodes[node].energest_joined:
                                nodes[node].energest_radio_rx_joined += ticks
                            nodes[node].energest_joined = nodes[node].is_tsch_joined
                    continue

    print(f"Total nodes parsed: {len(nodes)}")
    r = []
    total_ll_sent = 0
    total_ll_acked = 0
    total_ll_queue_dropped = 0
    total_e2e_sent = 0
    total_e2e_received = 0
    for k in sorted(nodes.keys()):
        n = nodes[k]
        if n.id == COORDINATOR_ID:
            continue
        ll_sent, ll_acked, ll_queue_dropped, e2e_sent, e2e_received = n.calc()
        print(f"Node {n.id}: ll_sent={ll_sent}, ll_acked={ll_acked}, ll_queue_dropped={ll_queue_dropped}, e2e_sent={e2e_sent}, e2e_received={e2e_received}")
        if n.is_valid or PLOT_ALL_NODES:
            d = {
                "id": n.id,
                "pdr": n.pdr,
                "par": n.par,
                "rpl_switches": n.rpl_parent_changes,
                "duty_cycle": n.rdc,
                "duty_cycle_joined": n.rdc_joined,
                "charge": n.charge
            }
            r.append(d)
            total_ll_sent += ll_sent
            total_ll_acked += ll_acked
            total_ll_queue_dropped += ll_queue_dropped
            total_e2e_sent += e2e_sent
            total_e2e_received += e2e_received
    ll_par = 100.0 * total_ll_acked / total_ll_sent if total_ll_sent else 0.0
    e2e_pdr = 100.0 * total_e2e_received / total_e2e_sent if total_e2e_sent else 0.0
    return r, ll_par, total_ll_queue_dropped, e2e_pdr

#######################################################
# Plot the results of a given metric as a bar chart

def plot(results, metric, ylabel):
    if not results:
        print(f"No results to plot for {metric}")
        return
    
    pl.figure(figsize=(5, 4))

    data = [r[metric] for r in results]
    x = range(len(data))
    barlist = pl.bar(x, data, width=0.4)

    for b in barlist:
        b.set_color("orange")
        b.set_edgecolor("black")
        b.set_linewidth(1)

    ids = [r["id"] for r in results]
    pl.xticks(x, [str(u) for u in ids], rotation=90)
    pl.xlabel("Node ID")
    pl.ylabel(ylabel)

    if metric == "pdr":
        miny = min(80, min(data))
        pl.ylim([miny, 100])
    else:
        pl.ylim(ymin=0)

    pl.savefig("plot_{}.pdf".format(metric), format="pdf", bbox_inches='tight')
    pl.close()

#######################################################
# Run the application

def main():
    input_file = LOG_FILE
    if len(sys.argv) > 1:
        # change from the default
        input_file = sys.argv[1]

    if not os.access(input_file, os.R_OK):
        print('The input file "{}" does not exist'.format(input_file))
        exit(-1)

    results, ll_par, ll_queue_dropped, e2e_pdr = analyze_results(input_file)

    print("Link-layer PAR={:.2f} ({} packets queue dropped) End-to-end PDR={:.2f}".format(
        ll_par, ll_queue_dropped, e2e_pdr))

    plot(results, "pdr", "Packet Delivery Ratio, %")
    plot(results, "par", "Packet Acknowledgement Ratio, %")
    plot(results, "rpl_switches", "RPL parent switches")
    plot(results, "duty_cycle", "Radio Duty Cycle, %")
    plot(results, "duty_cycle_joined", "Joined Radio Duty Cycle, %")
    plot(results, "charge", "Charge consumption, mC")

#######################################################

if __name__ == '__main__':
    main()

