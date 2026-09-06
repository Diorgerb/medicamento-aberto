#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
import warnings
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import truststore

    truststore.inject_into_ssl()
    TRUSTSTORE_ENABLED = True
except ImportError:
    TRUSTSTORE_ENABLED = False

import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning
from urllib3.util.retry import Retry

from common import sha256_file
from source_registry import SOURCE_BY_KEY, SOURCES

ANVISA_OPEN_DATA_HOST = "dados.anvisa.gov.br"
TLS_FALLBACK_ENV = "MEDICAMENTO_ABERTO_DISABLE_TLS_FALLBACK"
REDIRECT_CODES = {301, 302, 303, 307, 308}
CHUNK_SIZE = 4 * 1024 * 1024

# O modo TLS é detectado apenas uma vez por execução.
# Se a primeira conexão comprovar que o host da Anvisa está com a cadeia
# incompleta, os downloads seguintes usam diretamente o fallback restrito.
_TLS_MODE: str | None = None  # None | "verified" | "fallback"
_VERIFIED_SESSION: requests.Session | None = None
_FALLBACK_SESSION: requests.Session | None = None


def _tls_diagnostic() -> None:
    if TRUSTSTORE_ENABLED:
        print("[TLS ] certificados do sistema operacional habilitados via truststore")
    else:
        print("[TLS ] truststore não instalado; usando o mecanismo TLS padrão do Python")

    if _fallback_disabled():
        print("[TLS ] fallback restrito para dados.anvisa.gov.br está DESABILITADO")


def _fallback_disabled() -> bool:
    return os.getenv(TLS_FALLBACK_ENV, "").strip().lower() in {"1", "true", "yes"}


def _session(*, verified_probe: bool = False) -> requests.Session:
    # A tentativa TLS validada é uma sondagem: não repetimos um erro de
    # certificado que será determinístico. Nos downloads reais, mantemos
    # poucas tentativas para falhas transitórias de rede/HTTP.
    if verified_probe:
        retry = Retry(
            total=0,
            connect=0,
            read=0,
            status=0,
            redirect=0,
            raise_on_status=False,
        )
    else:
        retry = Retry(
            total=3,
            connect=1,
            read=3,
            status=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
            raise_on_status=False,
        )

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Medicamento-Aberto (+dados-abertos)",
            "Accept": "text/csv,text/plain,application/octet-stream,*/*",
        }
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=4)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _verified_session() -> requests.Session:
    global _VERIFIED_SESSION
    if _VERIFIED_SESSION is None:
        _VERIFIED_SESSION = _session(verified_probe=True)
    return _VERIFIED_SESSION


def _fallback_session() -> requests.Session:
    global _FALLBACK_SESSION
    if _FALLBACK_SESSION is None:
        _FALLBACK_SESSION = _session(verified_probe=False)
    return _FALLBACK_SESSION


def _same_allowed_host(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() == ANVISA_OPEN_DATA_HOST


def _get_with_restricted_redirects(
    session: requests.Session,
    url: str,
    *,
    verify: bool,
    max_redirects: int = 5,
) -> requests.Response:
    current = url

    for _ in range(max_redirects + 1):
        response = session.get(
            current,
            stream=True,
            timeout=(10, 600),
            allow_redirects=False,
            verify=verify,
        )

        if response.status_code not in REDIRECT_CODES:
            return response

        location = response.headers.get("Location")
        response.close()
        if not location:
            raise RuntimeError(f"Redirecionamento sem cabeçalho Location em {current}")

        target = urljoin(current, location)
        if not _same_allowed_host(target):
            raise RuntimeError(
                "Redirecionamento recusado: a fonte oficial tentou direcionar o download "
                f"para outro host ({urlparse(target).hostname})."
            )
        current = target

    raise RuntimeError(f"Número excessivo de redirecionamentos ao baixar {url}")


def _open_fallback(url: str) -> requests.Response:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InsecureRequestWarning)
        return _get_with_restricted_redirects(
            _fallback_session(),
            url,
            verify=False,
        )


def _open_response(url: str) -> tuple[requests.Response, bool]:
    global _TLS_MODE

    if not _same_allowed_host(url):
        raise RuntimeError(f"Host de download não autorizado: {urlparse(url).hostname}")

    # Depois que a cadeia incompleta é detectada uma vez, não desperdiça tempo
    # repetindo o mesmo handshake inválido para as outras cinco fontes.
    if _TLS_MODE == "fallback":
        return _open_fallback(url), True

    try:
        response = _get_with_restricted_redirects(
            _verified_session(),
            url,
            verify=True,
        )
        _TLS_MODE = "verified"
        return response, False
    except requests.exceptions.SSLError as exc:
        if _fallback_disabled():
            raise RuntimeError(
                "Falha na validação HTTPS e o fallback TLS está desabilitado. "
                f"Detalhe original: {exc}"
            ) from exc

        _TLS_MODE = "fallback"
        print(
            "[TLS ] cadeia incompleta detectada em dados.anvisa.gov.br; "
            "fallback restrito ativado para esta execução"
        )
        return _open_fallback(url), True


def _validate_download(temporary: Path, target: Path) -> None:
    size = temporary.stat().st_size if temporary.exists() else 0
    if size < 100:
        raise RuntimeError(f"Download inválido ou vazio para {target.name}: {size} bytes")

    with temporary.open("rb") as check:
        prefix = check.read(4096).lstrip()

    lower = prefix.lower()
    if lower.startswith(b"<html") or lower.startswith(b"<!doctype html"):
        raise RuntimeError(f"A origem retornou HTML em vez de CSV para {target.name}")

    if b";" not in prefix:
        raise RuntimeError(
            f"Conteúdo inesperado para {target.name}: o arquivo não parece ser CSV delimitado por ';'."
        )

    if b"\n" not in prefix and b"\r" not in prefix:
        raise RuntimeError(f"Conteúdo inesperado para {target.name}: nenhuma quebra de linha encontrada.")


def download(url: str, target: Path, *, force: bool = False) -> None:
    if target.exists() and not force:
        print(f"[SKIP] {target.name} já existe. Use --force para substituir.")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    temporary.unlink(missing_ok=True)

    print(f"[GET ] {url}")
    response: requests.Response | None = None

    try:
        response, fallback_used = _open_response(url)
        response.raise_for_status()

        total = int(response.headers.get("content-length", "0") or 0)
        received = 0

        with temporary.open("wb") as stream:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                stream.write(chunk)
                received += len(chunk)
                if total:
                    print(
                        f"      {received / 1024 / 1024:7.1f} MB / {total / 1024 / 1024:7.1f} MB",
                        end="\r",
                    )

        if total:
            print()

        _validate_download(temporary, target)
        shutil.move(str(temporary), str(target))

        mode = "fallback TLS restrito" if fallback_used else "TLS validado"
        print(f"[ OK ] {target.name} · {mode} · SHA-256 {sha256_file(target)[:16]}…")

    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    finally:
        if response is not None:
            response.close()


def _close_sessions() -> None:
    global _VERIFIED_SESSION, _FALLBACK_SESSION
    if _VERIFIED_SESSION is not None:
        _VERIFIED_SESSION.close()
        _VERIFIED_SESSION = None
    if _FALLBACK_SESSION is not None:
        _FALLBACK_SESSION.close()
        _FALLBACK_SESSION = None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa os arquivos de dados abertos utilizados pelo Medicamento Aberto."
    )
    parser.add_argument("--output", default="public/fontes", help="Pasta de destino")
    parser.add_argument(
        "--only",
        nargs="*",
        choices=list(SOURCE_BY_KEY),
        help="Baixar apenas fontes específicas",
    )
    parser.add_argument("--force", action="store_true", help="Substituir arquivos já existentes")
    args = parser.parse_args()

    selected = [SOURCE_BY_KEY[key] for key in args.only] if args.only else list(SOURCES)
    output = Path(args.output)

    _tls_diagnostic()

    try:
        for source in selected:
            target = output / source.filenames[0]
            download(source.download_url, target, force=args.force)
    finally:
        _close_sessions()


if __name__ == "__main__":
    main()
