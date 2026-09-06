#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Usa o repositório nativo de certificados do sistema operacional.
# No Windows isso faz o Python confiar nas mesmas CAs que o navegador/Windows,
# sem desabilitar a validação TLS.
try:
    import truststore

    truststore.inject_into_ssl()
    TRUSTSTORE_ENABLED = True
except ImportError:
    TRUSTSTORE_ENABLED = False

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from common import sha256_file
from source_registry import SOURCE_BY_KEY, SOURCES


def _tls_diagnostic() -> None:
    if TRUSTSTORE_ENABLED:
        print("[TLS ] certificados do sistema operacional habilitados via truststore")
        return

    print("[TLS ] truststore não instalado; usando o mecanismo TLS padrão do Python")
    if sys.platform == "win32":
        print("      No Windows, instale as dependências com: python -m pip install -r requirements.txt")


def _session() -> requests.Session:
    retry = Retry(
        total=6,
        connect=6,
        read=6,
        status=6,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.headers.update({"User-Agent": "Medicamento-Aberto (+dados-abertos)"})
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


def download(url: str, target: Path, *, force: bool = False) -> None:
    if target.exists() and not force:
        print(f"[SKIP] {target.name} já existe. Use --force para substituir.")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    print(f"[GET ] {url}")
    try:
        with _session().get(url, stream=True, timeout=(30, 600), allow_redirects=True) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", "0") or 0)
            received = 0
            with temporary.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    stream.write(chunk)
                    received += len(chunk)
                    if total:
                        print(f"      {received / 1024 / 1024:7.1f} MB / {total / 1024 / 1024:7.1f} MB", end="\r")
            print()
    except requests.exceptions.SSLError as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            "Falha na validação HTTPS. A verificação SSL permanece habilitada por segurança. "
            "Reinstale as dependências com 'python -m pip install -r requirements.txt'. "
            "No Windows, o projeto usa truststore para consultar o repositório de certificados do sistema. "
            f"Detalhe original: {exc}"
        ) from exc
    size = temporary.stat().st_size if temporary.exists() else 0
    if size < 100:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Download inválido ou vazio para {target.name}: {size} bytes")
    with temporary.open("rb") as check:
        prefix = check.read(512).lstrip().lower()
    if prefix.startswith(b"<html") or prefix.startswith(b"<!doctype html"):
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"A origem retornou HTML em vez de CSV para {target.name}")
    shutil.move(temporary, target)
    print(f"[ OK ] {target.name} · SHA-256 {sha256_file(target)[:16]}…")


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa os arquivos de dados abertos utilizados pelo Medicamento Aberto.")
    parser.add_argument("--output", default="public/fontes", help="Pasta de destino")
    parser.add_argument("--only", nargs="*", choices=list(SOURCE_BY_KEY), help="Baixar apenas fontes específicas")
    parser.add_argument("--force", action="store_true", help="Substituir arquivos já existentes")
    args = parser.parse_args()

    selected = [SOURCE_BY_KEY[key] for key in args.only] if args.only else list(SOURCES)
    output = Path(args.output)

    _tls_diagnostic()

    for source in selected:
        # O primeiro nome é o nome canônico usado pelo projeto.
        target = output / source.filenames[0]
        download(source.download_url, target, force=args.force)


if __name__ == "__main__":
    main()
