"""Run an explicit fixed schedule with Fastchess; never overwrite match evidence."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/chromatique-v4"
FASTCHESS = ROOT / ".benchmark-tools/fastchess/fastchess"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run(spec, results_dir):
    prefix = results_dir / spec["id"]
    receipt = prefix.with_suffix(".run.json")
    pgn = prefix.with_suffix(".pgn")
    log = prefix.with_suffix(".log")
    book = BASE / "data" / (spec["panel"] + "-openings.pgn")
    inputs = {"fastchess": sha(FASTCHESS), "opening_book": sha(book),
              "model": sha(ROOT / "weights/chromatique-v4.native")}
    cmd = [str(FASTCHESS)]
    env = {k: v for k, v in os.environ.items() if not k.startswith("CHROMATIQUE_")}
    for index, engine in enumerate(spec["engines"]):
        binary = ROOT / engine["binary"]
        inputs[f"engine_{index}"] = sha(binary)
        probe = subprocess.run([str(binary)], input="uci\nquit\n", text=True,
                               capture_output=True, check=True, timeout=15, env=env)
        supported = set(re.findall(r"^option name (.*?) type ", probe.stdout, re.MULTILINE))
        if missing := set(engine["options"]) - supported:
            raise ValueError(f"Unsupported options for {engine['name']}: {missing}")
        cmd += ["-engine", f"cmd={binary}", f"name={engine['name']}", "proto=uci"]
        cmd += [f"option.{k}={str(v).lower() if isinstance(v, bool) else v}"
                for k, v in engine["options"].items()]
    cmd += ["-each", f"tc={spec['tc']}", "timemargin=100", "restart=on", "-rounds", str(spec["pairs"]),
            "-repeat", "-recover", "-concurrency", str(spec.get("concurrency", 6)),
            "-openings", f"file={book}", "format=pgn", "order=sequential", "plies=16",
            "-maxmoves", "300", "-pgnout", f"file={pgn}", "append=false", "nodes=true",
            "timeleft=true", "-event", spec["id"], "-site", "Local Apple Silicon benchmark",
            "-config", f"outname={prefix.with_suffix('.state.json')}", "-autosaveinterval", "20"]
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        if (previous.get("returncode") == 0 and previous["spec"] == spec and previous["command"] == cmd
                and previous["inputs_sha256"] == inputs and pgn.exists()
                and previous.get("pgn_sha256") == sha(pgn)):
            print(f"Already complete: {spec['id']}", flush=True)
            return
        raise FileExistsError(f"Unfinished or changed run: {receipt}; inspect it before recovery")
    if pgn.exists() or log.exists():
        raise FileExistsError(f"Existing artifacts for {spec['id']}")
    info = {"spec": spec, "inputs_sha256": inputs, "command": cmd, "started_utc": now(),
            "platform": platform.platform(), "logical_cpus": os.cpu_count(),
            "python": sys.version, "runner_pid": os.getpid(),
            "environment_policy": "Inherited environment, with all CHROMATIQUE_* removed"}
    receipt.write_text(json.dumps(info, indent=2) + "\n")
    print(f"Starting {spec['id']}: {2 * spec['pairs']} games, {spec['tc']}", flush=True)
    with log.open("x") as output:
        process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
        info["fastchess_pid"] = process.pid
        receipt.write_text(json.dumps(info, indent=2) + "\n")
        info["returncode"] = process.wait()
    info["finished_utc"] = now()
    if pgn.exists():
        info["pgn_sha256"] = sha(pgn)
    receipt.write_text(json.dumps(info, indent=2) + "\n")
    if info["returncode"] != 0:
        raise RuntimeError(f"Fastchess failed: inspect {log}")
    print(f"Finished {spec['id']}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schedule", type=Path)
    parser.add_argument("--results-dir", type=Path, default=BASE / "results")
    args = parser.parse_args()
    args.results_dir = args.results_dir.resolve()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    for spec in json.loads(args.schedule.read_text())["matches"]:
        run(spec, args.results_dir)


if __name__ == "__main__":
    main()
