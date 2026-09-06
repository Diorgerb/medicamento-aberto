from __future__ import annotations

# Esquemas efetivamente observados nos seis CSVs fornecidos pelo usuário.
# Nos quatro arquivos com cabeçalho, os nomes são literais.
# Nos dois arquivos do Bulário, que não trazem cabeçalho, os nomes abaixo são
# NOMES FUNCIONAIS INTERNOS do Medicamento Aberto, definidos a partir da
# estrutura e das correspondências verificadas entre os próprios arquivos.

MEDICINES_COLUMNS = [
    "TIPO_PRODUTO",
    "NOME_PRODUTO",
    "DATA_FINALIZACAO_PROCESSO",
    "CATEGORIA_REGULATORIA",
    "NUMERO_REGISTRO_PRODUTO",
    "DATA_VENCIMENTO_REGISTRO",
    "NUMERO_PROCESSO",
    "CLASSE_TERAPEUTICA",
    "EMPRESA_DETENTORA_REGISTRO",
    "SITUACAO_REGISTRO",
    "PRINCIPIO_ATIVO",
]

IRREGULAR_COLUMNS = [
    "CO_SEQ_DOSSIE_INVESTIG_MED",
    "NU_PROCESSO",
    "NU_CNPJ",
    "NO_RAZAO_SOCIAL",
    "CO_TIPO_PRODUTO",
    "DS_TIPO_PRODUTO",
    "CO_RISCO",
    "DS_RISCO_PRODUTO",
    "TOTAL_MEDIDA_CAUTELAR",
    "NO_EMPRESA_INVESTIGADA",
    "NU_CNPJ_EMPRESA_INVESTIGADA",
    "CO_ASSUNTO",
    "DT_PUBLICACAO_MEDIDA",
    "CO_ACAO_FISCALIZACAO",
    "CO_ATIVIDADE_FISCALIZACAO",
    "DT_PUBLICACAO",
    "PRODUTOS_CONCATENADOS",
    "DS_ACAO_FISCALIZACAO",
    "DS_ATIVIDADE_FISCALIZACAO",
    "ACAO_ATIVIDADE",
    "PRODUTO",
    "REGISTRO",
    "DT_CARGA_ETL",
]

CMED_ID_COLUMNS = [
    "SUBSTÂNCIA",
    "CNPJ",
    "LABORATÓRIO",
    "CÓDIGO GGREM",
    "REGISTRO",
    "EAN 1",
    "EAN 2",
    "EAN 3",
    "PRODUTO",
    "APRESENTAÇÃO",
    "CLASSE TERAPÊUTICA",
    "TIPO DE PRODUTO (STATUS DO PRODUTO)",
    "REGIME DE PREÇO",
]

CMED_TRAILING_COLUMNS = [
    "RESTRIÇÃO HOSPITALAR",
    "CAP",
    "CONFAZ 87",
    "ICMS 0%",
    "ANÁLISE RECURSAL",
    "LISTA DE CONCESSÃO DE CRÉDITO TRIBUTÁRIO (PIS/COFINS)",
    "COMERCIALIZAÇÃO 2025",
    "TARJA",
]

# ---------------------------------------------------------------------------
# BULÁRIO ELETRÔNICO — nomes funcionais internos
# ---------------------------------------------------------------------------
# TA_CONSULTA_BULA_PRODUTO.CSV não possui cabeçalho no arquivo publicado.
# Ele representa o estado MAIS RECENTE do produto no Bulário.
# Correspondências verificadas com TA_CONSULTA_BULA_DOCUMENTO.CSV:
#   ID_DOCUMENTO_ATUAL      == ID_DOCUMENTO
#   NUMERO_EXPEDIENTE_ATUAL == NUMERO_EXPEDIENTE
#   DATA_ULTIMA_ATUALIZACAO_BULARIO == DATA_ATUALIZACAO_BULARIO
#   NUMERO_TRANSACAO_ATUAL  == NUMERO_TRANSACAO
#   DATA_CARGA_ETL          == DATA_CARGA_ETL
BULA_PRODUTO_COLUMNS = [
    "ID_PRODUTO_BULARIO",
    "NOME_PRODUTO_BULARIO",
    "NUMERO_REGISTRO_PRODUTO",
    "CODIGO_CATEGORIA_REGULATORIA",
    "NUMERO_PROCESSO",
    "CNPJ_EMPRESA",
    "RAZAO_SOCIAL_EMPRESA",
    "ID_DOCUMENTO_ATUAL",
    "NUMERO_EXPEDIENTE_ATUAL",
    "DATA_ULTIMA_ATUALIZACAO_BULARIO",
    "NUMERO_TRANSACAO_ATUAL",
    "DATA_CARGA_ETL",
]

# TA_CONSULTA_BULA_DOCUMENTO.CSV não possui cabeçalho no arquivo publicado.
# Ele representa o HISTÓRICO de documentos/atualizações do Bulário.
# Os nomes abaixo são funcionais e documentados pelo projeto; não são
# apresentados como cabeçalho oficial fornecido pela Anvisa.
BULA_DOCUMENTO_COLUMNS = [
    "NUMERO_PROCESSO",
    "ID_DOCUMENTO",
    "NUMERO_EXPEDIENTE",
    "CODIGO_SITUACAO_DOCUMENTO",
    "SITUACAO_DOCUMENTO",
    "DATA_SITUACAO_DOCUMENTO",
    "NUMERO_TRANSACAO",
    "DATA_ATUALIZACAO_BULARIO",
    "DATA_REGISTRO_DOCUMENTO",
    "DATA_CARGA_ETL",
]

BULA_PRODUTO_LINK = {
    "product_name": "NOME_PRODUTO_BULARIO",
    "registration": "NUMERO_REGISTRO_PRODUTO",
    "process": "NUMERO_PROCESSO",
    "company_cnpj": "CNPJ_EMPRESA",
    "company_name": "RAZAO_SOCIAL_EMPRESA",
    "document_id": "ID_DOCUMENTO_ATUAL",
    "expedient": "NUMERO_EXPEDIENTE_ATUAL",
    "update_date": "DATA_ULTIMA_ATUALIZACAO_BULARIO",
    "transaction": "NUMERO_TRANSACAO_ATUAL",
}

BULA_DOCUMENTO_LINK = {
    "process": "NUMERO_PROCESSO",
    "document_id": "ID_DOCUMENTO",
    "expedient": "NUMERO_EXPEDIENTE",
    "update_date": "DATA_ATUALIZACAO_BULARIO",
    "transaction": "NUMERO_TRANSACAO",
}

EXPECTED_FIELD_COUNTS = {
    "medicamentos": len(MEDICINES_COLUMNS),
    "cmed_consumidor": 74,
    "cmed_governo": 74,
    "bula_produto": len(BULA_PRODUTO_COLUMNS),
    "bula_documento": len(BULA_DOCUMENTO_COLUMNS),
    "irregulares": len(IRREGULAR_COLUMNS),
}

CMED_TAX_BANDS = [
    "Sem impostos",
    "0%",
    "12%", "12% ALC",
    "17%", "17% ALC",
    "17,5%", "17,5% ALC",
    "18%", "18% ALC",
    "19%", "19% ALC",
    "19,5%", "19,5% ALC",
    "20%", "20% ALC",
    "20,5%", "20,5% ALC",
    "21%", "21% ALC",
    "22%", "22% ALC",
    "22,5%", "22,5% ALC",
    "23%", "23% ALC",
]
