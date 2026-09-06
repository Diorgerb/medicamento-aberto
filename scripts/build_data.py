#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import shutil
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cmed import CmedMetadata, consolidate_cmed, index_cmed_by_registration, read_cmed_csv
from common import clean_record, digits, dump_json, norm, norm_key, sha256_file, stable_id
from schemas import (
    BULA_DOCUMENTO_COLUMNS,
    BULA_DOCUMENTO_LINK,
    BULA_PRODUTO_COLUMNS,
    BULA_PRODUTO_LINK,
    CMED_TAX_BANDS,
    EXPECTED_FIELD_COUNTS,
    IRREGULAR_COLUMNS,
    MEDICINES_COLUMNS,
)
from source_registry import SOURCES, SourceDefinition

PIPELINE_VERSION = "4.0.0"
PROJECT_NAME = "Medicamento Aberto"
PROJECT_DESCRIPTION = "Plataforma integrada de dados abertos sobre medicamentos no Brasil."


def _load_json_if_exists(path: Path, fallback: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return fallback


def _related_value(record: dict[str, Any], columns: list[str], column: str) -> str:
    try:
        return norm(record.get("values", [])[columns.index(column)])
    except (ValueError, IndexError, TypeError):
        return ""


def _date_to_iso(value: str, order: str) -> str:
    text = norm(value)
    if not text:
        return ""
    for fmt in ({"mdy": "%m/%d/%Y %H:%M:%S", "dmy": "%d/%m/%Y %H:%M:%S"}.get(order, ""),
                {"mdy": "%m/%d/%Y", "dmy": "%d/%m/%Y"}.get(order, "")):
        if not fmt:
            continue
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue
    return ""


def _latest_related_date(records: list[dict[str, Any]], source: str, column: str) -> str:
    columns = BULA_PRODUTO_COLUMNS if source == "bula_produto" else (BULA_DOCUMENTO_COLUMNS if source == "bula_documento" else IRREGULAR_COLUMNS)
    values = [_date_to_iso(_related_value(record, columns, column), "mdy") for record in records]
    values = [value for value in values if value]
    return max(values, default="")


@dataclass(frozen=True)
class SourceInfo:
    key: str
    label: str
    fileName: str
    rows: int
    columns: int
    bytes: int
    sha256: str
    downloadUrl: str
    officialPageUrl: str
    catalogUrl: str
    organization: str
    layer: str
    publicationDate: str
    headerMode: str


def parse_company(value: Any) -> tuple[str, str]:
    text = norm(value)
    match = re.match(r"^\s*(\d{14})\s*-\s*(.*)$", text)
    return (match.group(1), match.group(2).strip()) if match else ("", text)


def normalize_registration(value: Any) -> str:
    return digits(value)


def product_seed(row: dict[str, Any]) -> str:
    registration = normalize_registration(row.get("NUMERO_REGISTRO_PRODUTO"))
    if len(registration) == 9:
        return f"registro:{registration}"
    # Produtos sem número de registro NÃO são fundidos por nome/empresa/categoria.
    # Depois da remoção das duplicatas exatas, cada linha distinta é uma entidade lógica.
    payload = "|".join(norm(row.get(column, "")) for column in MEDICINES_COLUMNS)
    return "linha-sem-registro:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def product_id(row: dict[str, Any]) -> str:
    return stable_id("med", product_seed(row))


def _find_source(input_dir: Path, definition: SourceDefinition) -> Path | None:
    files = {path.name.lower(): path for path in input_dir.iterdir() if path.is_file()}
    for filename in definition.filenames:
        hit = files.get(filename.lower())
        if hit:
            return hit
    return None


def _read_headered_exact(path: Path, expected_columns: list[str]) -> pd.DataFrame:
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            frame = pd.read_csv(
                path,
                sep=";",
                encoding=encoding,
                dtype=str,
                keep_default_na=False,
                low_memory=False,
            )
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")
            continue
        frame.columns = [str(column).replace("\ufeff", "").strip() for column in frame.columns]
        missing = [column for column in expected_columns if column not in frame.columns]
        if not missing:
            # Mantém apenas as colunas do esquema conhecido e na ordem publicada.
            return frame[expected_columns].copy()
        errors.append(f"{encoding}: ausentes {', '.join(missing[:8])}")
    raise RuntimeError(
        f"Esquema inesperado em {path.name}. "
        f"Esperado literalmente: {', '.join(expected_columns)}. "
        f"Tentativas: {' | '.join(errors[-4:])}"
    )


def _read_positional(path: Path, columns: list[str]) -> pd.DataFrame:
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            frame = pd.read_csv(
                path,
                sep=";",
                encoding=encoding,
                header=None,
                names=columns,
                dtype=str,
                keep_default_na=False,
                low_memory=False,
                quoting=csv.QUOTE_MINIMAL,
            )
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")
            continue
        if len(frame.columns) == len(columns):
            return frame
    raise RuntimeError(f"Não foi possível ler {path.name} como CSV posicional: {' | '.join(errors[-4:])}")


def _row_values(row: dict[str, Any], columns: Iterable[str]) -> list[str]:
    return [norm(row.get(column, "")) for column in columns]


def _related(source_key: str, method: str, value: str, row: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    return {
        "sourceKey": source_key,
        "matchMethod": method,
        "matchValue": value,
        "values": _row_values(row, columns),
    }


def _dedupe_related(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        payload = json.dumps([record["sourceKey"], record["values"]], ensure_ascii=False, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if digest not in seen:
            seen.add(digest)
            out.append(record)
    return out


def _price_array(mapping: dict[str, str]) -> list[str]:
    return [norm(mapping.get(band, "")) for band in CMED_TAX_BANDS]


def _marker_array(mapping: dict[str, str]) -> list[str]:
    return [norm(mapping.get(band, "")) for band in CMED_TAX_BANDS]


def compact_cmed(row: dict[str, Any]) -> dict[str, Any]:
    """Representação compacta: nomes das 26 faixas ficam no dicionário global, não repetidos em cada GGREM."""
    return {
        "ggremCode": norm(row.get("ggremCode")),
        "registrationNumber": norm(row.get("registrationNumber")),
        "registrationBase": norm(row.get("registrationBase")),
        "presentationRegistrationNumber": norm(row.get("presentationRegistrationNumber")),
        "productRegistrationNumber": norm(row.get("productRegistrationNumber")),
        "eans": row.get("eans") or [],
        "substance": norm(row.get("substance")),
        "companyCnpj": norm(row.get("companyCnpj")),
        "laboratory": norm(row.get("laboratory")),
        "product": norm(row.get("product")),
        "presentation": norm(row.get("presentation")),
        "therapeuticClass": norm(row.get("therapeuticClass")),
        "productType": norm(row.get("productType")),
        "priceRegime": norm(row.get("priceRegime")),
        "hospitalRestriction": norm(row.get("hospitalRestriction")),
        "cap": norm(row.get("cap")),
        "confaz87": norm(row.get("confaz87")),
        "icmsZero": norm(row.get("icmsZero")),
        "appealAnalysis": norm(row.get("appealAnalysis")),
        "taxCreditList": norm(row.get("taxCreditList")),
        "commercialization2025": norm(row.get("commercialization2025")),
        "stripe": norm(row.get("stripe")),
        "commercialDestination": norm(row.get("commercialDestination")),
        "factoryPrices": _price_array(row.get("factoryPrices") or {}),
        "consumerPrices": _price_array(row.get("consumerPrices") or {}),
        "governmentPrices": _price_array(row.get("governmentPrices") or {}),
        "governmentFactoryPriceMarkers": _marker_array(row.get("governmentFactoryPriceMarkers") or {}),
        "factoryPriceConsistency": row.get("factoryPriceConsistency"),
    }


def _merge_unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        value = norm(value)
        if value and value not in out:
            out.append(value)
    return out


def group_presentations(cmed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa os registros econômicos por apresentação de 13 dígitos.

    REGISTRO (13 dígitos) = apresentação comercializada.
    REGISTRO[:9] = medicamento/produto.
    CÓDIGO GGREM = identificador do registro econômico CMED, não da apresentação.
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cmed_rows:
        registration = norm(row.get("presentationRegistrationNumber"))
        if len(registration) == 13:
            grouped[registration].append(row)

    presentations: list[dict[str, Any]] = []
    for registration, rows in grouped.items():
        base = rows[0]
        descriptions = _merge_unique(row.get("presentation", "") for row in rows)
        products = _merge_unique(row.get("product", "") for row in rows)
        substances = _merge_unique(row.get("substance", "") for row in rows)
        laboratories = _merge_unique(row.get("laboratory", "") for row in rows)
        classes = _merge_unique(row.get("therapeuticClass", "") for row in rows)
        product_types = _merge_unique(row.get("productType", "") for row in rows)
        restrictions = _merge_unique(row.get("hospitalRestriction", "") for row in rows)
        commercialization = _merge_unique(row.get("commercialization2025", "") for row in rows)
        stripes = _merge_unique(row.get("stripe", "") for row in rows)
        destinations = _merge_unique(row.get("commercialDestination", "") for row in rows)
        eans: list[str] = []
        for row in rows:
            for ean in row.get("eans") or []:
                if ean and ean not in eans:
                    eans.append(ean)
        presentations.append({
            "registrationNumber": registration,
            "productRegistrationNumber": registration[:9],
            "description": descriptions[0] if descriptions else "",
            "descriptions": descriptions,
            "eans": eans,
            "ggremCodes": _merge_unique(row.get("ggremCode", "") for row in rows),
            "product": products[0] if products else "",
            "substance": substances[0] if substances else "",
            "companyCnpj": norm(base.get("companyCnpj")),
            "laboratory": laboratories[0] if laboratories else "",
            "therapeuticClass": classes[0] if classes else "",
            "productType": product_types[0] if product_types else "",
            "hospitalRestriction": restrictions[0] if restrictions else "",
            "commercialization2025": commercialization[0] if commercialization else "",
            "stripe": stripes[0] if stripes else "",
            "commercialDestination": destinations[0] if destinations else "",
            "economicRecordCount": len(rows),
        })
    presentations.sort(key=lambda row: (row["productRegistrationNumber"], row["registrationNumber"]))
    return presentations


def index_presentations_by_product(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        product_registration = norm(row.get("productRegistrationNumber"))
        if len(product_registration) == 9:
            index[product_registration].append(row)
    return index


def _write_gzip_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8-sig", newline="", compresslevel=6) as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


class Builder:
    def __init__(self, input_dir: Path, output_dir: Path) -> None:
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.sources: dict[str, pd.DataFrame] = {}
        self.source_info: dict[str, SourceInfo] = {}
        self.cmed_metadata: dict[str, CmedMetadata | None] = {"cmed_consumidor": None, "cmed_governo": None}
        self.schema_report: dict[str, Any] = {
            "pipelineVersion": PIPELINE_VERSION,
            "scope": "Exclusivamente os seis CSVs listados em source_registry.py",
            "sources": {},
            "relationships": {},
            "warnings": [],
        }

    def load_sources(self) -> None:
        for definition in SOURCES:
            path = _find_source(self.input_dir, definition)
            if path is None:
                raise FileNotFoundError(
                    f"Fonte obrigatória ausente: {definition.label}. "
                    f"Aceitos: {', '.join(definition.filenames)}"
                )
            print(f"[LOAD] {definition.key}: {path.name}")
            publication = ""
            if definition.key in {"cmed_consumidor", "cmed_governo"}:
                frame, meta = read_cmed_csv(path)
                if len(frame.columns) != EXPECTED_FIELD_COUNTS[definition.key]:
                    raise RuntimeError(
                        f"{path.name}: esperado {EXPECTED_FIELD_COUNTS[definition.key]} colunas após o preâmbulo; encontrado {len(frame.columns)}."
                    )
                self.cmed_metadata[definition.key] = meta
                publication = meta.publicationDate
            elif definition.key == "medicamentos":
                frame = _read_headered_exact(path, MEDICINES_COLUMNS)
            elif definition.key == "irregulares":
                frame = _read_headered_exact(path, IRREGULAR_COLUMNS)
            elif definition.key == "bula_produto":
                frame = _read_positional(path, BULA_PRODUTO_COLUMNS)
            elif definition.key == "bula_documento":
                frame = _read_positional(path, BULA_DOCUMENTO_COLUMNS)
            else:
                raise RuntimeError(definition.key)

            self.sources[definition.key] = frame
            info = SourceInfo(
                key=definition.key,
                label=definition.label,
                fileName=path.name,
                rows=len(frame),
                columns=len(frame.columns),
                bytes=path.stat().st_size,
                sha256=sha256_file(path),
                downloadUrl=definition.download_url,
                officialPageUrl=definition.official_page_url,
                catalogUrl=definition.catalog_url,
                organization=definition.organization,
                layer=definition.layer,
                publicationDate=publication,
                headerMode=definition.header_mode,
            )
            self.source_info[definition.key] = info
            self.schema_report["sources"][definition.key] = {
                "file": path.name,
                "rows": len(frame),
                "columnCount": len(frame.columns),
                "columns": list(map(str, frame.columns)),
                "headerMode": definition.header_mode,
                "sha256": info.sha256,
                "publicationDate": publication,
            }

    def prepare_output(self) -> None:
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        for part in ("catalog", "products", "downloads"):
            (self.output_dir / part).mkdir(parents=True, exist_ok=True)

    def deterministic_version(self) -> str:
        payload = f"pipeline:{PIPELINE_VERSION}|" + "|".join(
            f"{key}:{info.sha256}" for key, info in sorted(self.source_info.items())
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def source_catalog(self) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        source_by_key = {source.key: source for source in SOURCES}
        for key, info in self.source_info.items():
            definition = source_by_key[key]
            item = definition.public_dict()
            item.update({
                "detected": True,
                "fileName": info.fileName,
                "rows": info.rows,
                "columns": info.columns,
                "bytes": info.bytes,
                "sha256": info.sha256,
                "publicationDate": info.publicationDate,
            })
            output.append(item)
        return output

    def leaflet_indexes(self, medicines: pd.DataFrame) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
        """Cria índices do Bulário separando estado atual e histórico.

        TA_CONSULTA_BULA_PRODUTO = última atualização conhecida do produto no Bulário.
        TA_CONSULTA_BULA_DOCUMENTO = histórico de atualizações/documentos do processo.
        """
        bp = self.sources["bula_produto"]
        bd = self.sources["bula_documento"]
        latest_by_reg: dict[str, list[dict[str, Any]]] = defaultdict(list)
        latest_by_process: dict[str, list[dict[str, Any]]] = defaultdict(list)
        history_by_process: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for raw in bp.to_dict(orient="records"):
            row = clean_record(raw)
            registration = digits(row[BULA_PRODUTO_LINK["registration"]])
            process = digits(row[BULA_PRODUTO_LINK["process"]])
            if len(registration) == 9:
                latest_by_reg[registration].append(_related(
                    "bula_produto",
                    "NUMERO_REGISTRO_PRODUTO = NUMERO_REGISTRO_PRODUTO",
                    registration,
                    row,
                    BULA_PRODUTO_COLUMNS,
                ))
            if process:
                latest_by_process[process].append(_related(
                    "bula_produto",
                    "NUMERO_PROCESSO = NUMERO_PROCESSO",
                    process,
                    row,
                    BULA_PRODUTO_COLUMNS,
                ))

        for raw in bd.to_dict(orient="records"):
            row = clean_record(raw)
            process = digits(row[BULA_DOCUMENTO_LINK["process"]])
            if process:
                history_by_process[process].append(_related(
                    "bula_documento",
                    "NUMERO_PROCESSO = NUMERO_PROCESSO",
                    process,
                    row,
                    BULA_DOCUMENTO_COLUMNS,
                ))

        known_regs = {digits(v) for v in medicines["NUMERO_REGISTRO_PRODUTO"] if digits(v)}
        known_proc = {digits(v) for v in medicines["NUMERO_PROCESSO"] if digits(v)}
        bp_regs = [digits(v) for v in bp[BULA_PRODUTO_LINK["registration"]] if digits(v)]
        bp_proc = [digits(v) for v in bp[BULA_PRODUTO_LINK["process"]] if digits(v)]
        bd_proc = [digits(v) for v in bd[BULA_DOCUMENTO_LINK["process"]] if digits(v)]

        # Valida também a correspondência 1:1 entre o registro atual e o histórico.
        bd_ids = set(norm(v) for v in bd[BULA_DOCUMENTO_LINK["document_id"]] if norm(v))
        bd_exp = set(norm(v) for v in bd[BULA_DOCUMENTO_LINK["expedient"]] if norm(v))
        bd_trans = set(norm(v) for v in bd[BULA_DOCUMENTO_LINK["transaction"]] if norm(v))
        bd_update_dates = set(norm(v) for v in bd[BULA_DOCUMENTO_LINK["update_date"]] if norm(v))
        bp_ids = [norm(v) for v in bp[BULA_PRODUTO_LINK["document_id"]] if norm(v)]
        bp_exp = [norm(v) for v in bp[BULA_PRODUTO_LINK["expedient"]] if norm(v)]
        bp_trans = [norm(v) for v in bp[BULA_PRODUTO_LINK["transaction"]] if norm(v)]
        bp_update_dates = [norm(v) for v in bp[BULA_PRODUTO_LINK["update_date"]] if norm(v)]

        stats = {
            "header": {"bula_produto": False, "bula_documento": False},
            "columnNaming": (
                "Os CSVs de bula não contêm cabeçalho. Os nomes funcionais usados pelo Medicamento Aberto "
                "foram definidos a partir da estrutura e de correspondências verificadas entre os próprios arquivos."
            ),
            "semantics": {
                "bula_produto": "Última atualização do produto no Bulário Eletrônico da Anvisa.",
                "bula_documento": "Histórico de atualizações/documentos do Bulário Eletrônico da Anvisa.",
            },
            "verifiedLinks": {
                "bula_produto.NUMERO_REGISTRO_PRODUTO -> medicamentos.NUMERO_REGISTRO_PRODUTO": {
                    "nonEmpty": len(bp_regs), "matchingValues": sum(v in known_regs for v in bp_regs)
                },
                "bula_produto.NUMERO_PROCESSO -> medicamentos.NUMERO_PROCESSO": {
                    "nonEmpty": len(bp_proc), "matchingValues": sum(v in known_proc for v in bp_proc)
                },
                "bula_documento.NUMERO_PROCESSO -> medicamentos.NUMERO_PROCESSO": {
                    "nonEmpty": len(bd_proc), "matchingValues": sum(v in known_proc for v in bd_proc)
                },
                "bula_produto.ID_DOCUMENTO_ATUAL -> bula_documento.ID_DOCUMENTO": {
                    "nonEmpty": len(bp_ids), "matchingValues": sum(v in bd_ids for v in bp_ids)
                },
                "bula_produto.NUMERO_EXPEDIENTE_ATUAL -> bula_documento.NUMERO_EXPEDIENTE": {
                    "nonEmpty": len(bp_exp), "matchingValues": sum(v in bd_exp for v in bp_exp)
                },
                "bula_produto.NUMERO_TRANSACAO_ATUAL -> bula_documento.NUMERO_TRANSACAO": {
                    "nonEmpty": len(bp_trans), "matchingValues": sum(v in bd_trans for v in bp_trans)
                },
                "bula_produto.DATA_ULTIMA_ATUALIZACAO_BULARIO -> bula_documento.DATA_ATUALIZACAO_BULARIO": {
                    "nonEmpty": len(bp_update_dates), "matchingValues": sum(v in bd_update_dates for v in bp_update_dates)
                },
            },
        }
        return latest_by_reg, latest_by_process, history_by_process, stats

    def irregular_index(self) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
        frame = self.sources["irregulares"]
        output: dict[str, list[dict[str, Any]]] = defaultdict(list)
        nonempty = 0
        exact_nine = 0
        ignored: dict[int, int] = defaultdict(int)
        for raw in frame.to_dict(orient="records"):
            row = clean_record(raw)
            registration = digits(row.get("REGISTRO"))
            if not registration:
                continue
            nonempty += 1
            if len(registration) != 9:
                ignored[len(registration)] += 1
                continue
            exact_nine += 1
            output[registration].append(_related(
                "irregulares",
                "REGISTRO = NUMERO_REGISTRO_PRODUTO (9 dígitos exatos)",
                registration,
                row,
                IRREGULAR_COLUMNS,
            ))
        return output, {
            "registrationColumn": "REGISTRO",
            "nonEmptyRegistrationRows": nonempty,
            "nineDigitRegistrationRows": exact_nine,
            "ignoredOtherRegistrationLengths": dict(sorted(ignored.items())),
            "strategy": "Igualdade exata de 9 dígitos; valores de 11 dígitos não são truncados.",
            "note": "Ausência de ocorrência não é interpretada como comprovação de regularidade.",
        }

    def build(self) -> None:
        previous_catalog = _load_json_if_exists(self.output_dir / "catalog" / "products.json", [])
        previous_manifest = _load_json_if_exists(self.output_dir / "manifest.json", {})
        self.load_sources()
        medicines_source = self.sources["medicamentos"]
        duplicate_count = int(medicines_source.duplicated().sum())
        medicines = medicines_source.drop_duplicates().reset_index(drop=True)

        product_rows: dict[str, dict[str, Any]] = {}
        for raw in medicines.to_dict(orient="records"):
            row = clean_record(raw)
            pid = product_id(row)
            if pid in product_rows and product_rows[pid] != row:
                raise RuntimeError(
                    f"Mais de uma linha distinta foi encontrada para a mesma identidade de produto {pid}. "
                    "O pipeline bloqueou a consolidação para não escolher valores arbitrariamente."
                )
            product_rows[pid] = row

        registration_lengths: dict[int, int] = defaultdict(int)
        registered = 0
        for row in product_rows.values():
            registration = digits(row["NUMERO_REGISTRO_PRODUTO"])
            registration_lengths[len(registration)] += 1
            if len(registration) == 9:
                registered += 1
        without_valid_registration = len(product_rows) - registered
        malformed_registration = sum(
            count for length, count in registration_lengths.items() if length not in (0, 9)
        )

        print(f"[BASE] linhas fonte: {len(medicines_source):,}")
        print(f"[BASE] duplicatas exatas removidas: {duplicate_count:,}")
        print(
            f"[BASE] produtos lógicos: {len(product_rows):,} "
            f"(registro de 9 dígitos={registered:,}; sem registro válido de 9 dígitos={without_valid_registration:,})"
        )
        if malformed_registration:
            print(f"[BASE] registros informados com comprimento diferente de 9: {malformed_registration:,} (preservados, sem vínculo)")
        self.prepare_output()

        # CMED: GGREM = registro econômico; REGISTRO de 13 dígitos = apresentação; primeiros 9 = produto.
        cmed_full, cmed_stats = consolidate_cmed(
            self.sources["cmed_consumidor"],
            self.sources["cmed_governo"],
            self.cmed_metadata["cmed_consumidor"],
            self.cmed_metadata["cmed_governo"],
        )
        cmed_compact = [compact_cmed(row) for row in cmed_full]
        cmed_by_registration = index_cmed_by_registration(cmed_compact)
        presentations_all = group_presentations(cmed_compact)
        presentations_by_product = index_presentations_by_product(presentations_all)
        self.schema_report["relationships"]["cmed"] = cmed_stats

        leaf_latest_by_reg, leaf_latest_by_process, leaf_history_by_process, leaf_stats = self.leaflet_indexes(medicines)
        self.schema_report["relationships"]["leaflets"] = leaf_stats
        irregular_by_reg, irregular_stats = self.irregular_index()
        self.schema_report["relationships"]["irregularities"] = irregular_stats

        products_catalog: list[dict[str, Any]] = []
        product_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        companies: dict[str, dict[str, Any]] = {}
        ingredients: dict[str, dict[str, Any]] = {}

        product_registration_to_pid: dict[str, str] = {}
        for pid, row in product_rows.items():
            registration = digits(row["NUMERO_REGISTRO_PRODUTO"])
            if len(registration) == 9:
                if registration in product_registration_to_pid and product_registration_to_pid[registration] != pid:
                    raise RuntimeError(f"Registro de produto duplicado após deduplicação: {registration}")
                product_registration_to_pid[registration] = pid

        linked_ggrem = {
            row["ggremCode"]
            for row in cmed_compact
            if len(row.get("productRegistrationNumber", "")) == 9
            and row["productRegistrationNumber"] in product_registration_to_pid
            and row.get("ggremCode")
        }
        linked_presentation_regs = {
            row["registrationNumber"]
            for row in presentations_all
            if row["productRegistrationNumber"] in product_registration_to_pid
        }

        products_with_cmed = products_with_leaflet = products_with_leaflet_history = products_with_alert = 0
        products_without_company = products_without_ingredient = 0
        medicines_export: list[dict[str, Any]] = []

        for pid, row in product_rows.items():
            registration_raw = norm(row["NUMERO_REGISTRO_PRODUTO"])
            registration_digits = digits(registration_raw)
            valid_registration = registration_digits if len(registration_digits) == 9 else ""
            process_raw = norm(row["NUMERO_PROCESSO"])
            process = digits(process_raw)
            cnpj, company_name = parse_company(row["EMPRESA_DETENTORA_REGISTRO"])
            company_id = stable_id("emp", cnpj or company_name) if (cnpj or company_name) else ""
            name = norm(row["NOME_PRODUTO"]) or "Medicamento sem nome informado"
            ingredient = norm(row["PRINCIPIO_ATIVO"])
            active_ingredients = [ingredient] if ingredient else []
            category = norm(row["CATEGORIA_REGULATORIA"])
            status = norm(row["SITUACAO_REGISTRO"])
            cmed_rows = cmed_by_registration.get(valid_registration, []) if valid_registration else []
            presentation_rows = presentations_by_product.get(valid_registration, []) if valid_registration else []

            leaflet_latest: list[dict[str, Any]] = []
            if valid_registration:
                leaflet_latest.extend(leaf_latest_by_reg.get(valid_registration, []))
            if process:
                leaflet_latest.extend(leaf_latest_by_process.get(process, []))
            leaflet_latest = _dedupe_related(leaflet_latest)

            leaflet_history: list[dict[str, Any]] = []
            if process:
                leaflet_history.extend(leaf_history_by_process.get(process, []))
            leaflet_history = _dedupe_related(leaflet_history)
            alerts = _dedupe_related(irregular_by_reg.get(valid_registration, [])) if valid_registration else []
            leaflet_latest_date = _latest_related_date(leaflet_latest, "bula_produto", "DATA_ULTIMA_ATUALIZACAO_BULARIO")
            latest_alert_date = max(
                _latest_related_date(alerts, "irregulares", "DT_PUBLICACAO_MEDIDA"),
                _latest_related_date(alerts, "irregulares", "DT_PUBLICACAO"),
            )

            products_with_cmed += bool(cmed_rows)
            products_with_leaflet += bool(leaflet_latest)
            products_with_leaflet_history += bool(leaflet_history)
            products_with_alert += bool(alerts)
            products_without_company += not bool(cnpj or company_name)
            products_without_ingredient += not bool(ingredient)

            if company_id:
                company = companies.setdefault(company_id, {
                    "id": company_id,
                    "name": company_name,
                    "cnpj": cnpj,
                    "products": set(),
                    "presentations": 0,
                })
                company["products"].add(pid)
                company["presentations"] += len(presentation_rows)

            if ingredient:
                iid = stable_id("ifa", ingredient)
                item = ingredients.setdefault(iid, {"id": iid, "name": ingredient, "products": set(), "companies": set()})
                item["products"].add(pid)
                if company_id:
                    item["companies"].add(company_id)

            bucket = hashlib.sha256(pid.encode("utf-8")).hexdigest()[:2]
            detail = {
                "id": pid,
                "bucket": bucket,
                "name": name,
                "processFinalizationDate": norm(row["DATA_FINALIZACAO_PROCESSO"]),
                "regulatoryCategory": category,
                "registrationNumber": registration_raw,
                "registrationNumberDigits": registration_digits,
                "validProductRegistration": bool(valid_registration),
                "registrationExpiry": norm(row["DATA_VENCIMENTO_REGISTRO"]),
                "processNumber": process_raw,
                "therapeuticClass": norm(row["CLASSE_TERAPEUTICA"]),
                "companyId": company_id,
                "companyName": company_name,
                "companyCnpj": cnpj,
                "status": status,
                "activeIngredients": active_ingredients,
                "presentations": presentation_rows,
                "cmed": cmed_rows,
                "leafletLatest": leaflet_latest,
                "leafletHistory": leaflet_history,
                "alerts": alerts,
                "sourceLayers": {
                    "registration": True,
                    "presentations": bool(presentation_rows),
                    "cmed": bool(cmed_rows),
                    "leaflets": bool(leaflet_latest or leaflet_history),
                    "inspection": bool(alerts),
                },
                "rawValues": _row_values(row, MEDICINES_COLUMNS),
            }
            product_buckets[bucket].append(detail)

            products_catalog.append({
                "id": pid,
                "bucket": bucket,
                "name": name,
                "registrationNumber": registration_raw,
                "registrationNumberDigits": registration_digits,
                "validProductRegistration": bool(valid_registration),
                "regulatoryCategory": category,
                "activeIngredients": active_ingredients,
                "companyId": company_id,
                "companyName": company_name,
                "companyCnpj": cnpj,
                "processNumber": process_raw,
                "status": status,
                "presentationCount": len(presentation_rows),
                "hasLeaflet": bool(leaflet_latest),
                "hasLeafletHistory": bool(leaflet_history),
                "hasCmed": bool(cmed_rows),
                "hasAlert": bool(alerts),
                "leafletLatestDate": leaflet_latest_date,
                "latestAlertDate": latest_alert_date,
            })

            medicines_export.append({
                "ID_MEDICAMENTO_ABERTO": pid,
                **{column: row[column] for column in MEDICINES_COLUMNS},
                "REGISTRO_PRODUTO_9_VALIDO": valid_registration,
                "CNPJ_EMPRESA": cnpj,
                "RAZAO_SOCIAL_EMPRESA": company_name,
                "QTD_APRESENTACOES_COMERCIALIZADAS": len(presentation_rows),
                "QTD_REGISTROS_ECONOMICOS_CMED": len(cmed_rows),
                "POSSUI_BULA_ATUAL_NO_BULARIO": "SIM" if leaflet_latest else "NÃO",
                "POSSUI_HISTORICO_BULA": "SIM" if leaflet_history else "NÃO",
                "POSSUI_PRECO_PUBLICADO_CMED": "SIM" if cmed_rows else "NÃO",
                "POSSUI_OCORRENCIA_FISCALIZACAO": "SIM" if alerts else "NÃO",
            })

        products_catalog.sort(key=lambda x: (norm_key(x["name"]), x["registrationNumberDigits"], x["id"]))
        companies_catalog = [
            {
                "id": item["id"],
                "name": item["name"],
                "cnpj": item["cnpj"],
                "authorization": "",
                "productCount": len(item["products"]),
                "presentationCount": item["presentations"],
            }
            for item in companies.values()
        ]
        companies_catalog.sort(key=lambda x: norm_key(x["name"]))
        ingredients_catalog = [
            {
                "id": item["id"],
                "name": item["name"],
                "productCount": len(item["products"]),
                "companyCount": len(item["companies"]),
            }
            for item in ingredients.values()
        ]
        ingredients_catalog.sort(key=lambda x: norm_key(x["name"]))

        for bucket, rows in product_buckets.items():
            rows.sort(key=lambda x: (norm_key(x["name"]), x["registrationNumberDigits"], x["id"]))
            dump_json(self.output_dir / "products" / f"{bucket}.json", rows)

        current_version = self.deterministic_version()
        previous_by_id = {item.get("id"): item for item in previous_catalog if item.get("id")}
        changes: list[dict[str, Any]] = []
        recent_events: list[dict[str, Any]] = []

        def activity_event(item: dict[str, Any], event_type: str, date: str, title: str, description: str, source_label: str, detected: bool) -> dict[str, Any]:
            token = f"{item['id']}|{event_type}|{date}|{title}|{description}"
            return {
                "id": hashlib.sha256(token.encode("utf-8")).hexdigest()[:20],
                "type": event_type,
                "productId": item["id"],
                "bucket": item["bucket"],
                "productName": item["name"],
                "registrationNumber": item["registrationNumber"],
                "status": item["status"],
                "date": date,
                "title": title,
                "description": description,
                "sourceLabel": source_label,
                "detectedChange": detected,
            }

        for item in products_catalog:
            if item.get("leafletLatestDate"):
                recent_events.append(activity_event(item, "leaflet", item["leafletLatestDate"], "Atualização no Bulário", "Foi localizada uma atualização recente no Bulário Eletrônico.", "Bulário Eletrônico", False))
            if item.get("latestAlertDate"):
                recent_events.append(activity_event(item, "inspection", item["latestAlertDate"], "Publicação de fiscalização", "Foi localizada uma publicação de fiscalização relacionada ao medicamento.", "Fiscalização sanitária", False))

            previous = previous_by_id.get(item["id"])
            if not previous_catalog:
                continue
            if previous is None:
                changes.append(activity_event(item, "new", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), "Medicamento incluído na base integrada", "O medicamento não estava presente na publicação anterior.", "Base integrada", True))
                continue
            if norm(previous.get("status")) != norm(item.get("status")):
                changes.append(activity_event(item, "registration", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), "Situação do registro alterada", f"{norm(previous.get('status')) or 'Não informado'} → {norm(item.get('status')) or 'Não informado'}", "Regularização", True))
            old_count, new_count = int(previous.get("presentationCount") or 0), int(item.get("presentationCount") or 0)
            if old_count != new_count:
                changes.append(activity_event(item, "presentation", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), "Apresentações comercializadas alteradas", f"{old_count} → {new_count} apresentação(ões)", "Apresentações", True))
            if bool(previous.get("hasCmed")) != bool(item.get("hasCmed")):
                desc = "Passou a possuir preço publicado na lista da CMED." if item.get("hasCmed") else "Deixou de possuir preço publicado na lista da CMED atual."
                changes.append(activity_event(item, "cmed", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), "Presença na lista da CMED alterada", desc, "CMED", True))
            if previous.get("leafletLatestDate") and item.get("leafletLatestDate") and previous.get("leafletLatestDate") != item.get("leafletLatestDate"):
                changes.append(activity_event(item, "leaflet", item["leafletLatestDate"], "Nova atualização no Bulário", "A data da última atualização no Bulário mudou desde a publicação anterior.", "Bulário Eletrônico", True))
            if "latestAlertDate" in previous and previous.get("latestAlertDate") != item.get("latestAlertDate") and item.get("latestAlertDate"):
                changes.append(activity_event(item, "inspection", item["latestAlertDate"], "Nova publicação de fiscalização", "Uma publicação de fiscalização mais recente foi identificada desde a publicação anterior.", "Fiscalização sanitária", True))

        recent_events.sort(key=lambda event: event.get("date", ""), reverse=True)
        changes.sort(key=lambda event: event.get("date", ""), reverse=True)
        recent_events = recent_events[:500]
        changes = changes[:1000]
        activity_counts = defaultdict(int)
        for event in recent_events:
            activity_counts[event["type"]] += 1
        dump_json(self.output_dir / "catalog" / "activity.json", {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "previousVersion": previous_manifest.get("dataVersion", ""),
            "currentVersion": current_version,
            "hasPreviousSnapshot": bool(previous_catalog),
            "changes": changes,
            "recentEvents": recent_events,
            "counts": dict(activity_counts),
        }, pretty=True)
        dump_json(self.output_dir / "catalog" / "products.json", products_catalog)
        dump_json(self.output_dir / "catalog" / "companies.json", companies_catalog)
        dump_json(self.output_dir / "catalog" / "ingredients.json", ingredients_catalog)
        dump_json(self.output_dir / "catalog" / "sources.json", self.source_catalog(), pretty=True)

        # Uma linha por apresentação de 13 dígitos. GGREM(s) ficam associados à apresentação.
        presentations_export: list[dict[str, Any]] = []
        for presentation in presentations_all:
            product_registration = presentation["productRegistrationNumber"]
            pid = product_registration_to_pid.get(product_registration, "")
            product_row = product_rows.get(pid) if pid else None
            presentations_export.append({
                "ID_MEDICAMENTO_ABERTO": pid,
                "NOME_PRODUTO_BASE": norm(product_row["NOME_PRODUTO"]) if product_row else "",
                "REGISTRO_PRODUTO_9": product_registration,
                "REGISTRO_APRESENTACAO_13": presentation["registrationNumber"],
                "CÓDIGOS_GGREM": " | ".join(presentation["ggremCodes"]),
                "APRESENTAÇÃO": presentation["description"],
                "EAN": " | ".join(presentation["eans"]),
                "LABORATÓRIO": presentation["laboratory"],
                "SUBSTÂNCIA": presentation["substance"],
                "CLASSE TERAPÊUTICA": presentation["therapeuticClass"],
                "TIPO DE PRODUTO (STATUS DO PRODUTO)": presentation["productType"],
                "RESTRIÇÃO HOSPITALAR": presentation["hospitalRestriction"],
                "COMERCIALIZAÇÃO 2025": presentation["commercialization2025"],
                "TARJA": presentation["stripe"],
                "DESTINAÇÃO COMERCIAL": presentation["commercialDestination"],
                "QTD_REGISTROS_ECONOMICOS_GGREM": presentation["economicRecordCount"],
            })

        _write_gzip_csv(
            self.output_dir / "downloads" / "medicamentos.csv.gz",
            medicines_export,
            [
                "ID_MEDICAMENTO_ABERTO", *MEDICINES_COLUMNS, "REGISTRO_PRODUTO_9_VALIDO",
                "CNPJ_EMPRESA", "RAZAO_SOCIAL_EMPRESA", "QTD_APRESENTACOES_COMERCIALIZADAS",
                "QTD_REGISTROS_ECONOMICOS_CMED", "POSSUI_BULA_ATUAL_NO_BULARIO",
                "POSSUI_HISTORICO_BULA", "POSSUI_PRECO_PUBLICADO_CMED",
                "POSSUI_OCORRENCIA_FISCALIZACAO",
            ],
        )
        _write_gzip_csv(
            self.output_dir / "downloads" / "apresentacoes-comercializadas.csv.gz",
            presentations_export,
            [
                "ID_MEDICAMENTO_ABERTO", "NOME_PRODUTO_BASE", "REGISTRO_PRODUTO_9",
                "REGISTRO_APRESENTACAO_13", "CÓDIGOS_GGREM", "APRESENTAÇÃO", "EAN",
                "LABORATÓRIO", "SUBSTÂNCIA", "CLASSE TERAPÊUTICA",
                "TIPO DE PRODUTO (STATUS DO PRODUTO)", "RESTRIÇÃO HOSPITALAR",
                "COMERCIALIZAÇÃO 2025", "TARJA", "DESTINAÇÃO COMERCIAL",
                "QTD_REGISTROS_ECONOMICOS_GGREM",
            ],
        )

        cmed_export = [
            {
                "CÓDIGO GGREM": r["ggremCode"],
                "REGISTRO_APRESENTACAO_13": r["presentationRegistrationNumber"],
                "REGISTRO_PRODUTO_9": r["productRegistrationNumber"],
                "REGISTRO_ORIGINAL": r["registrationNumber"],
                "EAN": " | ".join(r["eans"]),
                "SUBSTÂNCIA": r["substance"],
                "CNPJ": r["companyCnpj"],
                "LABORATÓRIO": r["laboratory"],
                "PRODUTO": r["product"],
                "APRESENTAÇÃO": r["presentation"],
                "CLASSE TERAPÊUTICA": r["therapeuticClass"],
                "TIPO DE PRODUTO (STATUS DO PRODUTO)": r["productType"],
                "REGIME DE PREÇO": r["priceRegime"],
                "RESTRIÇÃO HOSPITALAR": r["hospitalRestriction"],
                "CAP": r["cap"],
                "CONFAZ 87": r["confaz87"],
                "ICMS 0%": r["icmsZero"],
                "ANÁLISE RECURSAL": r["appealAnalysis"],
                "LISTA DE CONCESSÃO DE CRÉDITO TRIBUTÁRIO (PIS/COFINS)": r["taxCreditList"],
                "COMERCIALIZAÇÃO 2025": r["commercialization2025"],
                "TARJA": r["stripe"],
                "DESTINAÇÃO COMERCIAL": r["commercialDestination"],
                "PF_JSON": json.dumps(dict(zip(CMED_TAX_BANDS, r["factoryPrices"])), ensure_ascii=False),
                "PMC_JSON": json.dumps(dict(zip(CMED_TAX_BANDS, r["consumerPrices"])), ensure_ascii=False),
                "PMVG_JSON": json.dumps(dict(zip(CMED_TAX_BANDS, r["governmentPrices"])), ensure_ascii=False),
            }
            for r in cmed_compact
        ]
        _write_gzip_csv(
            self.output_dir / "downloads" / "cmed-consolidada.csv.gz",
            cmed_export,
            list(cmed_export[0].keys()) if cmed_export else ["CÓDIGO GGREM"],
        )
        _write_gzip_csv(
            self.output_dir / "downloads" / "empresas.csv.gz",
            [
                {
                    "ID_EMPRESA": x["id"],
                    "CNPJ": x["cnpj"],
                    "RAZAO_SOCIAL": x["name"],
                    "QTD_PRODUTOS": x["productCount"],
                    "QTD_APRESENTACOES": x["presentationCount"],
                }
                for x in companies_catalog
            ],
            ["ID_EMPRESA", "CNPJ", "RAZAO_SOCIAL", "QTD_PRODUTOS", "QTD_APRESENTACOES"],
        )
        _write_gzip_csv(
            self.output_dir / "downloads" / "principios-ativos.csv.gz",
            [
                {
                    "ID_PRINCIPIO_ATIVO": x["id"],
                    "PRINCIPIO_ATIVO": x["name"],
                    "QTD_PRODUTOS": x["productCount"],
                    "QTD_EMPRESAS": x["companyCount"],
                }
                for x in ingredients_catalog
            ],
            ["ID_PRINCIPIO_ATIVO", "PRINCIPIO_ATIVO", "QTD_PRODUTOS", "QTD_EMPRESAS"],
        )

        cmed_total = len(cmed_compact)
        presentations_total = len(presentations_all)
        cmed_linked = len(linked_ggrem)
        presentations_linked = len(linked_presentation_regs)
        quality = {
            "pipelineVersion": PIPELINE_VERSION,
            "metrics": {
                "sourceMedicineRows": len(medicines_source),
                "exactDuplicateMedicineRowsRemoved": duplicate_count,
                "products": len(products_catalog),
                "productsWithRegistration": registered,
                "productsWithoutRegistration": without_valid_registration,
                "productsWithMalformedRegistrationLength": malformed_registration,
                "productsWithoutCompany": products_without_company,
                "productsWithoutActiveIngredient": products_without_ingredient,
                "productsWithLeaflet": products_with_leaflet,
                "productsWithLeafletHistory": products_with_leaflet_history,
                "productsWithCmed": products_with_cmed,
                "productsWithInspectionOccurrence": products_with_alert,
                "commercialPresentations13": presentations_total,
                "linkedCommercialPresentations13": presentations_linked,
                "unlinkedCommercialPresentations13": presentations_total - presentations_linked,
                "presentationLinkRate": round((presentations_linked / presentations_total * 100), 2) if presentations_total else 0,
                "cmedEconomicRecordsGgrem": cmed_total,
                "linkedCmedEconomicRecordsGgrem": cmed_linked,
                "unlinkedCmedEconomicRecordsGgrem": cmed_total - cmed_linked,
                "cmedLinkRate": round((cmed_linked / cmed_total * 100), 2) if cmed_total else 0,
                "cmedPfMismatchGgrem": cmed_stats.get("pfMismatchGgrem", 0),
                "cmedInvalidPresentationRegistrationLength": cmed_stats.get("invalidPresentationRegistrationLength", 0),
            },
            "relationships": self.schema_report["relationships"],
            "warnings": self.schema_report["warnings"],
        }
        dump_json(self.output_dir / "quality-report.json", quality, pretty=True)
        dump_json(self.output_dir / "schema-report.json", self.schema_report, pretty=True)
        dump_json(self.output_dir / "data-dictionary.json", {
            "project": PROJECT_NAME,
            "pipelineVersion": PIPELINE_VERSION,
            "sourceScope": "Somente os seis CSVs fornecidos/documentados",
            "schemas": {
                "medicamentos": {"header": True, "columns": MEDICINES_COLUMNS},
                "cmed": {
                    "header": True,
                    "identifierColumns": ["REGISTRO", "CÓDIGO GGREM", "APRESENTAÇÃO"],
                    "taxBands": CMED_TAX_BANDS,
                },
                "bula_produto": {
                    "header": False,
                    "columns": BULA_PRODUTO_COLUMNS,
                    "verifiedRelations": BULA_PRODUTO_LINK,
                },
                "bula_documento": {
                    "header": False,
                    "columns": BULA_DOCUMENTO_COLUMNS,
                    "verifiedRelations": BULA_DOCUMENTO_LINK,
                },
                "irregulares": {"header": True, "columns": IRREGULAR_COLUMNS},
            },
            "rules": {
                "productIdentity": (
                    "NUMERO_REGISTRO_PRODUTO com exatamente 9 dígitos identifica o medicamento. "
                    "Sem registro válido de 9 dígitos, cada linha distinta é preservada por hash; não há merge por nome."
                ),
                "presentationIdentity": (
                    "Na CMED, REGISTRO com exatamente 13 dígitos identifica a apresentação comercializada; "
                    "os 9 primeiros dígitos identificam o medicamento."
                ),
                "cmedEconomicIdentity": (
                    "CÓDIGO GGREM identifica o registro econômico usado para consolidar PF/PMC e PF/PMVG. "
                    "Mais de um GGREM pode estar associado ao mesmo REGISTRO de apresentação de 13 dígitos."
                ),
                "cmed": "Os valores econômicos são dados técnicos públicos; não são oferta, publicidade, cotação ou recomendação comercial.",
                "leaflets": ("Os dois CSVs do Bulário não têm cabeçalho. O Medicamento Aberto aplica nomes funcionais internos. "
                    "BULA_PRODUTO representa a última atualização do produto; BULA_DOCUMENTO representa o histórico. "
                    "Os vínculos por registro, processo, ID de documento, expediente e transação foram verificados nos próprios arquivos."),
                "irregularities": "Somente REGISTRO de exatamente 9 dígitos é relacionado por igualdade exata; valores de outros comprimentos não são truncados.",
            },
        }, pretty=True)

        dump_json(self.output_dir / "manifest.json", {
            "project": PROJECT_NAME,
            "description": PROJECT_DESCRIPTION,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "dataVersion": current_version,
            "pipelineVersion": PIPELINE_VERSION,
            "sourceMode": "real",
            "cmedTaxBands": CMED_TAX_BANDS,
            "schemas": {
                "medicamentos": MEDICINES_COLUMNS,
                "bula_produto": BULA_PRODUTO_COLUMNS,
                "bula_documento": BULA_DOCUMENTO_COLUMNS,
                "irregulares": IRREGULAR_COLUMNS,
            },
            "counts": {
                "products": len(products_catalog),
                "presentations": presentations_total,
                "linkedPresentations": presentations_linked,
                "cmedEconomicRecords": cmed_total,
                "companies": len(companies_catalog),
                "ingredients": len(ingredients_catalog),
                "productsWithLeaflet": products_with_leaflet,
                "productsWithLeafletHistory": products_with_leaflet_history,
                "productsWithCmed": products_with_cmed,
                "productsWithAlert": products_with_alert,
            },
            "sources": [asdict(info) for info in self.source_info.values()],
        }, pretty=True)

        print("[OK] Build concluído")
        print(f"     Produtos: {len(products_catalog):,}")
        print(f"     Apresentações comercializadas (REGISTRO 13): {presentations_total:,}")
        print(f"     Apresentações vinculadas a produto de 9 dígitos: {presentations_linked:,}/{presentations_total:,}")
        print(f"     Registros econômicos CMED (GGREM): {cmed_total:,}")
        print(f"     GGREM vinculados: {cmed_linked:,}/{cmed_total:,}")
        print(f"     Empresas: {len(companies_catalog):,}")
        print(f"     Princípios ativos: {len(ingredients_catalog):,}")
        print(f"     Produtos com bula atual no Bulário: {products_with_leaflet:,}")
        print(f"     Produtos com histórico de bula: {products_with_leaflet_history:,}")
        print(f"     Produtos com ocorrência de fiscalização: {products_with_alert:,}")


def parse_args() -> argparse.Namespace:
    root = SCRIPT_DIR.parent
    parser = argparse.ArgumentParser(description="Build estático do Medicamento Aberto — 6 CSVs exatos.")
    parser.add_argument("--input", type=Path, default=root / "public" / "fontes")
    parser.add_argument("--output", type=Path, default=root / "public" / "data")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    Builder(args.input.resolve(), args.output.resolve()).build()


if __name__ == "__main__":
    main()
