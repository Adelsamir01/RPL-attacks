import sys
import matplotlib.pyplot as plt
import pandas as pd
import re
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

def generate_summary(df):
    summary = df.groupby(['id', 'source']).size().reset_index(name='count')
    return summary

def visualize_data(df):
    summary = generate_summary(df)
    summary_pivot = summary.pivot(index='id', columns='source', values='count').fillna(0)

    summary_pivot.plot(kind='bar', stacked=True, figsize=(12, 8))
    plt.title('Log Messages by Node and Source')
    plt.xlabel('Node ID')
    plt.ylabel('Message Count')
    plt.legend(title='Source')
    plt.tight_layout()
    plt.show()

def main(file_path):
    df = parse_log_file(file_path)
    print("Parsed log data:")
    print(df.head())
    
    print("\nSummary of log data:")
    summary = generate_summary(df)
    print(summary)

    print("\nGenerating visualization...")
    visualize_data(df)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 script.py path/to/file")
        sys.exit(1)
    file_path = sys.argv[1]
    main(file_path)
