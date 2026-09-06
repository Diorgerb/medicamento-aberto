#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Arquivo obrigatório ausente: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON inválido: {path}: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida a camada estática antes do deploy.")
    parser.add_argument("--data", default="public/data", help="Diretório da camada publicada")
    parser.add_argument("--min-products", type=int, default=100, help="Quantidade mínima de produtos para aceitar o deploy")
    args = parser.parse_args()

    root = Path(args.data)
    manifest = load_json(root / "manifest.json")
    catalog = load_json(root / "catalog" / "products.json")
    activity = load_json(root / "catalog" / "activity.json")

    if manifest.get("sourceMode") != "real":
        raise RuntimeError(
            "A camada de dados não foi gerada a partir da base real. Execute `npm run data:build` antes do deploy."
        )
    manifest_products = int(manifest.get("counts", {}).get("products", 0) or 0)
    if manifest_products < args.min_products:
        raise RuntimeError(
            f"Manifesto contém apenas {manifest_products} produto(s). O deploy foi bloqueado para evitar publicação incompleta."
        )
    if not isinstance(activity, dict) or not isinstance(activity.get("recentEvents", []), list) or not isinstance(activity.get("changes", []), list):
        raise RuntimeError("catalog/activity.json não contém a estrutura esperada do Monitor de Atualizações.")

    if not isinstance(catalog, list):
        raise RuntimeError("catalog/products.json não contém uma lista JSON.")
    if len(catalog) != manifest_products:
        raise RuntimeError(
            f"Contagem inconsistente: manifest={manifest_products}, catalog/products.json={len(catalog)}."
        )

    missing_buckets: set[str] = set()
    for item in catalog:
        bucket = str(item.get("bucket", "")).strip()
        if not bucket or not (root / "products" / f"{bucket}.json").exists():
            missing_buckets.add(bucket or "<vazio>")
    if missing_buckets:
        preview = ", ".join(sorted(missing_buckets)[:10])
        raise RuntimeError(f"Buckets de detalhe ausentes: {preview}")

    print(
        f"[OK] Publicação validada: {manifest_products:,} produtos · "
        f"{manifest.get('counts', {}).get('presentations', 0):,} apresentações comercializadas · "
        f"versão {manifest.get('dataVersion', '')}".replace(",", ".")
    )


if __name__ == "__main__":
    main()
