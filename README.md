<div align="center">

<img src="public/brand/logo-horizontal.svg" alt="Medicamento Aberto" width="420">

# Medicamento Aberto

### Plataforma integrada de dados abertos sobre medicamentos no Brasil

Consolida informações públicas da **Anvisa** e da **CMED** em uma experiência única de consulta, análise, transparência e reutilização.

[Documentação](docs/DADOS_E_METODOLOGIA.md) ·
[Guia de uso](docs/GUIA_DE_USO.md) ·
[Identidade visual](docs/IDENTIDADE_VISUAL.md)

</div>

---

## Sobre o projeto

O **Medicamento Aberto** é uma plataforma pública de integração de dados sobre medicamentos no Brasil.

O projeto organiza, relaciona e disponibiliza informações que, nas fontes oficiais, estão distribuídas entre diferentes bases e estruturas. A proposta é transformar esses conjuntos de dados em uma camada de consulta mais clara, navegável e reutilizável, preservando a rastreabilidade das fontes originais.

A plataforma foi desenvolvida para atender diferentes perfis de uso:

- cidadãos e pacientes;
- profissionais de saúde;
- profissionais de assuntos regulatórios;
- pesquisadores;
- jornalistas;
- desenvolvedores;
- iniciativas de transparência e controle social.

> O Medicamento Aberto não substitui os sistemas, documentos, atos ou manifestações oficiais da Anvisa e da CMED.

---

## O que é possível consultar

A plataforma integra, por medicamento:

- situação do registro;
- número de registro;
- número do processo;
- categoria regulatória;
- empresa detentora do registro;
- princípio ativo;
- classe terapêutica;
- apresentações comercializadas;
- dados econômicos publicados pela CMED;
- última atualização localizada no Bulário Eletrônico;
- histórico documental do Bulário;
- ocorrências públicas de fiscalização;
- linha do tempo integrada;
- links para consultas oficiais da Anvisa.

Além da consulta individual, o projeto disponibiliza:

- páginas agregadas por empresa;
- páginas agregadas por princípio ativo;
- indicadores de transparência;
- monitor de atualizações;
- downloads das fontes originais;
- conjuntos derivados para reutilização.

---

## Perfis de visualização

### Paciente / cidadão

Apresentação simplificada das informações essenciais:

- registro ativo ou inativo;
- empresa;
- princípio ativo;
- apresentações;
- atualização do Bulário;
- existência de preço publicado na CMED;
- ocorrências públicas de fiscalização.

Essa visualização não fornece diagnóstico, orientação terapêutica ou recomendação de uso de medicamentos.

### Profissional

Apresentação técnica ampliada, incluindo:

- processo regulatório;
- vencimento do registro;
- identificadores das apresentações;
- PF, PMC e PMVG;
- expedientes;
- histórico documental;
- informações de fiscalização;
- linha do tempo integrada.

---

## Fontes de dados

O processamento utiliza exclusivamente dados abertos.

| Camada | Fonte |
|---|---|
| Medicamentos | Anvisa — Dados Abertos de Medicamentos |
| CMED | Lista de preços — PF e PMC |
| CMED Governo | Lista de preços — PF e PMVG |
| Bulário atual | Consulta de produtos do Bulário Eletrônico |
| Histórico do Bulário | Consulta de documentos do Bulário Eletrônico |
| Fiscalização | Produtos irregulares e ações de fiscalização |

Os arquivos originais utilizados pelo projeto são mantidos em:

[`public/fontes/`](public/fontes/)

A descrição completa das fontes, esquemas, campos, chaves e regras de relacionamento está em:

[`docs/DADOS_E_METODOLOGIA.md`](docs/DADOS_E_METODOLOGIA.md)

---

## Modelo de relacionamento

A integração utiliza identificadores com funções distintas:

| Identificador | Uso |
|---|---|
| **9 dígitos** | identifica o medicamento |
| **13 dígitos** | identifica a apresentação comercializada |
| **Código GGREM** | identifica o registro econômico da CMED |

O relacionamento entre apresentação e medicamento é realizado pelos nove primeiros dígitos do registro de 13 dígitos.

Registros sem chave válida não são associados por aproximação apenas com base em nome, empresa ou categoria.

---

## CMED

A indicação **“Possui preço publicado na CMED”** significa que foi localizado ao menos um registro correspondente nas listas públicas da CMED.

Os valores exibidos podem incluir:

- PF — Preço Fábrica;
- PMC — Preço Máximo ao Consumidor;
- PMVG — Preço Máximo de Venda ao Governo.

Esses valores são apresentados exclusivamente como informação pública oficial e não representam oferta comercial, cotação, promoção ou preço necessariamente praticado no mercado.

---

## Bulário Eletrônico

A plataforma utiliza duas camadas distintas:

**Última atualização**
: representa o documento mais recente localizado para o medicamento.

**Histórico**
: reúne documentos e atualizações disponíveis na base histórica integrada.

Os arquivos originais do Bulário não possuem cabeçalho. O projeto aplica nomes funcionais internos às colunas posicionais, documentados na metodologia.

---

## Fiscalização

As ocorrências são relacionadas de forma conservadora quando existe correspondência válida com o registro do medicamento.

A ausência de ocorrência na base integrada **não significa comprovação de regularidade sanitária**.

---

## Transparência e reutilização

O projeto disponibiliza duas camadas de dados:

### Fontes originais

Arquivos públicos utilizados diretamente no processamento.

### Dados derivados

Conjuntos estruturados produzidos pelo pipeline do Medicamento Aberto para facilitar:

- pesquisa;
- análise;
- jornalismo de dados;
- desenvolvimento de aplicações;
- estudos acadêmicos;
- controle social;
- novas iniciativas de reutilização de dados públicos.

---

## Arquitetura

```text
Fontes oficiais de dados abertos
            │
            ▼
      public/fontes/
            │
            ▼
      Python + pandas
            │
            ▼
normalização e validação
            │
            ▼
relacionamento entre bases
            │
            ▼
       public/data/
            │
            ▼
 React + TypeScript + Vite
            │
            ▼
           Vercel
```

A aplicação é estática e não depende de banco de dados ou API paga para funcionamento.

---

## Qualidade e rastreabilidade

O pipeline gera artefatos de controle e auditoria em `public/data/`, incluindo:

- manifesto da publicação;
- relatório de qualidade;
- relatório de esquema;
- catálogo de fontes;
- checksums;
- dicionário de dados;
- conjuntos derivados.

Princípios adotados:

- preservação das fontes originais;
- relacionamento por chaves explícitas;
- ausência de correspondência aproximada silenciosa;
- validação antes da publicação;
- rastreabilidade entre fonte e dado derivado;
- versionamento dos dados utilizados.

---

## Atualização automática

O projeto possui automação via GitHub Actions.

Workflow principal:

[`.github/workflows/update-data.yml`](.github/workflows/update-data.yml)

Fluxo:

```text
baixar fontes oficiais
        ↓
validar arquivos
        ↓
detectar mudanças
        ↓
reconstruir dados
        ↓
executar testes
        ↓
versionar alterações
        ↓
publicar nova versão
```

Quando não há mudança nas fontes, não é criado commit desnecessário.

---

## Acessibilidade

A interface contempla:

- navegação por teclado;
- foco visível;
- responsividade;
- estados não dependentes exclusivamente de cor;
- suporte a `prefers-reduced-motion`;
- conteúdo adaptado ao perfil de visualização;
- acesso sem cadastro;
- integração com o **VLibras Widget**.

O VLibras é carregado a partir do serviço oficial do Governo Federal.

---

## Tecnologias

### Front-end

- React
- TypeScript
- Vite
- React Router
- Lucide Icons

### Processamento de dados

- Python
- pandas
- requests

### Infraestrutura

- GitHub
- GitHub Actions
- Vercel

---

## Execução local

### Requisitos

- Python 3.12+
- Node.js 22+
- npm

### Instalação

```bash
python -m pip install -r requirements.txt
npm install
```

### Ambiente de desenvolvimento

```bash
npm run dev
```

### Validar os dados publicados

```bash
npm run data:verify
```

### Atualizar as fontes e reconstruir os dados

```bash
npm run data:update
```

### Executar testes do pipeline

```bash
npm run test:pipeline
```

### Build de produção

```bash
npm run build
```

---

## Estrutura do repositório

```text
.
├── .github/
│   └── workflows/
├── docs/
├── public/
│   ├── brand/
│   ├── data/
│   └── fontes/
├── scripts/
├── src/
├── tests/
├── package.json
├── requirements.txt
└── vercel.json
```

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [Dados e metodologia](docs/DADOS_E_METODOLOGIA.md) | Fontes, campos, chaves, regras de relacionamento e qualidade |
| [Guia de uso](docs/GUIA_DE_USO.md) | Orientações para consulta e interpretação |
| [Identidade visual](docs/IDENTIDADE_VISUAL.md) | Diretrizes de marca e aplicação visual |

---

## Autoria

**Diórger Bretas**  
Farmacêutico · Analista Regulatório · Desenvolvedor Full Stack

[Portfólio](https://diorgerb.github.io/Portfolio/)

---

## Aviso institucional

O **Medicamento Aberto** é uma iniciativa independente de organização e reutilização de dados públicos.

Não possui vínculo institucional com a Agência Nacional de Vigilância Sanitária — Anvisa ou com a Câmara de Regulação do Mercado de Medicamentos — CMED.

Todas as informações devem ser confirmadas nas respectivas fontes oficiais quando utilizadas para fins regulatórios, sanitários, profissionais ou decisórios.
