#!/usr/bin/env python3
"""Build a self-contained HTML, normalized input, and asset manifest from JSON."""
import argparse
import hashlib
import json
from pathlib import Path
from workbench_lib import normalize, json_for_script, lean_payload

ROOT = Path(__file__).resolve().parents[1]


def build(input_path, output_path):
    payload = normalize(json.loads(Path(input_path).read_text(encoding='utf-8')))
    lean = lean_payload(payload)
    payload['input_fingerprint'] = hashlib.sha256(json_for_script(lean).encode()).hexdigest()
    template = (ROOT / 'assets/workbench.html').read_text(encoding='utf-8')
    core = (ROOT / 'assets/workbench-core.js').read_text(encoding='utf-8')
    app = (ROOT / 'assets/workbench-app.js').read_text(encoding='utf-8')
    output = template.replace('__CORE__', core).replace('__APP__', app).replace('__DATA__', json_for_script(payload))
    output_path = Path(output_path).resolve()
    if output_path == Path(input_path).resolve():
        raise ValueError('HTML 输出不能覆盖输入文件')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding='utf-8')
    normalized = output_path.with_name(output_path.stem + '.input.json')
    normalized.write_text(json.dumps(lean, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest_path = output_path.with_name(output_path.stem + '.assets.json')
    manifest_path.write_text(json.dumps({'document_id': payload['document_id'], 'assets': lean['covers'] + lean['photos']}, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'ok': True, 'html': str(output_path), 'input': str(normalized), 'assets': str(manifest_path), 'cover_count': len(payload['covers']), 'photo_count': len(payload['photos']), 'bytes': output_path.stat().st_size, 'published': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.input, args.output), ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
