import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter, defaultdict


def parse_candidates(raw: str):
    candidates = [c.strip() for c in raw.split(",") if c.strip()]
    if len(set(candidates)) != len(candidates):
        raise ValueError("Candidate names must be unique.")
    if not candidates:
        raise ValueError("Please enter at least one candidate.")
    return candidates


def parse_ballots(raw: str, candidates):
    ballots = []
    if not raw.strip():
        raise ValueError("Please enter at least one ballot line.")

    for idx, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"Line {idx} must be in the format 'count: ranking'.")
        count_text, ranking_text = line.split(":", 1)
        try:
            count = int(count_text.strip())
        except ValueError as exc:
            raise ValueError(f"Line {idx} has an invalid count.") from exc
        if count <= 0:
            raise ValueError(f"Line {idx} count must be positive.")

        ranking = [c.strip() for c in ranking_text.replace(">", ",").split(",") if c.strip()]
        if len(set(ranking)) != len(ranking):
            raise ValueError(f"Line {idx} ranking has duplicate candidates.")
        unknown = [c for c in ranking if c not in candidates]
        if unknown:
            raise ValueError(f"Line {idx} contains unknown candidates: {', '.join(unknown)}.")

        ballots.append((count, ranking))

    if not ballots:
        raise ValueError("Please enter at least one valid ballot line.")
    return ballots


def irv_winner(candidates, ballots):
    remaining = list(candidates)
    rounds = []

    while len(remaining) > 1:
        tally = Counter()
        for count, ranking in ballots:
            for choice in ranking:
                if choice in remaining:
                    tally[choice] += count
                    break
        total = sum(tally.values())
        rounds.append((tally, total, list(remaining)))
        if total == 0:
            break
        for candidate, votes in tally.items():
            if votes > total / 2:
                return candidate, rounds
        lowest_votes = min(tally.values()) if tally else 0
        eliminated = [c for c in remaining if tally.get(c, 0) == lowest_votes]
        for candidate in eliminated:
            remaining.remove(candidate)
    return (remaining[0] if remaining else "No winner"), rounds


def borda_winner(candidates, ballots):
    scores = Counter({c: 0 for c in candidates})
    max_points = len(candidates) - 1
    for count, ranking in ballots:
        for idx, candidate in enumerate(ranking):
            scores[candidate] += count * (max_points - idx)
    return scores


def condorcet_winner(candidates, ballots):
    pairwise = defaultdict(lambda: defaultdict(int))
    for count, ranking in ballots:
        for i, winner in enumerate(ranking):
            for loser in ranking[i + 1:]:
                pairwise[winner][loser] += count
    victories = Counter()
    for a in candidates:
        for b in candidates:
            if a == b:
                continue
            if pairwise[a][b] > pairwise[b][a]:
                victories[a] += 1
    winner = None
    for candidate in candidates:
        if victories[candidate] == len(candidates) - 1:
            winner = candidate
            break
    return winner, pairwise, victories


class VotingApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()

    def create_widgets(self):
        header = ttk.Label(
            self,
            text="Ranked Choice Voting Simulator",
            font=("Segoe UI", 16, "bold"),
        )
        header.pack(pady=(10, 5))

        input_frame = ttk.LabelFrame(self, text="Election Setup")
        input_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        ttk.Label(input_frame, text="Candidates (comma-separated):").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.candidates_entry = ttk.Entry(input_frame)
        self.candidates_entry.insert(0, "Alice, Bob, Chen, Diego")
        self.candidates_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(input_frame, text="Ballots (count: ranking per line):").grid(
            row=1, column=0, sticky="nw", padx=5, pady=5
        )
        self.ballots_text = tk.Text(input_frame, height=8, width=50)
        self.ballots_text.insert(
            "1.0",
            "10: Alice > Bob > Chen > Diego\n"
            "8: Bob > Diego > Chen > Alice\n"
            "6: Chen > Alice > Bob > Diego\n"
            "4: Diego > Chen > Alice > Bob",
        )
        self.ballots_text.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        input_frame.columnconfigure(1, weight=1)

        options_frame = ttk.LabelFrame(self, text="Voting Systems")
        options_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        self.irv_var = tk.BooleanVar(value=True)
        self.borda_var = tk.BooleanVar(value=True)
        self.condorcet_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Instant Runoff (IRV)", variable=self.irv_var).pack(
            anchor="w", padx=5, pady=2
        )
        ttk.Checkbutton(options_frame, text="Borda Count", variable=self.borda_var).pack(
            anchor="w", padx=5, pady=2
        )
        ttk.Checkbutton(options_frame, text="Condorcet (pairwise)", variable=self.condorcet_var).pack(
            anchor="w", padx=5, pady=2
        )

        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(action_frame, text="Run Simulation", command=self.run_simulation).pack(
            side=tk.LEFT
        )
        ttk.Button(action_frame, text="Clear Output", command=self.clear_output).pack(
            side=tk.LEFT, padx=5
        )

        self.output = tk.Text(self, height=16)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.output.insert("1.0", "Simulation results will appear here.\n")
        self.output.config(state=tk.DISABLED)

    def clear_output(self):
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)

    def run_simulation(self):
        try:
            candidates = parse_candidates(self.candidates_entry.get())
            ballots = parse_ballots(self.ballots_text.get("1.0", tk.END), candidates)
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        if not (self.irv_var.get() or self.borda_var.get() or self.condorcet_var.get()):
            messagebox.showwarning("No Systems Selected", "Select at least one voting system.")
            return

        report_lines = []
        total_votes = sum(count for count, _ in ballots)
        report_lines.append(f"Total ballots: {total_votes}")
        report_lines.append("")

        if self.irv_var.get():
            winner, rounds = irv_winner(candidates, ballots)
            report_lines.append("Instant Runoff (IRV)")
            for idx, (tally, total, remaining) in enumerate(rounds, start=1):
                report_lines.append(f"  Round {idx} (remaining: {', '.join(remaining)}):")
                for candidate in remaining:
                    report_lines.append(f"    {candidate}: {tally.get(candidate, 0)}")
                report_lines.append(f"    Total counted: {total}")
            report_lines.append(f"  Winner: {winner}")
            report_lines.append("")

        if self.borda_var.get():
            scores = borda_winner(candidates, ballots)
            report_lines.append("Borda Count")
            for candidate, score in scores.most_common():
                report_lines.append(f"  {candidate}: {score} points")
            top_score = scores.most_common(1)[0][0] if scores else "No winner"
            report_lines.append(f"  Winner: {top_score}")
            report_lines.append("")

        if self.condorcet_var.get():
            winner, pairwise, victories = condorcet_winner(candidates, ballots)
            report_lines.append("Condorcet (pairwise)")
            for candidate in candidates:
                report_lines.append(
                    f"  {candidate}: {victories[candidate]} pairwise wins"
                )
            if winner:
                report_lines.append(f"  Condorcet winner: {winner}")
            else:
                report_lines.append("  No Condorcet winner found.")
            report_lines.append("")

        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert("1.0", "\n".join(report_lines))
        self.output.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Voting Outcome Simulator")
    root.geometry("760x680")
    root.minsize(680, 600)
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = VotingApp(root)
    root.mainloop()
