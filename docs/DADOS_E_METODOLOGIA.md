# Medicamento Aberto — Dados e metodologia

Este documento concentra os detalhes técnicos que não são exibidos como parte principal da experiência pública. O objetivo é permitir auditoria, reprodutibilidade e novo reúso dos dados.

## Princípio geral

O Medicamento Aberto utiliza exclusivamente **dados abertos** da Anvisa e da CMED.

Os arquivos originais utilizados no processamento são preservados em `public/fontes/`, versionados junto ao repositório e disponibilizados para download pela aplicação.

## Arquivos processados

1. `DADOS_ABERTOS_MEDICAMENTOS.csv`
2. `TA_PRECO_MEDICAMENTO.csv`
3. `TA_PRECO_MEDICAMENTO_GOV.csv`
4. `TA_CONSULTA_BULA_PRODUTO.CSV`
5. `TA_CONSULTA_BULA_DOCUMENTO.CSV`
6. `TA_CONSULTA_PRODUTOS_IRREGULARES_RESULTADO.CSV`

Os metadados de processamento, incluindo SHA-256, quantidade de linhas/colunas e endereços de origem, são preservados em `public/data/catalog/sources.json` e `public/data/manifest.json`.

## Base principal de medicamentos

`DADOS_ABERTOS_MEDICAMENTOS.csv` é validado pelas seguintes colunas:

```text
TIPO_PRODUTO
NOME_PRODUTO
DATA_FINALIZACAO_PROCESSO
CATEGORIA_REGULATORIA
NUMERO_REGISTRO_PRODUTO
DATA_VENCIMENTO_REGISTRO
NUMERO_PROCESSO
CLASSE_TERAPEUTICA
EMPRESA_DETENTORA_REGISTRO
SITUACAO_REGISTRO
PRINCIPIO_ATIVO
```

A situação **Ativo/Inativo** apresentada pela plataforma é reproduzida exclusivamente de `SITUACAO_REGISTRO`. CMED, Bulário, vencimento ou fiscalização não são utilizados para inferir esse status.

## Identidade e relacionamento

### Medicamento

`NUMERO_REGISTRO_PRODUTO` com exatamente **9 dígitos** identifica o medicamento quando disponível.

Para linhas sem registro válido de nove dígitos:

- duplicatas exatas são removidas;
- cada linha distinta permanece individualizada por identificador determinístico;
- não é realizado merge apenas por nome comercial, empresa ou categoria.

### Apresentação comercializada

Nas listas CMED, `REGISTRO` com exatamente **13 dígitos** identifica a apresentação.

Os primeiros nove dígitos identificam o medicamento relacionado:

```text
REGISTRO_APRESENTACAO[0:9] = NUMERO_REGISTRO_PRODUTO
```

### CÓDIGO GGREM

`CÓDIGO GGREM` identifica o registro econômico CMED associado à apresentação. Ele não é utilizado como identidade da apresentação.

Uma mesma apresentação pode possuir mais de um GGREM.

## CMED

As duas listas econômicas são complementares:

- `TA_PRECO_MEDICAMENTO.csv`: PF + PMC;
- `TA_PRECO_MEDICAMENTO_GOV.csv`: PF + PMVG.

Regras principais:

- consolidação econômica entre as listas por `CÓDIGO GGREM`;
- vínculo ao medicamento pelos nove primeiros dígitos do `REGISTRO` de 13 dígitos;
- normalização das faixas tributárias;
- preservação separada de marcadores presentes na fonte;
- contabilização de divergências de PF entre as duas listas.

Na interface, **“Possui preço publicado na CMED”** significa exclusivamente que existe ao menos um registro CMED relacionado ao medicamento.

PF, PMC e PMVG são parâmetros publicados pela CMED e não são apresentados como oferta, promoção, cotação, recomendação comercial ou preço efetivamente praticado.

## Bulário Eletrônico

Os dois arquivos de dados abertos utilizados para o Bulário não possuem linha de cabeçalho. O Medicamento Aberto atribui nomes funcionais internos às posições para permitir processamento e documentação.

### `TA_CONSULTA_BULA_PRODUTO.CSV`

Representa a **última atualização localizada** do medicamento no Bulário Eletrônico.

| Posição | Nome funcional interno |
| ---: | --- |
| 1 | `ID_PRODUTO_BULARIO` |
| 2 | `NOME_PRODUTO_BULARIO` |
| 3 | `NUMERO_REGISTRO_PRODUTO` |
| 4 | `CODIGO_CATEGORIA_REGULATORIA` |
| 5 | `NUMERO_PROCESSO` |
| 6 | `CNPJ_EMPRESA` |
| 7 | `RAZAO_SOCIAL_EMPRESA` |
| 8 | `ID_DOCUMENTO_ATUAL` |
| 9 | `NUMERO_EXPEDIENTE_ATUAL` |
| 10 | `DATA_ULTIMA_ATUALIZACAO_BULARIO` |
| 11 | `NUMERO_TRANSACAO_ATUAL` |
| 12 | `DATA_CARGA_ETL` |

### `TA_CONSULTA_BULA_DOCUMENTO.CSV`

Representa o **histórico de atualizações/documentos** do Bulário Eletrônico.

| Posição | Nome funcional interno |
| ---: | --- |
| 1 | `NUMERO_PROCESSO` |
| 2 | `ID_DOCUMENTO` |
| 3 | `NUMERO_EXPEDIENTE` |
| 4 | `CODIGO_SITUACAO_DOCUMENTO` |
| 5 | `SITUACAO_DOCUMENTO` |
| 6 | `DATA_SITUACAO_DOCUMENTO` |
| 7 | `NUMERO_TRANSACAO` |
| 8 | `DATA_ATUALIZACAO_BULARIO` |
| 9 | `DATA_REGISTRO_DOCUMENTO` |
| 10 | `DATA_CARGA_ETL` |

Os nomes acima são **nomes funcionais internos do projeto**, não cabeçalhos fornecidos nos arquivos de origem.

Os campos de documento, expediente, transação e data da atualização atual foram validados por correspondência entre os dois conjuntos.

## Atualizações na interface

A página pública **Atualizações** utiliza somente:

1. eventos datados do Bulário;
2. alertas e ocorrências de fiscalização.

Alterações de situação do registro, presença na CMED ou quantidade de apresentações não são classificadas como “Atualizações” na interface.

## Fiscalização

Em `TA_CONSULTA_PRODUTOS_IRREGULARES_RESULTADO.CSV`, o relacionamento com medicamentos é conservador.

Somente valores de `REGISTRO` com exatamente nove dígitos são relacionados a `NUMERO_REGISTRO_PRODUTO`. Valores com outros comprimentos não são truncados para forçar correspondência.

A ausência de ocorrência não comprova regularidade sanitária.

## Formatação de datas

- valores já em `DD/MM/AAAA` são preservados;
- datas do Bulário e fiscalização em `MM/DD/YYYY HH:mm:ss` são exibidas como `DD/MM/AAAA HH:mm:ss` ou `DD/MM/AAAA`, conforme o contexto;
- `DATA_VENCIMENTO_REGISTRO` em `MMAAAA` é exibida como `MM/AAAA`;
- a transformação de apresentação não altera o valor original preservado nos dados derivados.

## Dados originais e dados derivados

### Originais

Os arquivos brutos ficam em:

```text
public/fontes/
```

Eles são:

- versionados no GitHub;
- utilizados diretamente como entrada do ETL;
- disponibilizados para download na aplicação.

### Derivados

O processamento gera:

```text
public/data/
```

Entre os artefatos estão:

- `manifest.json`;
- `schema-report.json`;
- `quality-report.json`;
- `data-dictionary.json`;
- `catalog/sources.json`;
- catálogos de medicamentos, empresas e princípios ativos;
- detalhes particionados de medicamentos;
- arquivos derivados compactados em `downloads/`.

## Atualização automática

O workflow `.github/workflows/update-data.yml`:

1. baixa novamente as seis fontes para `public/fontes/`;
2. valida a estrutura da base principal;
3. compara os arquivos baixados com os checksums da publicação existente;
4. reconstrói `public/data/` somente quando necessário;
5. executa validações e testes;
6. commita `public/fontes/` e `public/data/` no mesmo commit.

Se o download ou a validação falhar, a publicação anterior não deve ser substituída por uma base incompleta.

## Princípios de integridade

- não utilizar fuzzy matching silencioso para aumentar cobertura;
- não interpretar ausência de resultado como conclusão regulatória;
- manter a situação do registro vinculada exclusivamente à fonte correspondente;
- distinguir apresentação de 13 dígitos de registro econômico GGREM;
- manter dados econômicos em contexto técnico, sem linguagem promocional;
- preservar os arquivos originais utilizados em cada publicação.
