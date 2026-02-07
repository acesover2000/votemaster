# Voting Outcome Simulator

A simple Windows-friendly Python GUI for simulating outcomes across popular ranked choice voting systems.

## Features
- Instant Runoff (IRV)
- Borda Count
- Condorcet pairwise comparison summary

## Usage
```bash
python main.py
```

## Ballot Format
Enter ballots one per line with the format:
```
count: Candidate A > Candidate B > Candidate C
```

Example:
```
10: Alice > Bob > Chen > Diego
8: Bob > Diego > Chen > Alice
```
