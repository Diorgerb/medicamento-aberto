import { Braces, Building2, Download, FileArchive, FileSpreadsheet, Pill, Tags } from 'lucide-react'
import { Link } from 'react-router-dom'

const originalSources = [
  { title: 'Medicamentos', text: 'Arquivo aberto de medicamentos utilizado como base regulatória principal.', href: '/fontes/DADOS_ABERTOS_MEDICAMENTOS.csv' },
  { title: 'CMED — PF e PMC', text: 'Arquivo aberto com preços publicados pela CMED para consumidor.', href: '/fontes/TA_PRECO_MEDICAMENTO.csv' },
  { title: 'CMED — PF e PMVG', text: 'Arquivo aberto com parâmetros de preços para vendas ao governo.', href: '/fontes/TA_PRECO_MEDICAMENTO_GOV.csv' },
  { title: 'Bulário — última atualização', text: 'Arquivo aberto com a atualização mais recente do produto no Bulário Eletrônico.', href: '/fontes/TA_CONSULTA_BULA_PRODUTO.CSV' },
  { title: 'Bulário — histórico', text: 'Arquivo aberto com o histórico de documentos e atualizações do Bulário Eletrônico.', href: '/fontes/TA_CONSULTA_BULA_DOCUMENTO.CSV' },
  { title: 'Fiscalização e alertas', text: 'Arquivo aberto com resultados publicados de produtos irregulares e medidas de fiscalização.', href: '/fontes/TA_CONSULTA_PRODUTOS_IRREGULARES_RESULTADO.CSV' },
]

const derivedDownloads = [
  {title:'Medicamentos consolidados',text:'Uma linha por medicamento, com os principais indicadores integrados.',href:'/data/downloads/medicamentos.csv.gz',icon:<Pill/>},
  {title:'Apresentações comercializadas',text:'Apresentações vinculadas aos medicamentos, preservando o registro próprio da apresentação.',href:'/data/downloads/apresentacoes-comercializadas.csv.gz',icon:<FileArchive/>},
  {title:'Empresas',text:'Catálogo de empresas com contagens de medicamentos e apresentações.',href:'/data/downloads/empresas.csv.gz',icon:<Building2/>},
  {title:'Princípios ativos',text:'Catálogo de princípios ativos e sua presença na base integrada.',href:'/data/downloads/principios-ativos.csv.gz',icon:<Tags/>},
]

export function ReusePage(){return <section className="page-section reuse-page"><div className="container">
  <div className="page-heading"><div><div className="eyebrow">Reúso que gera novo reúso</div><h1>Reutilize os dados</h1><p>Consulte as fontes abertas originais utilizadas pela plataforma e baixe também conjuntos consolidados produzidos pelo Medicamento Aberto.</p></div></div>

  <section className="reuse-section">
    <div className="section-heading"><div><div className="eyebrow">Fontes de dados abertos</div><h2>Arquivos originais versionados</h2><p>Estes são os seis arquivos utilizados pelo processamento. O GitHub preserva a cópia utilizada na publicação e a atualização automática substitui os arquivos quando a fonte aberta muda.</p></div></div>
    <div className="reuse-grid">{originalSources.map((item)=><a className="reuse-card" href={item.href} download key={item.title}><span><FileSpreadsheet/></span><div><h3>{item.title}</h3><p>{item.text}</p><strong><Download size={15}/> Baixar CSV original</strong></div></a>)}</div>
  </section>

  <div className="reuse-principle"><Braces/><div><h2>Dados derivados e novamente abertos</h2><p>Os conjuntos abaixo são produzidos pela integração do Medicamento Aberto. Eles complementam as fontes originais e reduzem o trabalho necessário para relacionar informações dispersas.</p></div></div>
  <div className="reuse-grid">{derivedDownloads.map((item)=><a className="reuse-card" href={item.href} download key={item.title}><span>{item.icon}</span><div><h3>{item.title}</h3><p>{item.text}</p><strong><Download size={15}/> Baixar CSV compactado</strong></div></a>)}</div>

  <section className="api-like-card"><div><div className="eyebrow">Para desenvolvedores</div><h2>JSONs estáticos como camada de consulta</h2><p>A publicação também mantém catálogos e detalhes em JSON. Isso permite criar protótipos e análises sem exigir uma API paga ou banco de dados próprio.</p></div><pre><code>{`/data/catalog/products.json\n/data/catalog/companies.json\n/data/catalog/ingredients.json\n/data/products/{bucket}.json`}</code></pre></section>
  <div className="reuse-note"><strong>Documentação técnica</strong><p>Esquemas, regras de relacionamento, critérios de qualidade e limites de interpretação permanecem documentados separadamente do site público.</p><Link className="text-link" to="/sobre">Entender a plataforma</Link></div>
</div></section>}
