import { Accessibility, ArrowRight, BarChart3, BookOpenCheck, Building2, ExternalLink, FileText, HeartPulse, Pill, RefreshCw, SearchCheck, ShieldCheck, Stethoscope, Tags } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorState } from '../components/ErrorState'
import { Loading } from '../components/Loading'
import { SearchBox } from '../components/SearchBox'
import { BrandMark } from '../components/Brand'
import { ViewModeSelector } from '../components/ViewModeSelector'
import { useViewMode } from '../components/ViewModeContext'
import { getManifest } from '../lib/data'
import { formatNumber, humanDate } from '../lib/format'
import type { Manifest } from '../types/data'

export function HomePage() {
  const { mode } = useViewMode()
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { getManifest().then(setManifest).catch((err) => setError(String(err))) }, [])

  return <>
    <section className="hero">
      <div className="container hero-grid">
        <div className="hero-copy-block">
          <div className="eyebrow">Informação pública sobre medicamentos</div>
          <h1>Tudo o que você precisa consultar sobre medicamentos, em um só lugar.</h1>
          <p className="hero-copy">Encontre informações de regularização, apresentações comercializadas, empresas, princípios ativos, Bulário, CMED e fiscalização em uma navegação simples e integrada.</p>
          <SearchBox large/>
          <p className="hero-hints">Busque por medicamento, princípio ativo, registro, processo, empresa ou CNPJ.</p>
        </div>
        <aside className="hero-brand-panel" aria-label="Identidade e princípios do projeto">
          <div className="hero-brand-symbol"><BrandMark size={132}/></div>
          <div className="hero-brand-copy"><strong>Medicamento <span>Aberto</span></strong><small>Dados públicos para uma saúde mais transparente</small></div>
          <div className="hero-proof">
            <div><SearchCheck/><span><strong>Busca inteligente</strong><small>Encontre medicamentos, empresas e princípios ativos</small></span></div>
            <div><ShieldCheck/><span><strong>Contexto regulatório</strong><small>Situação do registro sempre em destaque</small></span></div>
            <div><BookOpenCheck/><span><strong>Histórico integrado</strong><small>Bulário, CMED e fiscalização no mesmo medicamento</small></span></div>
          </div>
        </aside>
      </div>
    </section>

    <section className="profile-choice-section">
      <div className="container">
        <div className="profile-choice-head"><div><div className="eyebrow">Uma plataforma, duas formas de visualizar</div><h2>Escolha a leitura mais útil para você.</h2><p>A mesma informação pública pode ser apresentada com linguagem simples ou com maior densidade técnica. Você pode trocar a qualquer momento.</p></div><ViewModeSelector/></div>
        <div className="profile-use-grid">
          <article className={`profile-use-card ${mode==='patient'?'selected':''}`}><span><HeartPulse/></span><div><small>Paciente / cidadão</small><h3>Entenda o essencial sem precisar conhecer termos regulatórios.</h3><ul><li>Confirme se o registro consta como ativo ou inativo.</li><li>Veja empresa, princípio ativo e apresentações localizadas.</li><li>Confira quando houve atualização no Bulário.</li><li>Saiba se existe preço publicado na CMED, com explicações simples.</li><li>Identifique ocorrências públicas de fiscalização quando houver.</li></ul><p className="profile-use-warning">Não substitui orientação médica, farmacêutica ou a leitura da bula.</p></div></article>
          <article className={`profile-use-card ${mode==='professional'?'selected':''}`}><span><Stethoscope/></span><div><small>Profissional</small><h3>Explore detalhes para análise regulatória, pesquisa e acompanhamento técnico.</h3><ul><li>Registro, categoria, processo e vencimento em contexto.</li><li>Apresentações comercializadas e identificadores associados.</li><li>Parâmetros PF, PMC e PMVG por tributação.</li><li>Histórico detalhado de atualizações do Bulário.</li><li>Linha do tempo integrada e ocorrências de fiscalização.</li></ul><p className="profile-use-warning">Os dados apoiam análise e pesquisa, mas não substituem os sistemas e atos oficiais.</p></div></article>
        </div>
      </div>
    </section>

    <section className="container stats-section" aria-label="Indicadores da base">
      {error ? <ErrorState message={error}/> : !manifest ? <Loading/> : <>
        {manifest.sourceMode === 'empty' && <div className="callout warn">As informações ainda não estão disponíveis nesta publicação.</div>}
        <div className="stats-grid">
          <Metric icon={<Pill/>} label="Medicamentos" value={manifest.counts.products}/>
          <Metric icon={<FileText/>} label="Apresentações comercializadas" value={manifest.counts.presentations}/>
          <Metric icon={<Building2/>} label="Empresas" value={manifest.counts.companies}/>
          <Metric icon={<Tags/>} label="Princípios ativos" value={manifest.counts.ingredients}/>
        </div>
        <div className="data-version-line"><span>Dados processados em {humanDate(manifest.generatedAt)}</span></div>
      </>}
    </section>


    <section className="container accessibility-strip-section" aria-labelledby="accessibility-title">
      <div className="accessibility-strip">
        <span className="accessibility-strip-icon" aria-hidden="true"><Accessibility/></span>
        <div>
          <div className="eyebrow">Acessibilidade</div>
          <h2 id="accessibility-title">Conteúdo com suporte do VLibras.</h2>
          <p>O botão flutuante do VLibras permite traduzir automaticamente conteúdos em português para a Língua Brasileira de Sinais (Libras), ampliando o acesso de pessoas surdas às informações da plataforma.</p>
        </div>
        <a href="https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/vlibras" target="_blank" rel="noreferrer" className="accessibility-link">Conhecer o VLibras <ExternalLink size={15}/></a>
      </div>
    </section>

    <section className="section muted-section">
      <div className="container">
        <div className="section-heading"><span>Uma consulta mais completa</span><h2>Informações que fazem mais sentido quando estão juntas.</h2><p>O Medicamento Aberto organiza diferentes dimensões do medicamento em uma experiência única, clara e navegável.</p></div>
        <div className="feature-grid">
          <Feature icon={<Pill/>} title="Visão 360° do medicamento" text="Regularização, apresentações, Bulário, CMED e fiscalização reunidos em uma mesma página."/>
          <Feature icon={<ShieldCheck/>} title="Status regulatório em destaque" text="A situação do registro aparece de forma clara em buscas, cards e páginas de detalhe."/>
          <Feature icon={<BookOpenCheck/>} title="Histórico em contexto" text="Acompanhe a atualização atual e o histórico disponível no Bulário sem alternar entre diferentes consultas."/>
        </div>
      </div>
    </section>

    <section className="section">
      <div className="container split-panel">
        <div>
          <div className="eyebrow">Navegação orientada ao medicamento</div>
          <h2>Uma página para entender o medicamento por diferentes perspectivas.</h2>
          <p>Comece pelo medicamento e navegue por empresa, princípio ativo, apresentações, preço publicado na CMED, Bulário e fiscalização, mantendo o contexto regulatório durante toda a consulta.</p>
          <Link className="text-link" to="/sobre">Conhecer a plataforma <ArrowRight size={16}/></Link>
        </div>
        <div className="integrity-card">
          <ShieldCheck size={30}/><h3>Sem inferências sanitárias ou comerciais</h3>
          <p>A plataforma reproduz e relaciona dados abertos. Ela não converte ausência de resultado em declaração de regularidade e não apresenta dados econômicos da CMED como oferta, cotação ou recomendação comercial.</p>
        </div>
      </div>
    </section>

    <section className="section impact-section">
      <div className="container">
        <div className="section-heading"><span>Transparência em ação</span><h2>Não é apenas uma busca: é uma forma de acompanhar os dados abertos.</h2><p>Explore indicadores, acompanhe eventos recentes e reutilize os conjuntos consolidados em novas análises.</p></div>
        <div className="impact-links-grid">
          <Link to="/transparencia" className="impact-link-card"><BarChart3/><div><h3>Painel de transparência</h3><p>Situação dos registros, cobertura das fontes e indicadores consolidados.</p><strong>Explorar indicadores <ArrowRight size={15}/></strong></div></Link>
          <Link to="/atualizacoes" className="impact-link-card"><RefreshCw/><div><h3>Monitor de atualizações</h3><p>Atualizações recentes do Bulário e alertas de fiscalização.</p><strong>Ver atualizações <ArrowRight size={15}/></strong></div></Link>
          <Link to="/reutilize" className="impact-link-card"><FileText/><div><h3>Reutilize os dados</h3><p>Baixe conjuntos derivados e crie novas pesquisas, reportagens e aplicações.</p><strong>Acessar dados <ArrowRight size={15}/></strong></div></Link>
        </div>
      </div>
    </section>

    <section className="section open-data-strip">
      <div className="container open-data-inner"><div><div className="eyebrow">Transparência</div><h2>Saiba de onde vêm as informações.</h2><p>Conheça as dimensões integradas, os indicadores de cobertura e os links para as fontes de dados abertos oficiais.</p></div><Link className="primary-button" to="/sobre">Conhecer o Medicamento Aberto <ArrowRight size={16}/></Link></div>
    </section>
  </>
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return <div className="metric-card"><span className="metric-icon" aria-hidden="true">{icon}</span><strong>{formatNumber(value)}</strong><span>{label}</span></div>
}
function Feature({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return <article className="feature-card"><span className="feature-icon" aria-hidden="true">{icon}</span><h3>{title}</h3><p>{text}</p></article>
}
