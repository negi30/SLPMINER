import requests
import os
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

# --- 1. DOWNLOADER (Bypasses SPMF Server Blocks) ---
def download_spmf_dataset(filename):
    """Downloads the dataset using the correct public path and a browser User-Agent."""
    url = f"https://www.philippe-fournier-viger.com/spmf/publicdatasets/{filename.upper()}"

    if not os.path.exists(filename):
        print(f"Downloading '{filename}' from SPMF...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers)
            if b"<!DOCTYPE" in response.content[:20] or b"<html" in response.content[:20].lower():
                 print("Error: The server returned a webpage instead of data. Check the filename spelling.")
                 return False

            response.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(response.content)
            print("Download complete!\n")
        except Exception as e:
            print(f"Failed to download. Error: {e}")
            return False
    return True

# --- 2. DATA PARSER ---
def load_spmf_dataset(filepath, max_sequences=None):
    """Parses the SPMF text format into Python lists."""
    database = []
    with open(filepath, 'r') as file:
        for i, line in enumerate(file):
            if max_sequences and i >= max_sequences:
                break
            tokens = line.strip().split()
            sequence = []
            for token in tokens:
                if token == '-1':
                    continue
                elif token == '-2':
                    break
                else:
                    sequence.append(token)
            if sequence:
                database.append(sequence)
    return database

# --- 3. SLPMINER (LDSC) ALGORITHM ---
def slp_threshold(length, base_support, decay_rate, min_floor):
    """Calculates the dropping support threshold based on pattern length."""
    required_supp = base_support - ((length - 1) * decay_rate)
    return max(required_supp, min_floor)

def project_database(db, item):
    """Creates a projected database for PrefixSpan search."""
    projected_db = []
    for seq in db:
        if item in seq:
            idx = seq.index(item)
            if idx + 1 < len(seq):
                projected_db.append(seq[idx+1:])
    return projected_db

def mine_slp_patterns(db, prefix, current_length, base_support, decay_rate, min_floor, results):
    """Recursively finds patterns using the dynamic threshold."""
    required_supp = slp_threshold(current_length, base_support, decay_rate, min_floor)

    item_counts = defaultdict(int)
    for seq in db:
        for item in set(seq):
            item_counts[item] += 1

    for item, count in item_counts.items():
        if count >= required_supp:
            new_prefix = prefix + [item]
            results.append({
                'pattern': new_prefix,
                'length': current_length,
                'frequency': count,
                'required_support': required_supp
            })

            projected_db = project_database(db, item)
            if projected_db:
                mine_slp_patterns(
                    projected_db, new_prefix, current_length + 1,
                    base_support, decay_rate, min_floor, results
                )

# --- 4. EXECUTION & GRAPHING ---
def run_experiments_and_plot():
    dataset_filename = 'LEVIATHAN.txt'
    if os.path.exists(dataset_filename) and os.path.getsize(dataset_filename) < 2000:
        os.remove(dataset_filename)

    if not download_spmf_dataset(dataset_filename):
        return

    database = load_spmf_dataset(dataset_filename, max_sequences=9000)
    print(f"Total Sequences Loaded: {len(database)}")

    BASE_SUPPORT = 500
    DECAY_RATE = 40
    MIN_FLOOR = 50

    # --- EXPERIMENT 1: FIXED VS SLPMINER (LDSC) ---
    print("Mining with Fixed Support (Decay = 0)...")
    fixed_patterns = []
    mine_slp_patterns(database, [], 1, BASE_SUPPORT, 0, BASE_SUPPORT, fixed_patterns)

    print(f"Mining with SLPMiner / LDSC (Decay = {DECAY_RATE})...")
    slp_patterns = []
    mine_slp_patterns(database, [], 1, BASE_SUPPORT, DECAY_RATE, MIN_FLOOR, slp_patterns)

    # --- EXPERIMENT 2: EFFECT OF DIFFERENT DECAY RATES ---
    print("Testing various decay rates for comparison...")
    decay_rates_to_test = [0, 10, 20, 30, 40, 50, 60]
    decay_counts = []
    decay_max_lengths = []

    for dr in decay_rates_to_test:
        temp_patterns = []
        mine_slp_patterns(database, [], 1, BASE_SUPPORT, dr, MIN_FLOOR, temp_patterns)
        decay_counts.append(len(temp_patterns))
        max_l = max([p['length'] for p in temp_patterns]) if temp_patterns else 0
        decay_max_lengths.append(max_l)

    print("Generating graphs...")

    # --- 5. MATPLOTLIB DASHBOARD ---
    fig = plt.figure(figsize=(15, 16))
    fig.suptitle(f"Algorithm Comparison on {dataset_filename} (Base Supp={BASE_SUPPORT})", fontsize=16)

    # Setup Custom Grid (3 rows, 2 columns)
    ax1 = plt.subplot2grid((3, 2), (0, 0))
    ax2 = plt.subplot2grid((3, 2), (0, 1))
    ax3 = plt.subplot2grid((3, 2), (1, 0))
    ax4 = plt.subplot2grid((3, 2), (1, 1))
    ax5 = plt.subplot2grid((3, 2), (2, 0)) # Bar Graph
    ax6 = plt.subplot2grid((3, 2), (2, 1)) # Line Graph Trend

    # GRAPH 1: Fixed Support Scatter
    len_fixed = [p['length'] for p in fixed_patterns]
    freq_fixed = [p['frequency'] for p in fixed_patterns]
    max_len_fixed = max(len_fixed) if len_fixed else 1
    x_fixed = list(range(1, max_len_fixed + 2))

    ax1.step(x_fixed, [BASE_SUPPORT]*len(x_fixed), where='post', color='red', linestyle='--', label='Fixed Threshold')
    ax1.scatter(len_fixed, freq_fixed, color='gray', alpha=0.5, label='Discovered Patterns')
    ax1.set_title("Standard Mining (Fixed Support)")
    ax1.set_xlabel("Pattern Length")
    ax1.set_ylabel("Frequency")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # GRAPH 2: SLPMiner Scatter
    len_slp = [p['length'] for p in slp_patterns]
    freq_slp = [p['frequency'] for p in slp_patterns]
    max_len_slp = max(len_slp) if len_slp else 1
    x_slp = list(range(1, max_len_slp + 2))
    y_slp = [slp_threshold(l, BASE_SUPPORT, DECAY_RATE, MIN_FLOOR) for l in x_slp]

    ax2.step(x_slp, y_slp, where='post', color='red', linestyle='--', label='LDSC Threshold')
    ax2.scatter(len_slp, freq_slp, color='blue', alpha=0.5, label='Discovered Patterns')
    ax2.set_title(f"SLPMiner / LDSC (Decay={DECAY_RATE})")
    ax2.set_xlabel("Pattern Length")
    ax2.set_ylabel("Frequency")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # GRAPH 3: Threshold Curves for Different Decays
    ax3.set_title("Support Threshold Drop-off Curves")
    test_lengths = list(range(1, max(max_len_slp, 8) + 2))
    for dr in [0, 20, 40, 60]:
        y_vals = [slp_threshold(l, BASE_SUPPORT, dr, MIN_FLOOR) for l in test_lengths]
        ax3.plot(test_lengths, y_vals, marker='.', label=f'Decay = {dr}')
    ax3.set_xlabel("Pattern Length")
    ax3.set_ylabel("Required Support")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    # GRAPH 4: Effect of Decay Rate (Dual Axis)
    ax4_2 = ax4.twinx()
    ax4.plot(decay_rates_to_test, decay_counts, color='purple', marker='o', linewidth=2, label="Total Patterns")
    ax4_2.plot(decay_rates_to_test, decay_max_lengths, color='green', marker='s', linestyle=':', linewidth=2, label="Max Length")

    ax4.set_xlabel("Decay Rate")
    ax4.set_ylabel("Total Patterns Discovered", color='purple')
    ax4_2.set_ylabel("Max Pattern Length", color='green')
    ax4.tick_params(axis='y', labelcolor='purple')
    ax4_2.tick_params(axis='y', labelcolor='green')

    ax4.set_title("Effect of Decay Rate on Output")
    ax4.grid(True, alpha=0.3)

    # --- DATA PREP FOR GRAPHS 5 & 6 ---
    fixed_counts = Counter(len_fixed)
    slp_counts = Counter(len_slp)
    all_lengths = sorted(list(set(fixed_counts.keys()) | set(slp_counts.keys())))
    x_indices = list(range(len(all_lengths)))
    fixed_bar_vals = [fixed_counts.get(l, 0) for l in all_lengths]
    slp_bar_vals = [slp_counts.get(l, 0) for l in all_lengths]

    # GRAPH 5: Pattern Discovery Count per Length (Grouped Bar Chart)
    bar_width = 0.35
    ax5.bar([x - bar_width/2 for x in x_indices], fixed_bar_vals, width=bar_width, label='Fixed Support', color='gray')
    ax5.bar([x + bar_width/2 for x in x_indices], slp_bar_vals, width=bar_width, label='SLPMiner (LDSC)', color='blue')

    ax5.set_xticks(x_indices)
    ax5.set_xticklabels(all_lengths)
    ax5.set_title("Pattern Count per Length (Bar View)")
    ax5.set_xlabel("Pattern Length")
    ax5.set_ylabel("Number of Patterns Found")
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')

    # GRAPH 6: Frequent Patterns vs Pattern Length (Line Trend)
    ax6.plot(x_indices, fixed_bar_vals, marker='o', color='gray', linewidth=2, label='Fixed Support')
    ax6.plot(x_indices, slp_bar_vals, marker='s', color='blue', linewidth=2, label='SLPMiner (LDSC)')

    # Fill under the line slightly for better visualization
    ax6.fill_between(x_indices, slp_bar_vals, color='blue', alpha=0.1)
    ax6.fill_between(x_indices, fixed_bar_vals, color='gray', alpha=0.1)

    ax6.set_xticks(x_indices)
    ax6.set_xticklabels(all_lengths)
    ax6.set_title("Trend: Frequent Patterns vs. Pattern Length")
    ax6.set_xlabel("Pattern Length")
    ax6.set_ylabel("Number of Patterns Found")
    ax6.legend()
    ax6.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.show()

# Trigger the script
if __name__ == "__main__":
    run_experiments_and_plot()
