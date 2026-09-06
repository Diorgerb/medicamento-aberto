import { Accessibility, BookOpenCheck, Building2, CheckCircle2, ExternalLink, HeartPulse, Keyboard, Languages, Newspaper, Pill, Scale, ShieldAlert, ShieldCheck, Sparkles, Stethoscope, University, UserRound } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { ErrorState } from '../components/ErrorState'
import { Loading } from '../components/Loading'
import { getManifest, getQualityReport, getSources } from '../lib/data'
import { formatNumber, humanDate } from '../lib/format'
import type { Manifest, QualityReport, SourceCatalogItem } from '../types/data'

export function DataPage() {
  const [manifest,setManifest]=useState<Manifest|null>(null)
  const [sources,setSources]=useState<SourceCatalogItem[]>([])
  const [quality,setQuality]=useState<QualityReport|null>(null)
  const [error,setError]=useState('')
  const [loading,setLoading]=useState(true)
  useEffect(()=>{Promise.all([getManifest(),getSources(),getQualityReport()]).then(([m,s,q])=>{setManifest(m);setSources(s);setQuality(q)}).catch((err)=>setError(String(err))).finally(()=>setLoading(false))},[])

  const officialLinks = useMemo(() => {
    const first = (keys:string[]) => sources.find((source)=>keys.includes(source.key) && source.official_page_url)?.official_page_url || ''
    return {
      medicines: first(['medicamentos']),
      cmed: first(['cmed_consumidor','cmed_governo']),
      leaflets: first(['bula_produto','bula_documento']),
      inspection: first(['irregulares']),
    }
  }, [sources])

  if(loading)return <section className="page-section"><div className="container"><Loading/></div></section>
  if(error||!manifest)return <section className="page-section"><div className="container"><ErrorState message={error||'Informações da plataforma não disponíveis.'}/></div></section>

  const q=quality?.metrics??{}

  return <section className="page-section about-page"><div className="container narrow-wide">
    <div className="page-heading about-heading"><div><div className="eyebrow">Sobre o Medicamento Aberto</div><h1>Dados abertos, organizados para serem úteis.</h1><p>O Medicamento Aberto integra dados abertos sobre medicamentos em uma experiência única de consulta, conectando regularização, apresentações, Bulário, CMED e fiscalização.</p></div></div>

    <section className="about-highlight">
      <div><Sparkles/><span><strong>Uma busca, várias dimensões</strong><small>Informações que antes exigiam consultas separadas passam a ser visualizadas em conjunto.</small></span></div>
      <div><ShieldCheck/><span><strong>Contexto regulatório sempre visível</strong><small>A situação do registro acompanha o medicamento em toda a navegação.</small></span></div>
      <div><CheckCircle2/><span><strong>Atualização rastreável</strong><small>A plataforma informa quando a base integrada foi processada e preserva metadados técnicos para auditoria.</small></span></div>
    </section>

    <div className="data-status public-data-status"><div><span>Fontes integradas</span><strong>{sources.length.toLocaleString('pt-BR')}</strong></div><div><span>Última atualização</span><strong>{humanDate(manifest.generatedAt)}</strong></div><div><span>Medicamentos integrados</span><strong>{formatNumber(manifest.counts.products)}</strong></div></div>

    <div className="section-heading about-section-heading"><span>O que você encontra</span><h2>Uma visão integrada do medicamento</h2><p>Cada área foi organizada para responder rapidamente às perguntas mais comuns de consulta e acompanhamento.</p></div>
    <div className="feature-grid about-feature-grid">
      <AboutFeature icon={<Pill/>} title="Regularização" text="Registro, situação, categoria regulatória, processo, empresa e princípio ativo."/>
      <AboutFeature icon={<Building2/>} title="Apresentações" text="Apresentações comercializadas e suas principais características."/>
      <AboutFeature icon={<Scale/>} title="CMED" text="Identificação de medicamentos com preço publicado e parâmetros econômicos oficiais."/>
      <AboutFeature icon={<BookOpenCheck/>} title="Bulário Eletrônico" text="Última atualização e histórico de atualizações disponíveis para o medicamento."/>
      <AboutFeature icon={<ShieldAlert/>} title="Fiscalização" text="Ocorrências públicas relacionadas ao medicamento, quando localizadas."/>
      <AboutFeature icon={<ShieldCheck/>} title="Situação do registro" text="Indicador Ativo ou Inativo destacado em cards, buscas e páginas de detalhe."/>
    </div>

    <div className="section-heading about-section-heading"><span>Para quem é</span><h2>Diferentes públicos, diferentes perguntas</h2><p>A plataforma mantém os mesmos dados oficiais, mas organiza a experiência para necessidades distintas.</p></div>
    <div className="audience-grid">
      <Audience icon={<HeartPulse/>} title="Paciente / cidadão" text="Para verificar informações de dados abertos sem precisar dominar a linguagem regulatória." items={["Conferir se o registro consta como ativo ou inativo","Identificar empresa, princípio ativo e apresentações","Entender se existe atualização no Bulário","Ver se há preço publicado na CMED com explicação do que isso significa","Localizar ocorrências públicas de fiscalização quando houver"]}/>
      <Audience icon={<Stethoscope/>} title="Profissional de saúde ou regulatório" text="Para aprofundar a consulta e cruzar diferentes dimensões do medicamento." items={["Consultar categoria, registro, processo e vencimento","Analisar apresentações comercializadas","Consultar PF, PMC e PMVG por tributação","Acompanhar histórico do Bulário e expedientes","Relacionar eventos na linha do tempo integrada"]}/>
      <Audience icon={<University/>} title="Pesquisador" text="Para explorar padrões da base e reutilizar conjuntos derivados em estudos." items={["Analisar categorias e princípios ativos","Estudar cobertura entre diferentes fontes","Baixar dados consolidados para novas análises"]}/>
      <Audience icon={<Newspaper/>} title="Jornalismo e controle social" text="Para investigar dados abertos com contexto e rastreabilidade." items={["Acompanhar registros ativos e inativos","Acompanhar atualizações do Bulário e alertas de fiscalização","Explorar ocorrências de fiscalização e cobertura pública"]}/>
    </div>

    <div className="section-heading about-section-heading"><span>Cobertura</span><h2>Indicadores da base integrada</h2></div>
    <div className="quality-grid public-quality-grid">
      <Quality label="Medicamentos" value={q.products}/>
      <Quality label="Apresentações comercializadas" value={q.commercialPresentations13}/>
      <Quality label="Com preço publicado na CMED" value={q.productsWithCmed}/>
      <Quality label="Com atualização atual no Bulário" value={q.productsWithLeaflet}/>
      <Quality label="Com histórico no Bulário" value={q.productsWithLeafletHistory}/>
      <Quality label="Com ocorrência de fiscalização" value={q.productsWithInspectionOccurrence}/>
    </div>

    <div className="section-heading about-section-heading"><span>Fontes de dados abertos</span><h2>Dados abertos de referência</h2><p>As informações apresentadas são derivadas de fontes oficiais de dados abertos. Para conferência normativa ou tomada de decisão regulatória, consulte sempre o órgão responsável.</p></div>
    <div className="official-source-grid">
      <OfficialSource icon={<Pill/>} title="Medicamentos" text="Dados abertos de regularização de medicamentos da Anvisa." href={officialLinks.medicines}/>
      <OfficialSource icon={<Scale/>} title="CMED" text="Listas oficiais de preços máximos e parâmetros econômicos." href={officialLinks.cmed}/>
      <OfficialSource icon={<BookOpenCheck/>} title="Bulário Eletrônico" text="Informações de atualização e histórico de documentos do Bulário." href={officialLinks.leaflets}/>
      <OfficialSource icon={<ShieldAlert/>} title="Fiscalização" text="Dados abertos sobre ações e ocorrências de fiscalização sanitária." href={officialLinks.inspection}/>
    </div>


    <div className="section-heading about-section-heading"><span>Acessibilidade</span><h2>Informação aberta também precisa ser acessível.</h2><p>A plataforma combina recursos de navegação acessível com o VLibras, serviço oficial que oferece tradução automática de conteúdos em português para Libras.</p></div>
    <div className="accessibility-about-grid">
      <AboutFeature icon={<Languages/>} title="VLibras" text="O widget oficial fica disponível em todas as páginas para apoiar o acesso de pessoas surdas ao conteúdo textual."/>
      <AboutFeature icon={<Keyboard/>} title="Navegação por teclado" text="Links, controles e áreas interativas mantêm foco visível e podem ser percorridos sem depender apenas do mouse."/>
      <AboutFeature icon={<Accessibility/>} title="Leitura inclusiva" text="A interface usa linguagem por perfil, estados que não dependem somente de cor e comportamento responsivo em diferentes telas."/>
    </div>
    <p className="accessibility-source-note">O VLibras é um recurso externo mantido pelo Governo Federal e requer conexão com o serviço <strong>vlibras.gov.br</strong> para funcionar. <a href="https://vlibras.gov.br/doc/widget/installation/webpageintegration.html" target="_blank" rel="noreferrer">Consultar documentação oficial <ExternalLink size={13}/></a></p>

    <div className="section-heading about-section-heading"><span>Projeto e autoria</span><h2>Quem criou o Medicamento Aberto</h2><p>A plataforma foi idealizada e desenvolvida para aproximar dados regulatórios públicos de diferentes perfis de usuário, combinando conhecimento farmacêutico, regulatório e desenvolvimento de software.</p></div>
    <article className="creator-card">
      <span className="creator-icon"><UserRound/></span>
      <div className="creator-copy"><span className="eyebrow">Criador</span><h3>Diórger Bretas</h3><p>Farmacêutico, Analista Regulatório e Desenvolvedor Full Stack. Atua na interseção entre ciência regulatória, dados e tecnologia.</p><a href="https://diorgerb.github.io/Portfolio/" target="_blank" rel="noreferrer">Conhecer o portfólio <ExternalLink size={15}/></a></div>
    </article>

    <div className="public-disclaimer"><ShieldCheck/><div><strong>Importante</strong><p>O Medicamento Aberto organiza e relaciona dados abertos para facilitar a consulta. A plataforma não substitui atos, documentos, sistemas ou manifestações oficiais da Anvisa e da CMED. A ausência de uma ocorrência não deve ser interpretada como certificação de regularidade.</p></div></div>
  </div></section>
}

function AboutFeature({icon,title,text}:{icon:React.ReactNode;title:string;text:string}) { return <article className="feature-card"><span className="feature-icon">{icon}</span><h3>{title}</h3><p>{text}</p></article> }
function Quality({label,value}:{label:string;value?:number}) { return <div className="quality-card"><span>{label}</span><strong>{typeof value==='number'?formatNumber(value):'—'}</strong></div> }
function OfficialSource({icon,title,text,href}:{icon:React.ReactNode;title:string;text:string;href:string}) { return <article className="official-source-card"><span className="official-source-icon">{icon}</span><div><h3>{title}</h3><p>{text}</p>{href&&<a href={href} target="_blank" rel="noreferrer">Consultar fonte oficial <ExternalLink size={14}/></a>}</div></article> }

function Audience({icon,title,text,items}:{icon:React.ReactNode;title:string;text:string;items:string[]}) { return <article className="audience-card"><span className="audience-icon">{icon}</span><h3>{title}</h3><p>{text}</p><ul>{items.map((item)=><li key={item}>{item}</li>)}</ul></article> }
