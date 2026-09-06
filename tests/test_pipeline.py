from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from schemas import (  # noqa: E402
    BULA_DOCUMENTO_COLUMNS,
    BULA_PRODUTO_COLUMNS,
    CMED_ID_COLUMNS,
    CMED_TAX_BANDS,
    IRREGULAR_COLUMNS,
    MEDICINES_COLUMNS,
)


def price_columns(prefix: str) -> list[str]:
    output = []
    for band in CMED_TAX_BANDS:
        if band == "Sem impostos":
            output.append(f"{prefix} Sem Impostos")
        elif band.endswith(" ALC"):
            output.append(f"{prefix} {band[:-4]}  ALC")
        else:
            output.append(f"{prefix} {band}")
    return output


TRAILING = [
    "RESTRIÇÃO HOSPITALAR",
    "CAP",
    "CONFAZ 87",
    "ICMS 0%",
    "ANÁLISE RECURSAL",
    "LISTA DE CONCESSÃO DE CRÉDITO TRIBUTÁRIO (PIS/COFINS)",
    "COMERCIALIZAÇÃO 2025",
    "TARJA",
    "DESTINAÇÃO COMERCIAL",
]


def write_semicolon(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="cp1252", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def write_cmed(path: Path, government: bool) -> None:
    price2 = price_columns("PMVG" if government else "PMC")
    columns = [*CMED_ID_COLUMNS, *price_columns("PF"), *price2, *TRAILING]
    assert len(columns) == 74

    rows = []
    for ggrem, reg13, desc, pf, second in [
        ("111111111111111", "1234567890001", "500 MG COM CT BL X 10", "10,00", "7,85" if government else "16,00"),
        # Mesmo REGISTRO de 13 dígitos, GGREM diferente: continua sendo UMA apresentação.
        ("111111111111112", "1234567890001", "500 MG COM CT BL X 10", "10,00", "7,85" if government else "16,00"),
        ("111111111111113", "1234567890002", "500 MG COM CT BL X 20", "18,00", "14,14" if government else "28,00"),
    ]:
        row = {column: "" for column in columns}
        row.update({
            "SUBSTÂNCIA": "DIPIRONA",
            "CNPJ": "11111111000111",
            "LABORATÓRIO": "EMPRESA A",
            "CÓDIGO GGREM": ggrem,
            "REGISTRO": reg13,
            "EAN 1": "7890000000011" if reg13.endswith("001") else "7890000000012",
            "PRODUTO": "ALFA",
            "APRESENTAÇÃO": desc,
            "CLASSE TERAPÊUTICA": "ANALGÉSICOS",
            "TIPO DE PRODUTO (STATUS DO PRODUTO)": "Genérico",
            "REGIME DE PREÇO": "Regulado",
            "PF 0%": (pf + "*" if government else pf),
            ("PMVG 0%" if government else "PMC 0%"): second,
            "RESTRIÇÃO HOSPITALAR": "Não",
            "CAP": "Não",
            "COMERCIALIZAÇÃO 2025": "Sim",
            "TARJA": "Vermelha",
            "DESTINAÇÃO COMERCIAL": "Comercial",
        })
        rows.append(row)

    title = (
        "LISTA DE PREÇOS DE MEDICAMENTOS - PREÇOS FÁBRICA E MÁXIMOS DE VENDA AO GOVERNO"
        if government else
        "LISTA DE PREÇOS DE MEDICAMENTOS - PREÇOS FÁBRICA E MÁXIMOS AO CONSUMIDOR"
    )
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write("Secretaria Executiva - CMED\n")
        stream.write(title + "\n")
        stream.write("Publicada em 21/07/2026 17h30min.\n")
        if government:
            stream.write("O CAP é de 21,53%.\n")
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


class PipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="medicamento-aberto-test-"))
        self.input = self.temp / "input"
        self.output = self.temp / "output"
        self.input.mkdir()
        self.make_sources()
        self.run_build(self.output)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)

    def make_sources(self) -> None:
        write_semicolon(
            self.input / "DADOS_ABERTOS_MEDICAMENTOS.csv",
            MEDICINES_COLUMNS,
            [
                {
                    "TIPO_PRODUTO": "MEDICAMENTO",
                    "NOME_PRODUTO": "ALFA",
                    "DATA_FINALIZACAO_PROCESSO": "01/01/2020",
                    "CATEGORIA_REGULATORIA": "GENÉRICO",
                    "NUMERO_REGISTRO_PRODUTO": "123456789",
                    "DATA_VENCIMENTO_REGISTRO": "012030",
                    "NUMERO_PROCESSO": "253510001",
                    "CLASSE_TERAPEUTICA": "ANALGÉSICOS",
                    "EMPRESA_DETENTORA_REGISTRO": "11111111000111 - EMPRESA A",
                    "SITUACAO_REGISTRO": "VÁLIDO",
                    "PRINCIPIO_ATIVO": "DIPIRONA",
                },
                {
                    "TIPO_PRODUTO": "MEDICAMENTO NOTIFICADO",
                    "NOME_PRODUTO": "GAMA",
                    "DATA_FINALIZACAO_PROCESSO": "02/02/2021",
                    "CATEGORIA_REGULATORIA": "NOTIFICAÇÃO SIMPLIFICADA",
                    "NUMERO_REGISTRO_PRODUTO": "",
                    "DATA_VENCIMENTO_REGISTRO": "",
                    "NUMERO_PROCESSO": "253510002",
                    "CLASSE_TERAPEUTICA": "OUTROS",
                    "EMPRESA_DETENTORA_REGISTRO": "22222222000122 - EMPRESA B",
                    "SITUACAO_REGISTRO": "ATIVO",
                    "PRINCIPIO_ATIVO": "SUBSTÂNCIA X",
                },
            ],
        )
        write_cmed(self.input / "TA_PRECO_MEDICAMENTO (2).csv", government=False)
        write_cmed(self.input / "TA_PRECO_MEDICAMENTO_GOV(1).csv", government=True)

        # Sem cabeçalho: 12 posições, renomeadas internamente pelo pipeline.
        with (self.input / "TA_CONSULTA_BULA_PRODUTO.CSV").open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream, delimiter=";").writerow([
                "857968", "ALFA", "123456789", "5", "253510001", "11111111000111",
                "EMPRESA A", "34724385", "0104756268", "02/02/2026 09:15:21", "1416792026", "08/28/2026 00:00:00",
            ])

        # Sem cabeçalho: 10 posições, renomeadas internamente pelo pipeline.
        with (self.input / "TA_CONSULTA_BULA_DOCUMENTO.CSV").open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream, delimiter=";").writerow([
                "253510001", "34724385", "0104756268", "43", "Aditado ao processo",
                "02/02/2026 09:15:21", "1416792026", "02/02/2026 09:15:21", "02/02/2026 09:14:20", "08/28/2026 00:00:00",
            ])

        irr_rows = []
        for registration in ("123456789", "12345678901"):
            row = {column: "" for column in IRREGULAR_COLUMNS}
            row.update({
                "CO_SEQ_DOSSIE_INVESTIG_MED": "1",
                "NU_PROCESSO": "25351000999",
                "NO_RAZAO_SOCIAL": "EMPRESA A",
                "DS_TIPO_PRODUTO": "Medicamento",
                "DT_PUBLICACAO": "08/01/2026 00:00:00",
                "PRODUTO": "ALFA",
                "REGISTRO": registration,
                "DS_ACAO_FISCALIZACAO": "Recolhimento",
            })
            irr_rows.append(row)
        write_semicolon(self.input / "TA_CONSULTA_PRODUTOS_IRREGULARES_RESULTADO.CSV", IRREGULAR_COLUMNS, irr_rows)

    def run_build(self, output: Path) -> None:
        subprocess.run(
            [sys.executable, str(SCRIPTS / "build_data.py"), "--input", str(self.input), "--output", str(output)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def read_json(self, relative: str):
        return json.loads((self.output / relative).read_text(encoding="utf-8"))

    def details(self):
        rows = []
        for path in (self.output / "products").glob("*.json"):
            rows.extend(json.loads(path.read_text(encoding="utf-8")))
        return rows

    def test_exact_six_source_schema(self):
        schema = self.read_json("schema-report.json")
        self.assertEqual(set(schema["sources"]), {
            "medicamentos", "cmed_consumidor", "cmed_governo",
            "bula_produto", "bula_documento", "irregulares",
        })
        self.assertEqual(schema["sources"]["medicamentos"]["columns"], MEDICINES_COLUMNS)
        self.assertEqual(schema["sources"]["bula_produto"]["columnCount"], len(BULA_PRODUTO_COLUMNS))
        self.assertEqual(schema["sources"]["bula_documento"]["columnCount"], len(BULA_DOCUMENTO_COLUMNS))

    def test_product_identity_is_nine_digits(self):
        manifest = self.read_json("manifest.json")
        self.assertEqual(manifest["counts"]["products"], 2)
        alfa = next(row for row in self.details() if row["name"] == "ALFA")
        gama = next(row for row in self.details() if row["name"] == "GAMA")
        self.assertTrue(alfa["validProductRegistration"])
        self.assertEqual(alfa["registrationNumberDigits"], "123456789")
        self.assertFalse(gama["validProductRegistration"])
        self.assertEqual(gama["registrationNumber"], "")

    def test_presentation_identity_is_thirteen_digits_not_ggrem(self):
        manifest = self.read_json("manifest.json")
        # 3 GGREM, mas apenas 2 REGISTROS de apresentação de 13 dígitos.
        self.assertEqual(manifest["counts"]["cmedEconomicRecords"], 3)
        self.assertEqual(manifest["counts"]["presentations"], 2)
        alfa = next(row for row in self.details() if row["name"] == "ALFA")
        self.assertEqual(len(alfa["presentations"]), 2)
        first = next(row for row in alfa["presentations"] if row["registrationNumber"] == "1234567890001")
        self.assertEqual(first["productRegistrationNumber"], "123456789")
        self.assertEqual(len(first["ggremCodes"]), 2)
        self.assertEqual(first["economicRecordCount"], 2)

    def test_cmed_prices_are_economic_records(self):
        alfa = next(row for row in self.details() if row["name"] == "ALFA")
        self.assertEqual(len(alfa["cmed"]), 3)
        row = alfa["cmed"][0]
        self.assertEqual(row["presentationRegistrationNumber"][:9], row["productRegistrationNumber"])
        zero_index = self.read_json("manifest.json")["cmedTaxBands"].index("0%")
        self.assertEqual(row["factoryPrices"][zero_index], "10,00")
        self.assertEqual(row["consumerPrices"][zero_index], "16,00")
        self.assertEqual(row["governmentPrices"][zero_index], "7,85")
        self.assertEqual(row["governmentFactoryPriceMarkers"][zero_index], "*")

    def test_irregularities_require_exact_nine_digits(self):
        alfa = next(row for row in self.details() if row["name"] == "ALFA")
        self.assertEqual(len(alfa["alerts"]), 1)
        self.assertEqual(alfa["alerts"][0]["matchMethod"], "REGISTRO = NUMERO_REGISTRO_PRODUTO (9 dígitos exatos)")
        quality = self.read_json("quality-report.json")
        relation = quality["relationships"]["irregularities"]
        self.assertEqual(relation["nineDigitRegistrationRows"], 1)
        self.assertEqual(relation["ignoredOtherRegistrationLengths"], {"11": 1})

    def test_leaflets_have_functional_names_latest_and_history(self):
        alfa = next(row for row in self.details() if row["name"] == "ALFA")
        self.assertEqual(len(alfa["leafletLatest"]), 1)
        self.assertEqual(len(alfa["leafletHistory"]), 1)
        dictionary = self.read_json("data-dictionary.json")
        self.assertFalse(dictionary["schemas"]["bula_produto"]["header"])
        self.assertEqual(dictionary["schemas"]["bula_produto"]["columns"][2], "NUMERO_REGISTRO_PRODUTO")
        self.assertEqual(dictionary["schemas"]["bula_produto"]["columns"][9], "DATA_ULTIMA_ATUALIZACAO_BULARIO")
        self.assertEqual(dictionary["schemas"]["bula_documento"]["columns"][7], "DATA_ATUALIZACAO_BULARIO")
        relationships = self.read_json("quality-report.json")["relationships"]["leaflets"]["verifiedLinks"]
        self.assertEqual(relationships["bula_produto.ID_DOCUMENTO_ATUAL -> bula_documento.ID_DOCUMENTO"]["matchingValues"], 1)

    def test_open_exports_and_quality_metrics(self):
        for relative in [
            "downloads/medicamentos.csv.gz",
            "downloads/apresentacoes-comercializadas.csv.gz",
            "downloads/cmed-consolidada.csv.gz",
            "downloads/empresas.csv.gz",
            "downloads/principios-ativos.csv.gz",
            "quality-report.json",
            "schema-report.json",
            "data-dictionary.json",
            "catalog/sources.json",
        ]:
            self.assertTrue((self.output / relative).exists(), relative)
        quality = self.read_json("quality-report.json")
        self.assertEqual(quality["metrics"]["commercialPresentations13"], 2)
        self.assertEqual(quality["metrics"]["linkedCommercialPresentations13"], 2)
        self.assertEqual(quality["metrics"]["presentationLinkRate"], 100.0)

    def test_data_version_is_reproducible(self):
        first = self.read_json("manifest.json")["dataVersion"]
        second = self.temp / "second"
        self.run_build(second)
        other = json.loads((second / "manifest.json").read_text(encoding="utf-8"))["dataVersion"]
        self.assertEqual(first, other)


if __name__ == "__main__":
    unittest.main()
