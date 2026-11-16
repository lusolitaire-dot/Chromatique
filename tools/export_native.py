"""Lossless float32 export for Chromatique CHROMA3 and CHROMA4 models."""
import argparse, gzip, hashlib, json, struct
from pathlib import Path
import numpy as np

def layer(d):
    return np.asarray(d['weight'], np.float32).reshape(d['output'], d['input']).T.copy(), np.asarray(d['bias'], np.float32)

def export(model, out):
    raw = Path(model).read_bytes(); raw = gzip.decompress(raw) if str(model).endswith('.gz') else raw
    p = json.loads(raw)
    assert p['schema'] in (3, 4) and p['evaluation_kind'] == 'fully_neural'
    assert not p['classical_evaluation'] and not p['fixed_material']
    assert p['input_dim'] == 820 and p['architecture'] == [820, 512, 32]
    assert 'classical_blend' not in p
    assert len(p['policy_moves']) == 1968 and len(set(p['policy_moves'])) == 1968
    assert p['output_scale_cp'] == 600 and p['output_limit_cp'] == 10000
    assert p['score_perspective'] == 'side_to_move'
    assert np.isfinite(p['policy_temperature']) and p['policy_temperature'] > 0
    for key, ni, no in [('layers.0', 820, 512), ('layers.1', 512, 32), ('value_head', 32, 1), ('linear_head', 820, 1), ('policy_head', 512, 1968)]:
        d = p[key] if '.' not in key else p[key.split('.')[0]][int(key.split('.')[1])]
        assert d['input'] == ni and d['output'] == no
        assert len(d['weight']) == ni * no and len(d['bias']) == no
        assert np.isfinite(d['weight']).all() and np.isfinite(d['bias']).all()
    arrays = []
    w1, b1 = layer(p['layers'][0]); w2, b2 = layer(p['layers'][1])
    wv = np.asarray(p['value_head']['weight'], np.float32); bv = np.asarray(p['value_head']['bias'], np.float32)
    wl = np.asarray(p['linear_head']['weight'], np.float32); bl = np.asarray(p['linear_head']['bias'], np.float32)
    wp = np.asarray(p['policy_head']['weight'], np.float32); bp = np.asarray(p['policy_head']['bias'], np.float32)
    arrays += [w1, b1, np.asarray(p['layers'][1]['weight'], np.float32), b2, wv, bv, wl, bl, wp, bp, np.asarray([p['policy_temperature']], np.float32)]
    if p['schema'] == 3:
        assert p['policy_input'] == 'first_hidden_layer' and p['feature_version'] == 'chromatique-pure-v1'
        magic = b'CHROMA3\0'; extra = 0
    else:
        assert p['schema'] == 4 and p['policy_input'] == 'independent_first_hidden_layer'
        ep = p['policy_encoder']
        assert ep['input'] == 820 and ep['output'] == 512 and len(ep['weight']) == 820 * 512 and len(ep['bias']) == 512
        we, be = layer(ep)
        arrays += [we, be]; magic = b'CHROMA4\0'; extra = 820 * 512 + 512
    payload = b''.join(np.asarray(a, dtype='<f4').tobytes() for a in arrays)
    for name in p['policy_moves']:
        assert len(name) in (4, 5) and name.isascii(); payload += name.encode().ljust(6, b'\0')
    checksum = 14695981039346656037
    for b in payload: checksum = ((checksum ^ b) * 1099511628211) & ((1 << 64) - 1)
    source_sha = hashlib.sha256(raw).hexdigest()
    header = struct.pack('<8sIIII64sQ', magic, 820, 512, 32, 1968, source_sha.encode(), checksum)
    dest = Path(out); dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(header + payload)
    record = {'format': ('CHROMA4 independent-policy-encoder float32 little-endian' if p['schema'] == 4 else 'CHROMA3 float32 little-endian'),
              'source_model': str(model), 'source_model_sha256': source_sha,
              'native_sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'classical_evaluation': False,
              'fixed_material': False, 'policy_vocabulary': 1968, 'bytes': dest.stat().st_size,
              'parameter_count': 1867558 if p['schema'] == 4 else 766926}
    if p['schema'] == 4:
        record.update(all_float32=True, policy_encoder_input_dim=820, policy_encoder_output_dim=512)
    dest.with_suffix(dest.suffix + '.json').write_text(json.dumps(record, indent=2) + '\n'); print(json.dumps(record, indent=2))

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('model'); a.add_argument('out'); x = a.parse_args(); export(x.model, x.out)
