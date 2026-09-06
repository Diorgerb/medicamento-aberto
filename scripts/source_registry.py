from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    label: str
    organization: str
    description: str
    filenames: tuple[str, ...]
    download_url: str
    official_page_url: str
    catalog_url: str
    license_label: str
    format: str = "CSV"
    layer: str = ""
    header_mode: str = "header"

    def public_dict(self) -> dict[str, str | list[str]]:
        data = asdict(self)
        data["filenames"] = list(self.filenames)
        return data


# Fontes de dados abertos utilizadas pela plataforma.
SOURCES: tuple[SourceDefinition, ...] = (
    SourceDefinition(
        key="medicamentos",
        label="Medicamentos — dados abertos",
        organization="Agência Nacional de Vigilância Sanitária (Anvisa)",
        description="Base principal com produto, registro/processo, categoria regulatória, empresa, situação e princípio ativo.",
        filenames=("DADOS_ABERTOS_MEDICAMENTOS.csv",),
        download_url="https://dados.anvisa.gov.br/dados/DADOS_ABERTOS_MEDICAMENTOS.csv",
        official_page_url="https://dados.anvisa.gov.br/dados/",
        catalog_url="https://dados.gov.br/dados/conjuntos-dados/medicamentos-registrados-no-brasil",
        license_label="Dados abertos oficiais; consulte a licença/termos indicados no catálogo oficial.",
        layer="Regularização",
    ),
    SourceDefinition(
        key="cmed_consumidor",
        label="CMED — PF e PMC",
        organization="Câmara de Regulação do Mercado de Medicamentos (CMED) / Anvisa",
        description="Lista CMED com REGISTRO de 13 dígitos por apresentação, CÓDIGO GGREM e parâmetros PF/PMC por faixa tributária.",
        filenames=(
            "TA_PRECO_MEDICAMENTO.csv",
            "TA_PRECO_MEDICAMENTO (2).csv",
            "TA_PRECO_MEDICAMENTO(2).csv",
        ),
        download_url="https://dados.anvisa.gov.br/dados/TA_PRECO_MEDICAMENTO.csv",
        official_page_url="https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos",
        catalog_url="",
        license_label="Fonte de dados abertos oficial da Anvisa/CMED.",
        layer="Apresentações comercializadas e dados econômicos CMED",
    ),
    SourceDefinition(
        key="cmed_governo",
        label="CMED — PF e PMVG",
        organization="Câmara de Regulação do Mercado de Medicamentos (CMED) / Anvisa",
        description="Lista CMED com REGISTRO de 13 dígitos por apresentação, CÓDIGO GGREM e parâmetros PF/PMVG por faixa tributária.",
        filenames=(
            "TA_PRECO_MEDICAMENTO_GOV.csv",
            "TA_PRECO_MEDICAMENTO_GOV(1).csv",
        ),
        download_url="https://dados.anvisa.gov.br/dados/TA_PRECO_MEDICAMENTO_GOV.csv",
        official_page_url="https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos",
        catalog_url="",
        license_label="Fonte de dados abertos oficial da Anvisa/CMED.",
        layer="Apresentações comercializadas e dados econômicos CMED",
    ),
    SourceDefinition(
        key="bula_produto",
        label="Bulário — produto",
        organization="Agência Nacional de Vigilância Sanitária (Anvisa)",
        description="Estado mais recente do produto no Bulário Eletrônico da Anvisa. O CSV não traz cabeçalho; o projeto aplica nomes funcionais internos às 12 posições verificadas.",
        filenames=("TA_CONSULTA_BULA_PRODUTO.CSV",),
        download_url="https://dados.anvisa.gov.br/dados/CONSULTAS/DOCUMENTOS/TA_CONSULTA_BULA_PRODUTO.CSV",
        official_page_url="https://dados.anvisa.gov.br/dados/CONSULTAS/DOCUMENTOS/",
        catalog_url="",
        license_label="Fonte de dados abertos oficial da Anvisa.",
        layer="Bulas",
        header_mode="positional-12-named-internally",
    ),
    SourceDefinition(
        key="bula_documento",
        label="Bulário — documento",
        organization="Agência Nacional de Vigilância Sanitária (Anvisa)",
        description="Histórico de atualizações/documentos do Bulário Eletrônico da Anvisa. O CSV não traz cabeçalho; o projeto aplica nomes funcionais internos às 10 posições verificadas.",
        filenames=("TA_CONSULTA_BULA_DOCUMENTO.CSV",),
        download_url="https://dados.anvisa.gov.br/dados/CONSULTAS/DOCUMENTOS/TA_CONSULTA_BULA_DOCUMENTO.CSV",
        official_page_url="https://dados.anvisa.gov.br/dados/CONSULTAS/DOCUMENTOS/",
        catalog_url="",
        license_label="Fonte de dados abertos oficial da Anvisa.",
        layer="Bulas",
        header_mode="positional-10-named-internally",
    ),
    SourceDefinition(
        key="irregulares",
        label="Produtos irregulares — resultado",
        organization="Agência Nacional de Vigilância Sanitária (Anvisa)",
        description="Ocorrências e medidas publicadas na consulta de produtos irregulares.",
        filenames=("TA_CONSULTA_PRODUTOS_IRREGULARES_RESULTADO.CSV",),
        download_url="https://dados.anvisa.gov.br/dados/CONSULTAS/EMPRESA_FISCALIZACAO_PRODUTO/TA_CONSULTA_PRODUTOS_IRREGULARES_RESULTADO.CSV",
        official_page_url="https://dados.anvisa.gov.br/dados/CONSULTAS/EMPRESA_FISCALIZACAO_PRODUTO/",
        catalog_url="",
        license_label="Fonte de dados abertos oficial da Anvisa.",
        layer="Fiscalização",
    ),
)

SOURCE_BY_KEY = {source.key: source for source in SOURCES}
