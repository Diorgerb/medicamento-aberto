from __future__ import annotations

import io
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from common import clean_record, digits, norm, norm_key, resolve_column


@dataclass(frozen=True)
class CmedMetadata:
    fileName: str
    title: str
    publicationDate: str
    listType: str
    capRate: str
    headerLine: int
    rows: int
    columns: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_text(path: Path) -> str:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise RuntimeError(f"Não foi possível decodificar {path.name}: {last_error}")


def _normalize_header(column: str) -> str:
    text = str(column).replace("\xa0", " ").strip()
    if norm_key(text).startswith("destinacao comercial"):
        return "DESTINAÇÃO COMERCIAL"
    return re.sub(r"\s+", " ", text)


def read_cmed_csv(path: Path) -> tuple[pd.DataFrame, CmedMetadata]:
    """Lê uma lista CMED preservando o preâmbulo institucional e o cabeçalho real."""
    text = _read_text(path)
    lines = text.splitlines(keepends=True)

    header_index: int | None = None
    for index, line in enumerate(lines):
        key = norm_key(line)
        if key.startswith("substancia cnpj laboratorio codigo ggrem registro"):
            header_index = index
            break

    if header_index is None:
        raise RuntimeError(f"Cabeçalho tabular da CMED não localizado em {path.name}")

    preamble = "".join(lines[:header_index])
    tabular = "".join(lines[header_index:])
    frame = pd.read_csv(
        io.StringIO(tabular),
        sep=";",
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    frame.columns = [_normalize_header(column) for column in frame.columns]

    title = ""
    for line in preamble.splitlines():
        if "LISTA DE PREÇOS DE MEDICAMENTOS" in line.upper():
            title = line.strip(" ;\r\n\t\"")
            break

    publication_match = re.search(
        r"Publicada\s+em\s+(\d{2}/\d{2}/\d{4}(?:\s+\d{1,2}h\d{2}min\.?)?)",
        preamble,
        flags=re.IGNORECASE,
    )
    publication = publication_match.group(1).strip() if publication_match else ""

    cap_match = re.search(r"CAP\s+(?:é|e)\s+de\s+([\d,.]+%)", preamble, flags=re.IGNORECASE)
    cap_rate = cap_match.group(1) if cap_match else ""

    title_key = norm_key(title)
    normalized_columns = {norm_key(column) for column in frame.columns}
    if "maximos ao consumidor" in title_key or any(column.startswith("pmc ") for column in normalized_columns):
        list_type = "consumer"
    elif "venda ao governo" in title_key or any(column.startswith("pmvg ") for column in normalized_columns):
        list_type = "government"
    else:
        list_type = "unknown"

    metadata = CmedMetadata(
        fileName=path.name,
        title=title,
        publicationDate=publication,
        listType=list_type,
        capRate=cap_rate,
        headerLine=header_index + 1,
        rows=len(frame),
        columns=len(frame.columns),
    )
    return frame, metadata


def _clean_price(value: Any) -> str:
    text = norm(value)
    if not text:
        return ""
    return re.sub(r"[^0-9,.-]", "", text)


def _price_marker(value: Any) -> str:
    text = norm(value)
    return "*" if text and "*" in text else ""


def _price_band(column: str, prefix: str) -> str:
    remainder = re.sub(rf"^{re.escape(prefix)}\s*", "", column, flags=re.IGNORECASE).strip()
    key = norm_key(remainder)
    if not remainder or key == "base":
        return "Base"
    if key == "sem impostos":
        return "Sem impostos"
    match = re.search(r"(\d+(?:[,.]\d+)?)\s*%", remainder)
    if match:
        rate = match.group(1).replace(".", ",")
        alc = " ALC" if "alc" in key.split() else ""
        return f"{rate}%{alc}"
    return re.sub(r"\s+", " ", remainder)


def _price_specs(columns: list[str], prefix: str) -> list[tuple[str, str]]:
    prefix_key = norm_key(prefix)
    specs: list[tuple[str, str]] = []
    for column in columns:
        column_key = norm_key(column)
        if column_key == prefix_key or column_key.startswith(prefix_key + " "):
            specs.append((column, _price_band(column, prefix)))
    return specs


def _extract_price_specs(row: dict[str, Any] | None, specs: list[tuple[str, str]]) -> dict[str, str]:
    if not row:
        return {}
    return {band: _clean_price(row.get(column, "")) for column, band in specs}


def _extract_marker_specs(row: dict[str, Any] | None, specs: list[tuple[str, str]]) -> dict[str, str]:
    if not row:
        return {}
    output: dict[str, str] = {}
    for column, band in specs:
        marker = _price_marker(row.get(column, ""))
        if marker:
            output[band] = marker
    return output


def _ean_values(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for column in ("EAN 1", "EAN 2", "EAN 3"):
        value = digits(row.get(column, ""))
        if value and value not in values:
            values.append(value)
    return values


def _identity(row: dict[str, Any], key: str) -> str:
    return norm(row.get(key, ""))


def _pf_consistent(consumer: dict[str, str], government: dict[str, str]) -> bool | None:
    shared = set(consumer) & set(government)
    comparable = [band for band in shared if consumer.get(band) and government.get(band)]
    if not comparable:
        return None
    return all(consumer[band] == government[band] for band in comparable)


def _registration_parts(value: Any) -> tuple[str, str]:
    """Regra de domínio confirmada para estas fontes:

    - 13 dígitos: identifica a apresentação comercializada;
    - os 9 primeiros dígitos: identificam o medicamento/produto.

    Qualquer outro comprimento é preservado no registro bruto, mas não gera vínculo.
    """
    presentation_registration = digits(value)
    if len(presentation_registration) != 13:
        return presentation_registration, ""
    return presentation_registration, presentation_registration[:9]


def consolidate_cmed(
    consumer_df: pd.DataFrame,
    government_df: pd.DataFrame,
    consumer_meta: CmedMetadata | None,
    government_meta: CmedMetadata | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Funde PF/PMC e PF/PMVG por CÓDIGO GGREM.

    O GGREM identifica o registro econômico da CMED. A entidade de apresentação é o
    REGISTRO de 13 dígitos. O medicamento é identificado pelos 9 primeiros dígitos.
    """
    ggrem_aliases = ["CÓDIGO GGREM", "CODIGO GGREM", "GGREM"]
    consumer_ggrem = resolve_column(consumer_df, ggrem_aliases) if not consumer_df.empty else None
    government_ggrem = resolve_column(government_df, ggrem_aliases) if not government_df.empty else None

    consumer_columns = [str(column) for column in consumer_df.columns]
    government_columns = [str(column) for column in government_df.columns]
    consumer_pf_specs = _price_specs(consumer_columns, "PF")
    consumer_pmc_specs = _price_specs(consumer_columns, "PMC")
    government_pf_specs = _price_specs(government_columns, "PF")
    government_pmvg_specs = _price_specs(government_columns, "PMVG")

    consumer_rows: dict[str, dict[str, Any]] = {}
    government_rows: dict[str, dict[str, Any]] = {}
    consumer_duplicates = 0
    government_duplicates = 0

    if consumer_ggrem:
        for raw in consumer_df.to_dict(orient="records"):
            row = clean_record(raw)
            key = norm(row.get(consumer_ggrem, ""))
            if not key:
                continue
            if key in consumer_rows:
                consumer_duplicates += 1
                continue
            consumer_rows[key] = row

    if government_ggrem:
        for raw in government_df.to_dict(orient="records"):
            row = clean_record(raw)
            key = norm(row.get(government_ggrem, ""))
            if not key:
                continue
            if key in government_rows:
                government_duplicates += 1
                continue
            government_rows[key] = row

    keys = list(consumer_rows)
    keys.extend(key for key in government_rows if key not in consumer_rows)

    rows: list[dict[str, Any]] = []
    pf_mismatches = 0
    pf_comparable = 0
    invalid_presentation_registration = 0

    for ggrem in keys:
        consumer = consumer_rows.get(ggrem)
        government = government_rows.get(ggrem)
        base = consumer or government or {}

        registration_raw = _identity(base, "REGISTRO")
        presentation_registration, product_registration = _registration_parts(registration_raw)
        if len(presentation_registration) != 13:
            invalid_presentation_registration += 1

        consumer_pf = _extract_price_specs(consumer, consumer_pf_specs)
        government_pf = _extract_price_specs(government, government_pf_specs)
        consistency = _pf_consistent(consumer_pf, government_pf)
        if consistency is not None:
            pf_comparable += 1
            if not consistency:
                pf_mismatches += 1

        rows.append({
            "ggremCode": ggrem,
            "registrationNumber": registration_raw,
            "registrationNumberDigits": presentation_registration,
            "registrationBase": product_registration,
            "presentationRegistrationNumber": presentation_registration,
            "productRegistrationNumber": product_registration,
            "eans": _ean_values(base),
            "substance": _identity(base, "SUBSTÂNCIA"),
            "companyCnpj": digits(_identity(base, "CNPJ")),
            "laboratory": _identity(base, "LABORATÓRIO"),
            "product": _identity(base, "PRODUTO"),
            "presentation": _identity(base, "APRESENTAÇÃO"),
            "therapeuticClass": _identity(base, "CLASSE TERAPÊUTICA"),
            "productType": _identity(base, "TIPO DE PRODUTO (STATUS DO PRODUTO)"),
            "priceRegime": _identity(base, "REGIME DE PREÇO"),
            "hospitalRestriction": _identity(base, "RESTRIÇÃO HOSPITALAR"),
            "cap": _identity(base, "CAP"),
            "confaz87": _identity(base, "CONFAZ 87"),
            "icmsZero": _identity(base, "ICMS 0%"),
            "appealAnalysis": _identity(base, "ANÁLISE RECURSAL"),
            "taxCreditList": _identity(base, "LISTA DE CONCESSÃO DE CRÉDITO TRIBUTÁRIO (PIS/COFINS)"),
            "commercialization2025": _identity(base, "COMERCIALIZAÇÃO 2025"),
            "stripe": _identity(base, "TARJA"),
            "commercialDestination": _identity(base, "DESTINAÇÃO COMERCIAL"),
            "factoryPrices": consumer_pf or government_pf,
            "consumerPrices": _extract_price_specs(consumer, consumer_pmc_specs),
            "governmentPrices": _extract_price_specs(government, government_pmvg_specs),
            "governmentFactoryPriceMarkers": _extract_marker_specs(government, government_pf_specs),
            "factoryPriceConsistency": consistency,
            "sources": {
                "consumer": {
                    "available": consumer is not None,
                    "fileName": consumer_meta.fileName if consumer_meta else "",
                    "publicationDate": consumer_meta.publicationDate if consumer_meta else "",
                    "title": consumer_meta.title if consumer_meta else "",
                },
                "government": {
                    "available": government is not None,
                    "fileName": government_meta.fileName if government_meta else "",
                    "publicationDate": government_meta.publicationDate if government_meta else "",
                    "title": government_meta.title if government_meta else "",
                    "capRate": government_meta.capRate if government_meta else "",
                },
            },
        })

    consumer_keys = set(consumer_rows)
    government_keys = set(government_rows)
    presentation_regs = {
        row["presentationRegistrationNumber"]
        for row in rows
        if len(row["presentationRegistrationNumber"]) == 13
    }
    stats = {
        "consumerRows": len(consumer_df),
        "governmentRows": len(government_df),
        "consumerUniqueGgrem": len(consumer_keys),
        "governmentUniqueGgrem": len(government_keys),
        "mergedGgrem": len(rows),
        "overlapGgrem": len(consumer_keys & government_keys),
        "consumerOnlyGgrem": len(consumer_keys - government_keys),
        "governmentOnlyGgrem": len(government_keys - consumer_keys),
        "consumerDuplicateGgrem": consumer_duplicates,
        "governmentDuplicateGgrem": government_duplicates,
        "uniquePresentationRegistrations13": len(presentation_regs),
        "invalidPresentationRegistrationLength": invalid_presentation_registration,
        "pfComparableGgrem": pf_comparable,
        "pfMismatchGgrem": pf_mismatches,
        "strategy": (
            "outer merge econômico por CÓDIGO GGREM; REGISTRO de 13 dígitos identifica a apresentação; "
            "os 9 primeiros dígitos do REGISTRO identificam o medicamento"
        ),
    }
    return rows, stats


def index_cmed_by_registration(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Indexa registros econômicos CMED pelo registro de produto de 9 dígitos."""
    index: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = norm(row.get("productRegistrationNumber") or row.get("registrationBase"))
        if len(key) == 9:
            index.setdefault(key, []).append(row)
    return index
