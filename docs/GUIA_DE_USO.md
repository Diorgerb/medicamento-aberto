# Guia de uso — Medicamento Aberto

O Medicamento Aberto oferece duas formas de visualização. A escolha altera a organização e a densidade da informação, mas não modifica os dados apresentados.

## Paciente / cidadão

Use esta visualização para perguntas objetivas sobre informações abertas do medicamento:

- o registro consta como **Ativo** ou **Inativo**?
- qual empresa aparece vinculada ao medicamento?
- qual é o princípio ativo?
- quais apresentações comercializadas foram localizadas?
- quando houve a última atualização no Bulário?
- existe preço publicado na lista da CMED?
- há alerta ou ocorrência de fiscalização relacionada?

A plataforma não informa qual tratamento deve ser utilizado, não recomenda substituição de medicamentos, não define doses e não interpreta ausência de ocorrência como prova de regularidade.

## Profissional

Use esta visualização para análise regulatória, pesquisa, assistência farmacêutica e acompanhamento técnico:

- registro, categoria, situação, processo e vencimento;
- apresentações e seus identificadores;
- PF, PMC e PMVG por faixa tributária;
- última atualização e histórico do Bulário;
- expedientes e situação documental;
- linha do tempo integrada;
- detalhes de alertas e ocorrências de fiscalização.

## Medicamentos

A página de medicamentos permite pesquisar e filtrar por diferentes dimensões. A situação do registro permanece visível nos cards e nas áreas internas do medicamento.

## Empresas e princípios ativos

As páginas de Empresas e Princípios ativos reutilizam os filtros rápidos do catálogo de Medicamentos. Os filtros são aplicados aos medicamentos associados à entidade selecionada.

## Transparência

A página `/transparencia` apresenta indicadores agregados sobre:

- situação dos registros;
- cobertura das diferentes dimensões de dados;
- categorias regulatórias;
- presença de Bulário, CMED, apresentações e fiscalização.

Os indicadores mostram o que foi localizado nas fontes processadas e não devem ser interpretados além do escopo dessas fontes.

## Atualizações

A página `/atualizacoes` reúne exclusivamente:

- **Bulário** — atualizações e documentos datados;
- **Alertas** — alertas e ocorrências datadas de fiscalização.

Mudanças de situação do registro, presença na CMED ou quantidade de apresentações não são tratadas como “Atualizações” nessa página.

## Acessibilidade e VLibras

O Medicamento Aberto incorpora o **VLibras Widget**, recurso oficial que oferece tradução automática de conteúdos em português para a Língua Brasileira de Sinais (Libras). O botão do VLibras fica disponível de forma flutuante durante a navegação.

Além do VLibras, a interface foi projetada com foco visível, navegação por teclado, layout responsivo, estados que não dependem somente de cor e suporte a redução de movimentos.

O VLibras depende de conexão com `vlibras.gov.br` e pode ter comportamento condicionado à disponibilidade do serviço oficial e à compatibilidade do navegador.

## Reúso

A página `/reutilize` permite baixar:

- os seis arquivos originais de dados abertos utilizados pela plataforma;
- conjuntos derivados e consolidados pelo Medicamento Aberto.

A publicação também mantém catálogos JSON estáticos que podem ser utilizados por outras análises e aplicações.

## Interpretação responsável

- **Registro Ativo/Inativo:** reproduz a situação informada na base de medicamentos.
- **Possui preço publicado na CMED:** significa que há registro correspondente nas listas CMED processadas.
- **Sem ocorrência localizada:** não significa certificação de regularidade.
- **Dados econômicos:** PF, PMC e PMVG não representam necessariamente preços efetivamente praticados.

Para decisões regulatórias, terapêuticas ou clínicas, consulte sempre as fontes e orientações oficiais aplicáveis.

## Consultas oficiais da Anvisa

Na página de cada medicamento, o número de registro e o número do processo possuem atalhos para a consulta oficial de medicamentos da Anvisa. Na área **Bulário**, quando há um registro sanitário válido, há também um atalho para abrir o Bulário Eletrônico já filtrado por esse registro.

Esses atalhos complementam a experiência integrada do Medicamento Aberto e permitem conferir a informação diretamente nos sistemas oficiais.
