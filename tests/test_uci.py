"""Release contract: standalone UCI, legality and lossless neural inference."""
import gzip
import hashlib
import json
import os
import queue
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

import chess
import chess.engine
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from pure_features import encode, move_index

BINARY = ROOT / 'bin/chromatique-v4'
WEIGHTS = ROOT / 'weights/chromatique-v4.native'


def environment():
    return {k:v for k,v in os.environ.items() if not k.startswith('CHROMATIQUE_')}


class Probe:
    def __init__(self, binary=BINARY, cwd=None):
        self.p = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, bufsize=1,
                                  env=environment(), cwd=cwd)
        self.q = queue.Queue()
        def read():
            for line in self.p.stdout:
                self.q.put(line.rstrip())
            self.q.put(None)
        self.reader = threading.Thread(target=read, daemon=True); self.reader.start()
        self.send('uci'); self.handshake = self.until(lambda s:s=='uciok')
        self.send('setoption name Hash value 1')
        self.send('setoption name Threads value 1')
        self.send('isready'); self.until(lambda s:s=='readyok')

    def send(self, text):
        self.p.stdin.write(text+'\n'); self.p.stdin.flush()

    def until(self, predicate):
        lines=[]
        while True:
            line=self.q.get(timeout=15)
            if line is None:
                raise AssertionError(self.p.stderr.read())
            lines.append(line)
            if predicate(line):
                return lines

    def position(self, board):
        self.send('position fen '+board.root().fen(en_passant='fen')+
                  (' moves '+' '.join(m.uci() for m in board.move_stack) if board.move_stack else ''))

    def evaluate(self, board):
        self.position(board); self.send('eval'); self.send('isready')
        lines=self.until(lambda s:s=='readyok')
        return json.loads(next(s.removeprefix('chromatique ') for s in lines if s.startswith('chromatique {')))

    def close(self):
        if self.p.poll() is None:
            self.send('quit'); self.p.wait(timeout=15)
        self.reader.join(timeout=2)
        for pipe in [self.p.stdin,self.p.stdout,self.p.stderr]:
            pipe.close()

    def __enter__(self): return self
    def __exit__(self,*_): self.close()


def parity_cases():
    cases=[chess.Board(f) for f in [chess.STARTING_FEN,
        'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1',
        '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1',
        '4k3/P7/8/8/8/8/8/4K3 w - - 0 1']]
    for fen,moves in [(chess.STARTING_FEN,['e2e4','a7a6','e4e5','d7d5','e5d6']),
        (chess.STARTING_FEN,['g1f3','g8f6','f3g1','f6g8','g1f3','g8f6','f3g1','f6g8']),
        ('r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 17 22',['e8c8','e1g1']),
        ('4k3/P7/8/8/8/8/8/4K3 w - - 0 1',['a7a8n'])]:
        b=chess.Board(fen); cases.append(b.copy())
        for u in moves:
            b.push_uci(u);cases.append(b.copy())
    rng=random.Random(1919);b=chess.Board()
    while len(cases)<120:
        if b.is_game_over(): b=chess.Board()
        b.push(rng.choice(list(b.legal_moves)));cases.append(b.copy())
    return cases


class UCIRelease(unittest.TestCase):
    def test_01_model_identity_and_byte_identical_export(self):
        manifest=json.loads((ROOT/'release.json').read_text())
        for name,h in manifest['weights'].items():
            self.assertEqual(hashlib.sha256((ROOT/'weights'/name).read_bytes()).hexdigest(),h)
        for stem in ('chromatique-v4','pure-v4'):
            with self.subTest(model=stem), tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'model.native'
                subprocess.run([sys.executable,str(ROOT/'tools/export_native.py'),
                                str(ROOT/'weights'/f'{stem}.json.gz'),str(target)],check=True,
                               stdout=subprocess.DEVNULL)
                self.assertEqual((ROOT/'weights'/f'{stem}.native').read_bytes(),target.read_bytes())

    def test_02_native_reference_parity_120_positions(self):
        for stem in ('chromatique-v4','pure-v4'):
            p=json.loads(gzip.decompress((ROOT/'weights'/f'{stem}.json.gz').read_bytes()))
            def layer(d):
                return np.asarray(d['weight'],np.float32).reshape(d['output'],d['input']),np.asarray(d['bias'],np.float32)
            w1,b1=layer(p['layers'][0]);w2,b2=layer(p['layers'][1]);wv,bv=layer(p['value_head'])
            wl,bl=layer(p['linear_head']);wp,bp=layer(p['policy_head'])
            with tempfile.TemporaryDirectory() as cwd, Probe(cwd=cwd) as probe:
                self.assertIn('id name Chromatique v4',probe.handshake)
                if stem == 'pure-v4':
                    probe.send('setoption name ChromatiqueModel value '+str(ROOT/'weights/pure-v4.native'))
                    probe.send('isready');probe.until(lambda line:line=='readyok')
                for board in parity_cases():
                    actual=probe.evaluate(board);x=encode(board)
                    np.testing.assert_array_equal(np.asarray(actual['features'],np.float32),x)
                    first=np.maximum(w1@x+b1,0);hidden=np.maximum(w2@first+b2,0)
                    cp=float(np.clip(600*(wv@hidden+bv+wl@x+bl)[0],-10000,10000))
                    self.assertAlmostEqual(actual['cp'],cp,delta=.02)
                    logits=(wp@first+bp)/p['policy_temperature']
                    self.assertEqual({s['move'] for s in actual['policy']},{m.uci() for m in board.legal_moves})
                    for item in actual['policy']:
                        index=move_index(chess.Move.from_uci(item['move']),board.turn)
                        self.assertAlmostEqual(item['logit'],float(logits[index]),delta=.0001)

    def test_03_uci_search_mate_stalemate_and_history(self):
        with tempfile.TemporaryDirectory() as cwd, chess.engine.SimpleEngine.popen_uci(
                str(BINARY),cwd=cwd,env=environment()) as e:
            self.assertEqual(e.id['name'],'Chromatique v4')
            e.configure({'Threads':1,'Hash':1,'SyzygyProbeLimit':0})
            board=chess.Board()
            for u in ['e2e4','e7e5','g1f3','b8c6']:board.push_uci(u)
            self.assertIn(e.play(board,chess.engine.Limit(nodes=5000),game=object()).move,board.legal_moves)
            board=chess.Board('r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1')
            move=e.play(board,chess.engine.Limit(time=.1),game=object()).move
            self.assertIn(move,board.legal_moves);board.push(move);self.assertTrue(board.is_checkmate())
            board=chess.Board('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
            self.assertIsNone(e.play(board,chess.engine.Limit(time=.1),game=object()).move)

    def test_04_perft_start_and_kiwipete(self):
        with Probe() as p:
            for fen,depth,nodes in [(chess.STARTING_FEN,4,197281),
                ('r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',3,97862)]:
                p.position(chess.Board(fen));p.send(f'go perft {depth}')
                lines=p.until(lambda s:s.startswith('Nodes searched:'))
                self.assertEqual(int(lines[-1].split(':')[1]),nodes)

    def test_05_stop_and_readiness(self):
        with Probe() as p:
            p.send('ucinewgame');p.send('position startpos');p.send('go infinite')
            p.until(lambda s:s.startswith('info depth '));p.send('stop')
            lines=p.until(lambda s:s.startswith('bestmove '))
            self.assertIn(chess.Move.from_uci(lines[-1].split()[1]),chess.Board().legal_moves)
            p.send('isready');self.assertEqual(p.until(lambda s:s=='readyok')[-1],'readyok')

    def test_06_relocated_package_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='Chromatique release ') as tmp:
            root=Path(tmp);(root/'bin').mkdir();(root/'weights').mkdir()
            binary=root/'bin/chromatique-v4';shutil.copy2(BINARY,binary)
            shutil.copy2(WEIGHTS,root/'weights/chromatique-v4.native')
            with Probe(binary=binary,cwd=Path.home()) as p:
                self.assertIn('id name Chromatique v4',p.handshake)

    def test_07_missing_model_fails_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=subprocess.run([str(BINARY)],input='uci\nquit\n',text=True,capture_output=True,
                 env={**environment(),'CHROMATIQUE_NATIVE_MODEL':str(Path(tmp)/'missing.native')},timeout=15)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('Chromatique model error',p.stderr)


if __name__=='__main__':unittest.main()
