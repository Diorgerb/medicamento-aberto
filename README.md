# Medicamento Aberto

**Plataforma integrada de dados abertos sobre medicamentos no Brasil.**

O **Medicamento Aberto** reúne, relaciona e apresenta em uma única experiência informações de dados abertos da Anvisa e da CMED que normalmente precisam ser consultadas em fontes separadas.

A plataforma foi criada para facilitar a consulta por pacientes e cidadãos, apoiar análises profissionais e ampliar o reúso de dados abertos por pesquisadores, desenvolvedores, jornalistas e iniciativas de controle social.

## O que a plataforma integra

- situação do registro do medicamento;
- categoria regulatória, processo, empresa e princípio ativo;
- apresentações comercializadas;
- presença e parâmetros publicados nas listas da CMED;
- última atualização disponível no Bulário Eletrônico;
- histórico de atualizações do Bulário;
- alertas e ocorrências de fiscalização relacionados ao medicamento, quando localizados;
- indicadores agregados de transparência e cobertura das informações.

## Perfis de visualização

A plataforma oferece duas formas de leitura dos mesmos dados.

### Paciente / cidadão

Prioriza linguagem simples e informações de consulta rápida, como:

- registro **Ativo** ou **Inativo**;
- empresa e princípio ativo;
- apresentações comercializadas;
- última atualização no Bulário;
- indicação de existência de preço publicado na CMED;
- alertas e ocorrências de fiscalização, quando existentes.

Essa visualização não fornece orientação terapêutica, diagnóstico, recomendação de uso ou substituição de medicamentos.

### Profissional

Mantém as informações essenciais e acrescenta maior densidade técnica, incluindo:

- processo e vencimento do registro;
- identificadores de apresentações;
- PF, PMC e PMVG por faixa tributária;
- expedientes e histórico documental do Bulário;
- linha do tempo integrada;
- detalhes das ocorrências de fiscalização.

## Áreas da plataforma

### Medicamentos

Busca e filtros por nome, registro, processo, empresa, princípio ativo, categoria regulatória, situação do registro, Bulário, CMED e fiscalização.

### Empresas

Exploração das empresas e dos medicamentos associados, com os mesmos filtros rápidos utilizados no catálogo de medicamentos.

### Princípios ativos

Consulta transversal por princípio ativo, com indicadores e filtros sobre os medicamentos relacionados.

### Transparência

Indicadores agregados de situação dos registros, cobertura das diferentes dimensões de dados e distribuição por categoria regulatória.

### Atualizações

Área dedicada **exclusivamente** a:

- atualizações do Bulário Eletrônico;
- alertas e ocorrências de fiscalização.

Alterações de situação do registro, presença na CMED ou quantidade de apresentações não são apresentadas como “Atualizações”.

### Reutilize os dados

Disponibiliza duas camadas de download:

1. **arquivos originais de dados abertos** utilizados pela plataforma;
2. **conjuntos derivados** produzidos pela integração do Medicamento Aberto.

## Fontes de dados abertos

O processamento utiliza exclusivamente seis arquivos de dados abertos:

1. medicamentos;
2. CMED — PF e PMC;
3. CMED — PF e PMVG;
4. Bulário — última atualização;
5. Bulário — histórico de documentos e atualizações;
6. fiscalização e produtos irregulares.

Os arquivos originais utilizados pela publicação ficam versionados em [`public/fontes/`](public/fontes/) e são também disponibilizados para download pela própria aplicação.

Os nomes exatos dos arquivos, esquemas, regras de relacionamento e critérios de qualidade estão documentados em [`docs/DADOS_E_METODOLOGIA.md`](docs/DADOS_E_METODOLOGIA.md).

## Estrutura de dados

A modelagem adota três identificadores com papéis distintos:

- **9 dígitos**: medicamento;
- **13 dígitos**: apresentação comercializada;
- **CÓDIGO GGREM**: registro econômico da CMED associado à apresentação.

O vínculo entre apresentação e medicamento é feito pelos nove primeiros dígitos do registro de 13 dígitos.

Produtos sem registro sanitário válido de nove dígitos são preservados como entidades distintas e não são fundidos apenas por nome, empresa ou categoria.

## CMED

“**Possui preço publicado na CMED**” significa exclusivamente que existe ao menos um registro das listas CMED relacionado ao medicamento.

A plataforma pode apresentar PF, PMC e PMVG como parâmetros publicados pela CMED. Esses valores não são tratados como oferta, promoção, cotação, recomendação comercial ou preço efetivamente praticado no varejo.

## Bulário Eletrônico

- **Bulário — última atualização** representa o estado mais recente localizado para o medicamento;
- **Bulário — histórico** reúne as atualizações/documentos disponíveis no histórico integrado.

Os dois arquivos de origem não possuem cabeçalho. O projeto aplica nomes funcionais internos às posições, documentados na metodologia técnica.

## Fiscalização

Ocorrências são relacionadas de forma conservadora pelo registro do medicamento quando a correspondência é válida.

A ausência de ocorrência na base integrada **não comprova regularidade sanitária**.

## Arquitetura

```text
Dados abertos originais
        ↓
public/fontes/
        ↓
Python + pandas
        ↓
normalização + validação + relacionamentos
        ↓
public/data/
        ↓
React + TypeScript + Vite
        ↓
Vercel
```

A aplicação é estática e não exige banco de dados ou API paga para funcionar.

## Atualização automática dos dados

O workflow [`.github/workflows/update-data.yml`](.github/workflows/update-data.yml) executa diariamente e também pode ser disparado manualmente.

Fluxo:

```text
Baixar novamente as seis fontes
        ↓
substituir public/fontes/
        ↓
validar estrutura e detectar mudanças
        ↓
regenerar public/data/ quando necessário
        ↓
executar validações e testes
        ↓
commitar fontes + base processada
        ↓
push
        ↓
novo deploy pela Vercel
```

Quando nenhuma fonte muda, o workflow preserva a publicação existente e não cria commit desnecessário.

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

### Validar a base já publicada

```bash
npm run data:verify
```

### Executar o site

```bash
npm run dev
```

### Atualizar as fontes e reconstruir a base

```bash
npm run data:update
```

Esse comando:

1. baixa novamente os arquivos para `public/fontes/`;
2. diagnostica o esquema da base principal;
3. reconstrói `public/data/`;
4. valida a publicação.

#### Certificados HTTPS no Windows

O downloader mantém a validação TLS habilitada e utiliza `truststore` para consultar o repositório nativo de certificados do sistema operacional. Isso evita diferenças entre a confiança do navegador e a do Python em ambientes Windows ou redes com certificados corporativos.

Se ocorrer `CERTIFICATE_VERIFY_FAILED`, atualize o `pip`, reinstale as dependências e tente novamente:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
npm run data:update
```

Não é necessário nem recomendado desabilitar a verificação SSL.

### Testar o pipeline

```bash
npm run test:pipeline
```

### Build de produção

```bash
npm run build
```

## Estrutura principal

```text
.
├── .github/workflows/
│   ├── quality.yml
│   └── update-data.yml
├── docs/
│   ├── DADOS_E_METODOLOGIA.md
│   ├── GUIA_DE_USO.md
│   ├── IDENTIDADE_VISUAL.md
│   └── manual-identidade-visual.png
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

## Qualidade e reprodutibilidade

O processamento gera artefatos de auditoria em `public/data/`, incluindo:

- manifesto da publicação;
- dicionário de dados;
- relatório de qualidade;
- relatório de esquema;
- catálogo das fontes e checksums;
- conjuntos derivados para download.

Os cruzamentos evitam correspondências aproximadas silenciosas. Quando uma relação não pode ser sustentada pela chave definida, ela permanece não vinculada.

## Acessibilidade

A interface foi estruturada para:

- navegação por teclado;
- foco visível;
- layout responsivo;
- estados não dependentes somente de cor;
- suporte a `prefers-reduced-motion`;
- linguagem adaptada ao perfil de visualização;
- funcionamento sem cadastro;
- **VLibras Widget**, oferecendo tradução automática de conteúdos em português para a Língua Brasileira de Sinais (Libras).

O VLibras é carregado a partir do serviço oficial `https://vlibras.gov.br` e, por ser um recurso externo, depende de conexão com esse domínio para funcionar. A integração segue a documentação oficial do VLibras Widget.

## Documentação

- [Dados e metodologia](docs/DADOS_E_METODOLOGIA.md)
- [Guia de uso](docs/GUIA_DE_USO.md)
- [Identidade visual](docs/IDENTIDADE_VISUAL.md)

## Autoria

**Diórger Bretas**  
Farmacêutico, Analista Regulatório e Desenvolvedor Full Stack.

Portfólio: https://diorgerb.github.io/Portfolio/

## Aviso

O Medicamento Aberto organiza e relaciona dados abertos para facilitar consulta, análise e reúso. A plataforma não substitui atos, documentos, sistemas, orientações ou manifestações oficiais da Anvisa e da CMED.
