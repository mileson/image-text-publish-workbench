#!/usr/bin/env python3
"""Validate a workbench input and its local image assets without writing files."""
import argparse
import json
from pathlib import Path
from workbench_lib import normalize

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = normalize(json.loads(args.input.read_text(encoding='utf-8')))
        print(json.dumps({'ok': True, 'titles': len(payload['titles']), 'bodies': len(payload['body_variants']), 'covers': len(payload['covers']), 'photos': len(payload['photos'])}))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
