"""Replay complete PGNs and estimate logistic Elo with opening-pair uncertainty."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics

import chess.pgn
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/chromatique-v4"


def elo(score):
    if score <= 0:
        return "-inf"
    if score >= 1:
        return "+inf"
    return 400 * math.log10(score / (1 - score))


def paired_stats(pairs):
    n = len(pairs)
    if n < 2 or any(x not in (0, 0.25, 0.5, 0.75, 1) for x in pairs):
        raise ValueError("Need at least two legal opening-pair scores")
    score = statistics.mean(pairs)
    variance = statistics.variance(pairs)
    se = math.sqrt(variance / n)
    h = math.sqrt(math.log(2 / 0.05) / (2 * n))
    hoeffding = [max(0, score - h), min(1, score + h)]
    normal = [max(0, score - 1.959963984540054 * se), min(1, score + 1.959963984540054 * se)]
    method = "pair_mean_normal_unbiased_variance"
    if variance == 0:
        normal, method = hoeffding, "hoeffding_degenerate_fallback"
    penta = [pairs.count(x) for x in (0, 0.25, 0.5, 0.75, 1)]
    samples = np.random.default_rng(20261020).multinomial(n, np.array(penta) / n, size=20000)
    bootstrap = np.quantile((samples @ np.arange(5)) / (4 * n), [0.025, 0.975]).tolist()
    if variance == 0:
        bootstrap = None  # Empirical resampling cannot identify unseen pair outcomes.
    return {"opening_pairs": n, "games": 2 * n, "pentanomial": penta,
            "score": score, "pair_variance": variance, "score_se": se,
            "elo_difference": elo(score), "normal95_score": normal,
            "normal95_elo": [elo(s) for s in normal], "interval_method": method,
            "bootstrap95_score": bootstrap, "bootstrap95_elo": [elo(s) for s in bootstrap] if bootstrap else None,
            "bootstrap_resamples": 20000, "bootstrap_seed": 20261020,
            "hoeffding95_score": hoeffding, "hoeffding95_elo": [elo(s) for s in hoeffding]}


def read_openings(path, count):
    result = []
    with path.open() as stream:
        while (game := chess.pgn.read_game(stream)) is not None:
            if game.errors:
                raise ValueError(game.errors)
            result.append(tuple(m.uci() for m in game.mainline_moves()))
    if count > len(result) or len(set(result)) != len(result):
        raise ValueError("Invalid opening panel/count")
    return result[:count]


def validate_games(stream, target, openings, book_plies=16, tc=None):
    expected = set(openings)
    if len(expected) != len(openings):
        raise ValueError("Duplicate expected openings")
    groups = defaultdict(list)
    wdl = [0, 0, 0]
    colors = {"white": [0, 0, 0], "black": [0, 0, 0]}
    terminations = Counter()
    opponents = set()
    lengths = []
    for game in iter(lambda: chess.pgn.read_game(stream), None):
        if game.errors:
            raise ValueError(f"PGN parse/legality errors: {game.errors}")
        if game.board().fen() != chess.STARTING_FEN:
            raise ValueError("Unexpected PGN initial position")
        if tc is not None and game.headers.get("TimeControl") != tc:
            raise ValueError("PGN time control disagrees with schedule")
        result = game.headers.get("Result")
        if result not in ("1-0", "0-1", "1/2-1/2"):
            raise ValueError("Unfinished game in PGN")
        white, black = game.headers["White"], game.headers["Black"]
        if (white == target) + (black == target) != 1:
            raise ValueError("Unexpected target/color identity")
        color = "white" if white == target else "black"
        opponents.add(black if color == "white" else white)
        moves = tuple(m.uci() for m in game.mainline_moves())
        opening = moves[:book_plies]
        if opening not in expected:
            raise ValueError("Unexpected or incomplete opening history")
        terminal = game.end().board().outcome(claim_draw=True)
        termination = game.headers.get("Termination", "missing")
        if termination == "normal" and (terminal is None or terminal.result() != result):
            raise ValueError("Normal game result disagrees with replayed rules")
        score_white = {"1-0": 1, "0-1": 0, "1/2-1/2": 0.5}[result]
        score = score_white if color == "white" else 1 - score_white
        index = {1: 0, 0.5: 1, 0: 2}[score]
        wdl[index] += 1
        colors[color][index] += 1
        groups[opening].append((color, score))
        terminations[termination] += 1
        lengths.append(len(moves) / 2)
    if len(opponents) != 1:
        raise ValueError("Expected exactly one opponent")
    pairs = []
    for opening in openings:
        games = groups[opening]
        if len(games) != 2:
            raise ValueError("Missing or duplicate opening pair")
        if {color for color, _ in games} != {"white", "black"}:
            raise ValueError("Opening pair did not reverse colors")
        pairs.append(sum(score for _, score in games) / 2)
    return {"wdl": wdl, "colors_wdl": colors, "pairs": pairs,
            "opponent": next(iter(opponents)), "terminations": dict(terminations),
            "mean_game_moves": statistics.mean(lengths), "max_game_moves": max(lengths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schedule", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, default=BASE / "results")
    args = parser.parse_args()
    rows = []
    for spec in json.loads(args.schedule.read_text())["matches"]:
        prefix = args.results_dir / spec["id"]
        receipt = json.loads(prefix.with_suffix(".run.json").read_text())
        pgn = prefix.with_suffix(".pgn")
        if receipt.get("returncode") != 0 or receipt["spec"] != spec:
            raise ValueError(f"Run not successfully complete: {spec['id']}")
        if hashlib.sha256(pgn.read_bytes()).hexdigest() != receipt["pgn_sha256"]:
            raise ValueError("PGN checksum changed")
        book = BASE / "data" / (spec["panel"] + "-openings.pgn")
        if hashlib.sha256(book.read_bytes()).hexdigest() != receipt["inputs_sha256"]["opening_book"]:
            raise ValueError("Opening checksum changed")
        openings = read_openings(book, spec["pairs"])
        target = spec["engines"][0]["name"]
        with pgn.open() as stream:
            row = validate_games(stream, target, openings, tc=spec["tc"])
        if row["opponent"] != spec["engines"][1]["name"]:
            raise ValueError("Unexpected opponent")
        row.update(paired_stats(row.pop("pairs")))
        row.update(id=spec["id"], target=target, tc=spec["tc"], panel=spec["panel"],
                   pgn_sha256=receipt["pgn_sha256"], validation="complete_legal_replay_and_exact_opening_pairs")
        rows.append(row)
        print(f"{spec['id']}: WDL={row['wdl']}, score={row['score']:.4f}, delta={row['elo_difference']}, 95%={row['normal95_elo']}")
    args.output.write_text(json.dumps({"matches": rows}, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
