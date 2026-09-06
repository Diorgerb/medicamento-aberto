#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from source_registry import SOURCES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description='Compara os seis downloads com a publicação atual.')
    parser.add_argument('--input', default='public/fontes')
    parser.add_argument('--manifest', default='public/data/manifest.json')
    parser.add_argument('--github-output', default='')
    parser.add_argument('--fail-if-unchanged', action='store_true')
    args = parser.parse_args()

    input_dir = Path(args.input)
    manifest_path = Path(args.manifest)
    previous: dict[str, str] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            previous = {
                str(item.get('key', '')): str(item.get('sha256', ''))
                for item in manifest.get('sources', [])
                if item.get('key')
            }
        except Exception as exc:
            print(f'[WARN] Não foi possível ler o manifest atual: {exc}')

    current: dict[str, str] = {}
    missing: list[str] = []
    for source in SOURCES:
        path = input_dir / source.filenames[0]
        if not path.exists():
            missing.append(path.name)
            continue
        current[source.key] = sha256_file(path)

    if missing:
        raise RuntimeError('Downloads obrigatórios ausentes: ' + ', '.join(missing))

    changed_keys = [key for key, digest in current.items() if previous.get(key) != digest]
    changed = bool(changed_keys) or len(previous) != len(current)

    print('[CHECK] Fontes alteradas: ' + (', '.join(changed_keys) if changed_keys else 'nenhuma'))
    print(f'[CHECK] changed={str(changed).lower()}')

    if args.github_output:
        with Path(args.github_output).open('a', encoding='utf-8') as out:
            out.write(f'changed={str(changed).lower()}\n')
            out.write(f'changed_keys={",".join(changed_keys)}\n')

    if args.fail_if_unchanged and not changed:
        raise SystemExit(10)


if __name__ == '__main__':
    main()
