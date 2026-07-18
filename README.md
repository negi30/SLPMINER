# SLPMiner – Sequential Pattern Mining with Length Decreasing Support Constraint (LDSC)

## Overview

SLPMiner is a Python implementation of a **PrefixSpan-inspired sequential pattern mining** algorithm that introduces a **Length Decreasing Support Constraint (LDSC)**. Unlike traditional approaches that use a fixed minimum support for all pattern lengths, SLPMiner dynamically lowers the support threshold as pattern length increases, enabling the discovery of longer and more informative sequential patterns.

The project automatically downloads benchmark datasets from the SPMF repository, mines sequential patterns using both **fixed support** and **LDSC**, and visualizes the results through comparative graphs.

---

## Features

* PrefixSpan-inspired recursive sequential pattern mining
* Dynamic Length Decreasing Support Constraint (LDSC)
* Automatic SPMF dataset download
* Comparison with traditional fixed-support mining
* Six Matplotlib visualizations for performance analysis

---

## Installation

```bash
git clone https://github.com/negi30/SLPMiner.git
cd SLPMiner

pip install -r requirements.txt
```

**requirements.txt**

```text
matplotlib
requests
```

---

## Usage

Run the script:

```bash
python slpminer.py
```

The program will:

1. Download the **LEVIATHAN** dataset (if not already present).
2. Parse the dataset.
3. Mine sequential patterns using:

   * Fixed Support
   * SLPMiner (LDSC)
4. Generate comparison graphs.

---

## Parameters

```python
BASE_SUPPORT = 500
DECAY_RATE = 40
MIN_FLOOR = 50
```

The LDSC threshold is computed as:

[
\text{Support}(L)=\max(\text{BaseSupport}-(L-1)\times\text{DecayRate},\ \text{MinFloor})
]

---

## Project Structure

```
SLPMiner/
│── slpminer.py
│── README.md
│── requirements.txt
│── project.pdf
└── LEVIATHAN.txt (downloaded automatically)

