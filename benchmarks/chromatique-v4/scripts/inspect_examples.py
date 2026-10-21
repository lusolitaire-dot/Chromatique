"""Rejudge fixed, mechanically selected offer examples at two million nodes."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import chess
import chess.engine
import chess.pgn

from style import judge_loss, score_info

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/chromatique-v4"
NODES = 2000000
RULE = "Two lowest-loss offer candidates and one highest; rank negative losses as zero, ties by probe index; exclude mate-valued losses; deduplicate. No game-outcome filter."


def select_examples(rows):
    candidates = [r for r in rows if r["choices"][0]["material_concession_proxy"] >= 1
                  and r["choices"][0]["judge_loss_cp"] is not None]
    low = sorted(candidates, key=lambda r: (max(0, r["choices"][0]["judge_loss_cp"]), r["index"]))
    high = sorted(candidates, key=lambda r: (-max(0, r["choices"][0]["judge_loss_cp"]), r["index"]))
    result = []
    for row in low[:2] + high[:1]:
        if row["index"] not in {r["index"] for r in result}:
            result.append(row)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=BASE / "results")
    args = parser.parse_args()
    source = args.results_dir / "style-probes.jsonl"
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    expected = json.loads((args.results_dir / "style-positions.json").read_text())["positions"]
    if len(rows) != len(expected) or [r["index"] for r in rows] != list(range(len(expected))):
        raise ValueError("Incomplete style probes; do not select examples from a partial panel")
    selection = select_examples(rows)
    destination = args.results_dir / "style-examples.json"
    pgn_destination = args.results_dir / "style-examples.pgn"
    if destination.exists() or pgn_destination.exists():
        raise FileExistsError("Existing example evidence; use a fresh results directory to rerun")
    binary = ROOT / ".benchmark-tools/Stockfish/src/stockfish-17.1"
    output = {"selection_rule": RULE, "probe_file_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "judge_binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "judge_nodes_per_search": NODES, "examples": []}
    games = []
    env = {k: v for k, v in os.environ.items() if not k.startswith("CHROMATIQUE_")}
    with chess.engine.SimpleEngine.popen_uci(str(binary), env=env) as judge:
        judge.configure({"Threads": 1, "Hash": 32, "UCI_LimitStrength": False,
                         "Skill Level": 20, "SyzygyProbeLimit": 0})
        for row in selection:
            board = chess.Board()
            for move in row["history"]:
                board.push_uci(move)
            if board.fen() != row["fen"]:
                raise ValueError("Example history/FEN mismatch")
            info = judge.analyse(board, chess.engine.Limit(nodes=NODES), game=object())
            baseline = score_info(info, board.turn)
            game = chess.pgn.Game.from_board(board)
            game.headers.update(Event="Analysis: common-position material offer", White="Analysis", Black="Analysis",
                                Result="*", Annotator="Stockfish17.1, 2 million nodes per search",
                                SourceMatch=row["source_match"], SourceGame=str(row["source_game"]),
                                SourcePly=str(row["source_ply"]), ProbeIndex=str(row["index"]))
            root_node = game.end()
            root_node.comment = "Source game history ends here. Following variations are judge analysis, not played game results."
            choices = []
            evaluated = {}
            for choice in row["choices"]:
                move = chess.Move.from_uci(choice["move"])
                if move not in evaluated:
                    info = judge.analyse(board, chess.engine.Limit(nodes=NODES), root_moves=[move], game=object())
                    evaluated[move] = score_info(info, board.turn)
                evaluation = evaluated[move]
                loss = judge_loss(baseline, evaluation)
                choices.append({"engine": choice["engine"], "move": choice["move"], "san": choice["san"],
                                "original_judge_loss_cp": choice["judge_loss_cp"],
                                "material_concession_proxy": choice["material_concession_proxy"],
                                "judge": evaluation, "judge_loss_cp": loss})
                node = root_node.add_variation(move)
                node.comment = f"{choice['engine']} choice; offer proxy={choice['material_concession_proxy']}; 2M-node judge loss={loss} cp (None means mate-valued)."
                continuation = board.copy()
                continuation.push(move)
                pv = evaluation["pv"]
                if not pv or pv[0] != choice["move"]:
                    raise ValueError("Judge PV does not begin with its forced root move")
                for uci in pv[1:]:
                    following = chess.Move.from_uci(uci)
                    if following not in continuation.legal_moves:
                        raise ValueError("Illegal judge PV")
                    node = node.add_variation(following)
                    continuation.push(following)
            output["examples"].append({"probe_index": row["index"], "source_match": row["source_match"],
                                        "source_game": row["source_game"], "source_ply": row["source_ply"],
                                        "fen": row["fen"], "history": row["history"],
                                        "baseline_judge": baseline, "choices": choices})
            games.append(str(game))
            print(f"Example probe {row['index']}: {[c['judge_loss_cp'] for c in choices]}", flush=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    pgn_destination.write_text("\n\n".join(games) + ("\n" if games else ""))
    print(f"Retained {len(games)} rejudged examples; no mate surrogate used as centipawn loss")


if __name__ == "__main__":
    main()
