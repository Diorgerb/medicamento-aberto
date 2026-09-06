from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

NULL_STRINGS = {"nan", "none", "null", "<na>", "nat"}


def norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).replace("\xa0", " ").strip()
    return "" if text.lower() in NULL_STRINGS else text


def norm_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", norm(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def digits(value: Any) -> str:
    return re.sub(r"\D", "", norm(value))


def clean_record(row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in row.items():
        if value is None or (isinstance(value, float) and math.isnan(value)):
            result[str(key)] = ""
        elif isinstance(value, (int, float, bool)):
            result[str(key)] = value
        else:
            result[str(key)] = norm(value)
    return result


def unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = norm(value)
        key = norm_key(value)
        if value and key and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def split_multi(value: Any) -> list[str]:
    text = norm(value)
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                values = [norm(item.get("nome") if isinstance(item, dict) else item) for item in parsed]
                return unique(values)
        except (json.JSONDecodeError, TypeError):
            pass
    return unique(re.split(r"\s*\|\s*|\s*;\s*|\s*\n\s*", text))


def stable_id(prefix: str, *parts: Any) -> str:
    normalized = [norm_key(part) for part in parts if norm(part)]
    raw = "|".join(normalized) or "empty"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:18]
    return f"{prefix}-{digest}"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def dump_json(path: Path, data: Any, *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        if pretty:
            json.dump(data, stream, ensure_ascii=False, indent=2)
        else:
            json.dump(data, stream, ensure_ascii=False, separators=(",", ":"))


def _decode_sample(path: Path, encoding: str, max_bytes: int = 512 * 1024) -> str:
    with path.open("rb") as stream:
        raw = stream.read(max_bytes)
    return raw.decode(encoding)


def _header_candidates(
    path: Path,
    *,
    encoding: str,
    sep: str,
    expected_columns: Iterable[str],
    max_lines: int = 120,
) -> list[tuple[float, int, int]]:
    """Retorna candidatos (score, linha, nº de colunas) para o cabeçalho.

    O score favorece linhas que contêm nomes esperados e, como critério
    secundário, linhas com muitas colunas. Isso permite ler tanto os CSVs
    tabulares simples quanto arquivos que ganhem preâmbulo institucional.
    """
    try:
        sample = _decode_sample(path, encoding)
    except (UnicodeDecodeError, OSError):
        return []

    expected = {norm_key(column) for column in expected_columns if norm(column)}
    candidates: list[tuple[float, int, int]] = []
    for index, line in enumerate(sample.splitlines()[:max_lines]):
        if not line.strip():
            continue
        try:
            parsed = next(csv.reader([line], delimiter=sep))
        except (csv.Error, StopIteration):
            continue
        cells = [norm_key(cell) for cell in parsed]
        nonempty = [cell for cell in cells if cell]
        if len(nonempty) < 2:
            continue

        exact_hits = sum(1 for cell in nonempty if cell in expected) if expected else 0
        partial_hits = 0
        if expected:
            for cell in nonempty:
                if cell in expected:
                    continue
                if any(cell.startswith(token + " ") or token.startswith(cell + " ") for token in expected if len(token) >= 5):
                    partial_hits += 1
        # Hits explícitos dominam. A cardinalidade serve somente para desempate.
        score = exact_hits * 1000 + partial_hits * 100 + min(len(nonempty), 200)
        candidates.append((float(score), index, len(nonempty)))
    return sorted(candidates, key=lambda item: (-item[0], item[1], -item[2]))


def read_csv_robust(
    path: Path,
    *,
    expected_columns: Iterable[str] | None = None,
    min_columns: int = 2,
) -> pd.DataFrame:
    """Lê CSV com detecção defensiva de encoding, separador e cabeçalho.

    ``expected_columns`` é especialmente importante para a base principal:
    impede que uma linha de preâmbulo ou um parsing incorreto seja aceita como
    cabeçalho e, posteriormente, faça todas as linhas caírem na mesma chave.
    """
    separators = (";", ",", "\t", "|")
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin1")
    expected = list(expected_columns or [])
    errors: list[str] = []
    best: tuple[float, pd.DataFrame, str, str, int] | None = None

    for encoding in encodings:
        for sep in separators:
            candidates = _header_candidates(
                path,
                encoding=encoding,
                sep=sep,
                expected_columns=expected,
            )
            # Sempre tenta a linha 0, mesmo quando o scorer não encontrou nada.
            header_lines = [candidate[1] for candidate in candidates[:5]]
            if 0 not in header_lines:
                header_lines.append(0)

            for header_line in dict.fromkeys(header_lines):
                try:
                    frame = pd.read_csv(
                        path,
                        sep=sep,
                        encoding=encoding,
                        dtype=str,
                        keep_default_na=False,
                        low_memory=False,
                        skiprows=header_line,
                    )
                except Exception as exc:
                    errors.append(f"{sep!r}/{encoding}/linha {header_line + 1}: {exc}")
                    continue

                frame.columns = [str(column).replace("\ufeff", "").replace("\xa0", " ").strip() for column in frame.columns]
                if frame.shape[1] < min_columns:
                    continue

                normalized = {norm_key(column) for column in frame.columns}
                expected_norm = {norm_key(column) for column in expected if norm(column)}
                hits = len(normalized & expected_norm) if expected_norm else 0
                unnamed = sum(1 for column in frame.columns if norm_key(column).startswith("unnamed"))
                score = hits * 10000 + min(frame.shape[1], 500) * 10 - unnamed

                if best is None or score > best[0]:
                    best = (float(score), frame, sep, encoding, header_line)

                # Com nomes esperados, só encerra cedo quando já há evidência forte.
                if expected_norm and hits >= min(3, len(expected_norm)):
                    return frame
                if not expected_norm and frame.shape[1] >= min_columns and header_line == 0:
                    return frame

    if best is not None:
        _, frame, _, _, _ = best
        return frame
    raise RuntimeError(
        f"Não foi possível ler {path.name}. "
        f"Tentativas recentes: {' | '.join(errors[-5:])}"
    )

def column_map(frame: pd.DataFrame) -> dict[str, str]:
    return {norm_key(column): str(column) for column in frame.columns}


def resolve_column(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    columns = column_map(frame)
    for alias in aliases:
        hit = columns.get(norm_key(alias))
        if hit:
            return hit
    return None


def detect_registration_column(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    explicit = resolve_column(frame, aliases)
    if explicit:
        return explicit

    sample = frame.head(3000)
    best_column: str | None = None
    best_score = 0.0
    for column in sample.columns:
        values = [digits(value) for value in sample[column].tolist() if norm(value)]
        if len(values) < 15:
            continue
        matches = sum(1 for value in values if len(value) in {9, 13})
        score = matches / len(values)
        if score >= 0.70 and score > best_score:
            best_score = score
            best_column = str(column)
    return best_column


def first_nonempty(rows: list[dict[str, Any]], column: str | None) -> str:
    if not column:
        return ""
    for row in rows:
        value = norm(row.get(column, ""))
        if value:
            return value
    return ""


def all_nonempty(rows: list[dict[str, Any]], column: str | None) -> list[str]:
    if not column:
        return []
    return unique(norm(row.get(column, "")) for row in rows)


def dedupe_dicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        payload = json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if digest not in seen:
            seen.add(digest)
            result.append(row)
    return result
