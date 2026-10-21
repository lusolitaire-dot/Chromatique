"""Descriptive PGN metrics and a common-position, stronger-judge style probe."""
import argparse
from collections import defaultdict
import csv
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import statistics

import chess
import chess.engine
import chess.pgn
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/chromatique-v4"
VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def material(board, color):
    return sum(value * (len(board.pieces(piece, color)) - len(board.pieces(piece, not color)))
               for piece, value in VALUES.items())


def move_features(board, move):
    if move not in board.legal_moves:
        raise ValueError("Illegal style-probe move")
    color = board.turn
    before = material(board, color)
    check, capture = board.gives_check(move), board.is_capture(move)
    after = board.copy()
    after.push(move)
    concession = 0
    # A proxy only: opponent takes a non-pawn, followed by the best immediate
    # material recapture on that square. It does not prove intent or soundness.
    for reply in list(after.legal_moves):
        victim = after.piece_at(reply.to_square)
        if not after.is_capture(reply) or victim is None or VALUES[victim.piece_type] < 3:
            continue
        reply_board = after.copy()
        reply_board.push(reply)
        best = material(reply_board, color)
        for recapture in list(reply_board.legal_moves):
            if recapture.to_square == reply.to_square and reply_board.is_capture(recapture):
                reply_board.push(recapture)
                best = max(best, material(reply_board, color))
                reply_board.pop()
        concession = max(concession, before - best)
    return {"check": check, "capture": capture, "promotion": bool(move.promotion),
            "quiet": not (check or capture or move.promotion),
            "material_concession_proxy": concession}


def describe(schedule, results_dir):
    rows = []
    for spec in schedule["matches"]:
        if not spec["id"].startswith("main-"):
            continue
        with (results_dir / (spec["id"] + ".pgn")).open() as stream:
            for index, game in enumerate(iter(lambda: chess.pgn.read_game(stream), None), 1):
                if game.errors:
                    raise ValueError(game.errors)
                board = game.board()
                queenless_by40 = False
                counts = {c: defaultdict(int) for c in [chess.WHITE, chess.BLACK]}
                for ply, move in enumerate(game.mainline_moves()):
                    color = board.turn
                    if ply >= 16:
                        counts[color]["moves"] += 1
                        check, capture = board.gives_check(move), board.is_capture(move)
                        counts[color]["checks"] += check
                        counts[color]["captures"] += capture
                        counts[color]["quiet"] += not (check or capture or move.promotion)
                        counts[color]["promotions"] += bool(move.promotion)
                        counts[color]["deficit_ge2_moves"] += material(board, color) <= -2
                    board.push(move)
                    if ply < 80 and not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(chess.QUEEN, chess.BLACK):
                        queenless_by40 = True
                for color in [chess.WHITE, chess.BLACK]:
                    rows.append({"match": spec["id"], "game": index,
                                 "engine": game.headers["White" if color else "Black"],
                                 "color": "white" if color else "black", "result": game.headers["Result"],
                                 "queenless_by40": int(queenless_by40),
                                 "game_moves": board.ply() / 2, **dict(counts[color])})
    fields = ["match", "game", "engine", "color", "result", "game_moves", "moves", "checks", "captures", "quiet", "promotions", "deficit_ge2_moves", "queenless_by40"]
    with (results_dir / "game-style.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, restval=0)
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for match, engine in sorted({(r["match"], r["engine"]) for r in rows}):
        group = [r for r in rows if (r["match"], r["engine"]) == (match, engine)]
        total = sum(r.get("moves", 0) for r in group)
        summary.append({"match": match, "engine": engine, "games": len(group), "moves": total,
                        **{name + "_rate": sum(r.get(name, 0) for r in group) / total
                           for name in fields[7:-1]},
                        "queenless_by40_games": sum(r["queenless_by40"] for r in group),
                        "mean_game_moves": statistics.mean(r["game_moves"] for r in group)})
    (results_dir / "game-style-summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def probe_positions(spec, results_dir):
    groups = defaultdict(list)
    path = results_dir / (spec["id"] + ".pgn")
    with path.open() as stream:
        for index, game in enumerate(iter(lambda: chess.pgn.read_game(stream), None), 1):
            moves = tuple(m.uci() for m in game.mainline_moves())
            groups[moves[:16]].append((index, game))
    positions = []
    excluded = []
    for opening in sorted(groups):
        key = hashlib.sha256(" ".join(opening).encode()).digest()
        chosen_white = bool(key[0] & 1)
        index, game = next((i, g) for i, g in groups[opening]
                           if (g.headers["White"] == "Chromatique-v4") == chosen_white)
        moves = list(game.mainline_moves())
        candidates = [24, 32, 40]
        candidates = candidates[key[1] % 3:] + candidates[:key[1] % 3]
        for base_ply in candidates:
            ply = base_ply + (0 if chosen_white else 1)
            if ply >= len(moves):
                continue
            board = game.board()
            for move in moves[:ply]:
                board.push(move)
            if not board.is_check() and board.legal_moves.count() >= 3 and not board.is_game_over(claim_draw=True):
                positions.append({"source_game": index, "source_match": spec["id"],
                                  "source_ply": ply, "fen": board.fen(),
                                  "history": [m.uci() for m in moves[:ply]]})
                break
        else:
            excluded.append({"opening": list(opening), "source_game": index,
                             "reason": "No eligible preselected ply (ended, check, or <3 legal moves)"})
    return positions, excluded


def score_info(info, color):
    score = info["score"].pov(color)
    return {"cp_or_mate_equivalent": score.score(mate_score=100000), "mate": score.mate(),
            "depth": info.get("depth"), "nodes": info.get("nodes"),
            "pv": [m.uci() for m in info.get("pv", [])]}


def judge_loss(baseline, selected):
    if baseline["mate"] is not None or selected["mate"] is not None:
        return None
    return baseline["cp_or_mate_equivalent"] - selected["cp_or_mate_equivalent"]


def common_position_probe(spec, results_dir):
    destination = results_dir / "style-probes.jsonl"
    manifest = results_dir / "style-positions.json"
    if destination.exists() or manifest.exists():
        raise FileExistsError("Do not overwrite existing style probe evidence")
    positions, excluded = probe_positions(spec, results_dir)
    judge_binary = ROOT / ".benchmark-tools/Stockfish/src/stockfish-17.1"
    judge_options = {"Threads": 1, "Hash": 32, "UCI_LimitStrength": False, "Skill Level": 20, "SyzygyProbeLimit": 0}
    paths = {"source_pgn": results_dir / (spec["id"] + ".pgn"),
             "model": ROOT / "weights/chromatique-v4.native", "judge_binary": judge_binary,
             "script": Path(__file__)}
    paths.update({f"engine_{i}": ROOT / entry["binary"] for i, entry in enumerate(spec["engines"])})
    manifest.write_text(json.dumps(
        {"prepared_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "source_match": spec["id"], "engine_spec": spec["engines"], "play_ponder": False,
         "judge_binary": str(judge_binary.relative_to(ROOT)), "judge_options": judge_options,
         "inputs_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()},
         "selection": "one hash-selected game and eligible preselected ply per opening pair",
         "positions": positions, "excluded": excluded}, indent=2) + "\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith("CHROMATIQUE_")}
    engines = []
    try:
        for entry in spec["engines"]:
            engine = chess.engine.SimpleEngine.popen_uci(str(ROOT / entry["binary"]), env=env)
            engine.configure({k: v for k, v in entry["options"].items() if k not in ["Ponder", "MultiPV"]})
            engines.append(engine)
        judge = chess.engine.SimpleEngine.popen_uci(str(judge_binary), env=env)
        judge.configure(judge_options)
        engines.append(judge)
        with destination.open("x") as output:
            for index, position in enumerate(positions):
                board = chess.Board()
                for uci in position["history"]:
                    board.push_uci(uci)
                best = judge.analyse(board, chess.engine.Limit(nodes=200000), game=object())
                baseline = score_info(best, board.turn)
                choices = []
                evaluated = {}
                for entry, engine in zip(spec["engines"], engines[:2]):
                    play = engine.play(board, chess.engine.Limit(time=0.25), game=object(), ponder=False, info=chess.engine.INFO_ALL)
                    move = play.move
                    if move not in board.legal_moves:
                        raise ValueError("Invalid choice from style engine")
                    if move not in evaluated:
                        info = judge.analyse(board, chess.engine.Limit(nodes=200000), root_moves=[move], game=object())
                        evaluated[move] = score_info(info, board.turn)
                    evaluation = evaluated[move]
                    loss = judge_loss(baseline, evaluation)
                    choices.append({"engine": entry["name"], "move": move.uci(), "san": board.san(move),
                                    **move_features(board, move), "judge": evaluation,
                                    "judge_loss_cp": loss, "search_nodes": play.info.get("nodes"),
                                    "search_depth": play.info.get("depth")})
                row = {"index": index, **position, "choice_seconds": 0.25, "judge_nodes_per_search": 200000,
                       "baseline_judge": baseline, "choices": choices}
                output.write(json.dumps(row) + "\n")
                output.flush()
                if (index + 1) % 20 == 0:
                    print(f"Style positions complete: {index + 1}/{len(positions)}", flush=True)
    finally:
        for engine in engines:
            engine.quit()


def summarize_probes(results_dir):
    rows = [json.loads(s) for s in (results_dir / "style-probes.jsonl").read_text().splitlines()]
    expected = json.loads((results_dir / "style-positions.json").read_text())["positions"]
    if len(rows) != len(expected) or [r["index"] for r in rows] != list(range(len(expected))):
        raise ValueError("Incomplete style probes")
    measures = {
        "check": lambda c: int(c["check"]), "capture": lambda c: int(c["capture"]),
        "quiet": lambda c: int(c["quiet"]),
        "material_offer_proxy": lambda c: int(c["material_concession_proxy"] >= 1),
        "low_loss_offer_proxy": lambda c: int(c["material_concession_proxy"] >= 1 and c["judge_loss_cp"] <= 50),
        "loss_ge100cp": lambda c: int(c["judge_loss_cp"] >= 100),
    }
    result = {"positions": len(rows), "same_choice": sum(r["choices"][0]["move"] == r["choices"][1]["move"] for r in rows),
              "choice_seconds": 0.25, "judge_nodes_per_search": 200000, "metrics": {}}
    result["mate_transitions"] = [{"index": r["index"], "baseline_mate": r["baseline_judge"]["mate"],
                                    "selected_mates": [c["judge"]["mate"] for c in r["choices"]]}
                                   for r in rows if any(c["judge_loss_cp"] is None for c in r["choices"])]
    rng = np.random.default_rng(20261020)
    for name, function in measures.items():
        eligible = rows if name not in ("low_loss_offer_proxy", "loss_ge100cp") else [
            r for r in rows if all(c["judge_loss_cp"] is not None for c in r["choices"])]
        if not eligible:
            result["metrics"][name] = {"eligible_pairs": 0, "counts": None, "rates": None,
                                        "target_minus_reference": None, "paired_bootstrap95": None,
                                        "hoeffding95_difference": None}
            continue
        values = np.array([[function(c) for c in r["choices"]] for r in eligible])
        delta = values[:, 0] - values[:, 1]
        samples = rng.choice(delta, size=(20000, len(delta)), replace=True).mean(axis=1)
        interval = np.quantile(samples, [0.025, 0.975]).tolist() if len(set(delta)) > 1 else None
        halfwidth = 2 * math.sqrt(math.log(2 / 0.05) / (2 * len(delta)))
        result["metrics"][name] = {"eligible_pairs": len(eligible), "counts": values.sum(axis=0).tolist(), "rates": values.mean(axis=0).tolist(),
                                   "target_minus_reference": float(delta.mean()),
                                   "paired_bootstrap95": interval,
                                   "hoeffding95_difference": [max(-1, float(delta.mean()) - halfwidth), min(1, float(delta.mean()) + halfwidth)]}
    losses = [[max(0, r["choices"][i]["judge_loss_cp"]) for r in rows if r["choices"][i]["judge_loss_cp"] is not None] for i in [0, 1]]
    result["median_nonnegative_judge_loss_cp"] = [statistics.median(v) if v else None for v in losses]
    result["nonmate_loss_positions_per_engine"] = [len(v) for v in losses]
    (results_dir / "style-probe-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schedule", type=Path)
    parser.add_argument("--central-match", required=True)
    parser.add_argument("--summarize-only", action="store_true")
    parser.add_argument("--results-dir", type=Path, default=BASE / "results")
    args = parser.parse_args()
    schedule = json.loads(args.schedule.read_text())
    if not args.summarize_only:
        spec = next(m for m in schedule["matches"] if m["id"] == args.central_match)
        common_position_probe(spec, args.results_dir)
        describe(schedule, args.results_dir)
    summarize_probes(args.results_dir)


if __name__ == "__main__":
    main()
