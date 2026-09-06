#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
import warnings
from pathlib import Path
from urllib.parse import urljoin, urlparse

# Usa o repositório nativo de certificados do sistema operacional quando disponível.
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


def _tls_diagnostic() -> None:
    if TRUSTSTORE_ENABLED:
        print("[TLS ] certificados do sistema operacional habilitados via truststore")
    else:
        print("[TLS ] truststore não instalado; usando o mecanismo TLS padrão do Python")

    if os.getenv(TLS_FALLBACK_ENV, "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        print("[TLS ] fallback restrito para dados.anvisa.gov.br está DESABILITADO por variável de ambiente")


def _session(*, connect_retries: int = 2) -> requests.Session:
    retry = Retry(
        total=6,
        connect=connect_retries,
        read=6,
        status=6,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Medicamento-Aberto/1.0 (+https://github.com/Diorgerb/medicamento-aberto)",
            "Accept": "text/csv,text/plain,application/octet-stream,*/*",
        }
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


def _same_allowed_host(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() == ANVISA_OPEN_DATA_HOST


def _get_with_restricted_redirects(
    session: requests.Session,
    url: str,
    *,
    verify: bool,
    stream: bool = True,
    max_redirects: int = 5,
) -> requests.Response:
    """
    Faz GET permitindo redirecionamento apenas dentro de dados.anvisa.gov.br.

    Isso é especialmente importante no fallback TLS: verify=False nunca é aplicado
    a um host diferente da origem oficial configurada no projeto.
    """
    current = url

    for _ in range(max_redirects + 1):
        response = session.get(
            current,
            stream=stream,
            timeout=(30, 600),
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
                f"para um host diferente ({urlparse(target).hostname})."
            )
        current = target

    raise RuntimeError(f"Número excessivo de redirecionamentos ao baixar {url}")


def _open_response(url: str) -> tuple[requests.Response, bool]:
    """
    Tenta primeiro HTTPS com validação normal.

    Se, e somente se, houver erro de cadeia SSL no host fixo dados.anvisa.gov.br,
    repete a requisição com validação de certificado desabilitada para esse host.
    O arquivo ainda é submetido às validações de conteúdo antes de substituir a
    cópia versionada existente.

    Retorna (response, tls_fallback_used).
    """
    if not _same_allowed_host(url):
        raise RuntimeError(f"Host de download não autorizado: {urlparse(url).hostname}")

    verified_session = _session(connect_retries=1)
    try:
        response = _get_with_restricted_redirects(
            verified_session,
            url,
            verify=True,
            stream=True,
        )
        return response, False
    except requests.exceptions.SSLError as exc:
        verified_session.close()

        fallback_disabled = os.getenv(TLS_FALLBACK_ENV, "").strip() in {
            "1",
            "true",
            "TRUE",
            "yes",
            "YES",
        }
        if fallback_disabled:
            raise RuntimeError(
                "Falha na validação HTTPS e o fallback TLS está desabilitado. "
                f"Detalhe original: {exc}"
            ) from exc

        print(
            "[TLS ] cadeia de certificados incompleta em dados.anvisa.gov.br; "
            "usando fallback restrito ao host oficial da Anvisa"
        )

        insecure_session = _session(connect_retries=2)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InsecureRequestWarning)
                response = _get_with_restricted_redirects(
                    insecure_session,
                    url,
                    verify=False,
                    stream=True,
                )
            # Mantemos a sessão viva enquanto o response streaming é consumido.
            setattr(response, "_medicamento_aberto_session", insecure_session)
            return response, True
        except Exception:
            insecure_session.close()
            raise
    except Exception:
        verified_session.close()
        raise


def _close_response(response: requests.Response) -> None:
    response.close()
    session = getattr(response, "_medicamento_aberto_session", None)
    if session is not None:
        session.close()


def _validate_download(temporary: Path, target: Path) -> None:
    size = temporary.stat().st_size if temporary.exists() else 0
    if size < 100:
        raise RuntimeError(f"Download inválido ou vazio para {target.name}: {size} bytes")

    with temporary.open("rb") as check:
        prefix = check.read(4096).lstrip()

    lower = prefix.lower()
    if lower.startswith(b"<html") or lower.startswith(b"<!doctype html"):
        raise RuntimeError(f"A origem retornou HTML em vez de CSV para {target.name}")

    # Todos os seis arquivos utilizados pelo projeto são delimitados por ';'.
    # Esta checagem simples evita aceitar páginas de erro, JSON ou binários como CSV.
    if b";" not in prefix:
        raise RuntimeError(
            f"Conteúdo inesperado para {target.name}: o arquivo baixado não parece ser um CSV delimitado por ';'."
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
            for chunk in response.iter_content(chunk_size=1024 * 1024):
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

        # Só substitui a cópia versionada depois de o novo arquivo ter passado
        # pelas validações mínimas acima.
        shutil.move(str(temporary), str(target))

        mode = "fallback TLS restrito" if fallback_used else "TLS validado"
        print(f"[ OK ] {target.name} · {mode} · SHA-256 {sha256_file(target)[:16]}…")

    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    finally:
        if response is not None:
            _close_response(response)


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

    for source in selected:
        target = output / source.filenames[0]
        download(source.download_url, target, force=args.force)


if __name__ == "__main__":
    main()
