"""Select disjoint opening panels from the public CC0 8moves_v3 book."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

import chess.pgn

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/chromatique-v4"
ARCHIVE_SHA = "7e1e9dd118b4bb97d8a8b5b8a790c86e21f8509d59a27d2883767d94477be02e"
BOOK_REV = "a804a97e709f40aa75a00f9d19e84915b7a3a45c"


def main():
    archive = ROOT / ".benchmark-tools/8moves_v3.pgn.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA:
        raise ValueError("Opening archive checksum mismatch")
    with zipfile.ZipFile(archive) as z:
        stream = io.StringIO(z.read("8moves_v3.pgn").decode("utf-8-sig"))
    positions = {}
    count = 0
    while (game := chess.pgn.read_game(stream)) is not None:
        count += 1
        if game.errors:
            raise ValueError(game.errors)
        moves = list(game.mainline_moves())
        if len(moves) != 16:
            raise ValueError(f"Book game {count} is not 16 plies")
        board = game.end().board()
        if board.is_game_over(claim_draw=True):
            continue
        key = " ".join(board.fen().split()[:4])
        positions.setdefault(key, [m.uci() for m in moves])
    # Hash ranking fixes the sample independently of Python RNG implementation.
    keys = sorted(positions, key=lambda k: hashlib.sha256(
        ("chromatique-v4-20261020:" + k).encode()).digest())
    manifest = {"source_revision": BOOK_REV, "archive_sha256": ARCHIVE_SHA,
                "source_url": f"https://raw.githubusercontent.com/official-stockfish/books/{BOOK_REV}/8moves_v3.pgn.zip",
                "license": "CC0-1.0", "book_games": count,
                "distinct_nonterminal_positions": len(keys), "panels": {}}
    offset = 0
    for name, size in [("pilot", 50), ("main", 200), ("bridge", 100), ("slow", 50), ("anchor", 100)]:
        games = []
        for i, key in enumerate(keys[offset:offset + size], 1):
            game = chess.pgn.Game()
            game.headers.update(Event=f"Chromatique {name} opening", Round=str(i), Result="*")
            node = game
            for uci in positions[key]:
                node = node.add_variation(chess.Move.from_uci(uci))
            games.append(str(game))
        path = BASE / "data" / f"{name}-openings.pgn"
        content = "\n\n".join(games) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != content:
                raise ValueError(f"Existing opening panel differs: {path}")
        else:
            path.write_text(content, encoding="utf-8")
        manifest["panels"][name] = {"count": size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        offset += size
    (BASE / "data/openings.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
