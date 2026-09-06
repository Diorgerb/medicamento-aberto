import { Activity, BookOpenCheck, Building2, CheckCircle2, PackageOpen, Pill, Scale, ShieldAlert, ShieldCheck, Tags } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { ErrorState } from '../components/ErrorState'
import { Loading } from '../components/Loading'
import { getCatalog, getManifest, getQualityReport } from '../lib/data'
import { formatNumber } from '../lib/format'
import type { Manifest, ProductCatalogItem, QualityReport } from '../types/data'

export function TransparencyPage() {
  const [items, setItems] = useState<ProductCatalogItem[]>([])
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [quality, setQuality] = useState<QualityReport | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getCatalog(), getManifest(), getQualityReport()])
      .then(([catalog, dataManifest, report]) => { setItems(catalog); setManifest(dataManifest); setQuality(report) })
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false))
  }, [])

  const metrics = useMemo(() => {
    const total = items.length || 1
    const active = items.filter((item) => item.status.toLowerCase() === 'ativo').length
    const inactive = items.filter((item) => item.status.toLowerCase() === 'inativo').length
    const withPresentations = items.filter((item) => item.presentationCount > 0).length
    const withLeaflet = items.filter((item) => item.hasLeaflet || item.hasLeafletHistory).length
    const withCmed = items.filter((item) => item.hasCmed).length
    const withAlert = items.filter((item) => item.hasAlert).length
    const integrated3 = items.filter((item) => item.presentationCount > 0 && (item.hasLeaflet || item.hasLeafletHistory) && item.hasCmed).length
    const categories = new Map<string, number>()
    items.forEach((item) => { const key = item.regulatoryCategory || 'Não informada'; categories.set(key, (categories.get(key) || 0) + 1) })
    const topCategories = [...categories.entries()].sort((a,b) => b[1]-a[1]).slice(0, 8)
    return { total, active, inactive, withPresentations, withLeaflet, withCmed, withAlert, integrated3, topCategories }
  }, [items])

  if (loading) return <section className="page-section"><div className="container"><Loading/></div></section>
  if (error || !manifest) return <section className="page-section"><div className="container"><ErrorState message={error || 'Indicadores indisponíveis.'}/></div></section>

  return <section className="page-section transparency-page"><div className="container">
    <div className="page-heading"><div><div className="eyebrow">Transparência e controle social</div><h1>Panorama dos medicamentos</h1><p>Indicadores consolidados para compreender a cobertura, a situação dos registros e como diferentes dimensões públicas se conectam.</p></div></div>

    <div className="transparency-kpis">
      <Kpi icon={<Pill/>} label="Medicamentos" value={manifest.counts.products}/>
      <Kpi icon={<CheckCircle2/>} label="Registros ativos" value={metrics.active}/>
      <Kpi icon={<ShieldAlert/>} label="Registros inativos" value={metrics.inactive}/>
      <Kpi icon={<PackageOpen/>} label="Apresentações comercializadas" value={manifest.counts.presentations}/>
      <Kpi icon={<Building2/>} label="Empresas" value={manifest.counts.companies}/>
      <Kpi icon={<Tags/>} label="Princípios ativos" value={manifest.counts.ingredients}/>
    </div>

    <div className="dashboard-grid">
      <section className="dashboard-card wide">
        <div className="dashboard-card-heading"><div><span>Cobertura das informações</span><h2>Quanto da base está conectado a cada dimensão?</h2></div><Activity/></div>
        <div className="coverage-list">
          <Coverage label="Com apresentações comercializadas" value={metrics.withPresentations} total={metrics.total}/>
          <Coverage label="Com informação no Bulário" value={metrics.withLeaflet} total={metrics.total}/>
          <Coverage label="Com preço publicado na CMED" value={metrics.withCmed} total={metrics.total}/>
          <Coverage label="Com ocorrência de fiscalização" value={metrics.withAlert} total={metrics.total}/>
          <Coverage label="Com apresentações + Bulário + CMED" value={metrics.integrated3} total={metrics.total}/>
        </div>
      </section>

      <section className="dashboard-card">
        <div className="dashboard-card-heading"><div><span>Situação regulatória</span><h2>Ativos e inativos</h2></div><ShieldCheck/></div>
        <div className="status-composition">
          <div className="composition-bar" aria-label={`${metrics.active} ativos e ${metrics.inactive} inativos`}><span className="active" style={{width:`${metrics.active/metrics.total*100}%`}}/><span className="inactive" style={{width:`${metrics.inactive/metrics.total*100}%`}}/></div>
          <div className="composition-legend"><span><i className="dot active"/>Ativos <strong>{formatNumber(metrics.active)}</strong></span><span><i className="dot inactive"/>Inativos <strong>{formatNumber(metrics.inactive)}</strong></span></div>
        </div>
      </section>

      <section className="dashboard-card">
        <div className="dashboard-card-heading"><div><span>Categorias</span><h2>Principais categorias regulatórias</h2></div><Scale/></div>
        <div className="mini-bars">{metrics.topCategories.map(([label,value]) => <div className="mini-bar" key={label}><div><span>{label}</span><strong>{formatNumber(value)}</strong></div><span className="track"><i style={{width:`${value/(metrics.topCategories[0]?.[1]||1)*100}%`}}/></span></div>)}</div>
      </section>
    </div>

    <section className="public-value-panel">
      <div><div className="eyebrow">Controle social</div><h2>O que esses indicadores permitem acompanhar?</h2></div>
      <div className="public-value-grid">
        <Value icon={<ShieldCheck/>} title="Situação regulatória" text="Visualizar quantos medicamentos constam como ativos ou inativos na base pública e explorar os registros correspondentes."/>
        <Value icon={<BookOpenCheck/>} title="Cobertura documental" text="Entender em quais medicamentos foram localizadas informações do Bulário e acompanhar o histórico disponível."/>
        <Value icon={<Scale/>} title="Cobertura econômica" text="Identificar quais medicamentos possuem preço publicado na lista oficial da CMED, sem tratar esses valores como oferta comercial."/>
        <Value icon={<ShieldAlert/>} title="Fiscalização" text="Localizar e contextualizar ocorrências públicas de fiscalização vinculadas aos medicamentos quando houver correspondência segura."/>
      </div>
    </section>

    {quality?.metrics.presentationLinkRate !== undefined && <div className="quality-evidence"><strong>Qualidade da integração</strong><span>{quality.metrics.presentationLinkRate.toLocaleString('pt-BR')}% das apresentações de 13 dígitos foram vinculadas automaticamente aos medicamentos.</span></div>}
  </div></section>
}

function Kpi({icon,label,value}:{icon:React.ReactNode;label:string;value:number}) { return <article className="transparency-kpi"><span>{icon}</span><strong>{formatNumber(value)}</strong><small>{label}</small></article> }
function Coverage({label,value,total}:{label:string;value:number;total:number}) { const pct=total?value/total*100:0; return <div className="coverage-row"><div><span>{label}</span><strong>{formatNumber(value)} <small>({pct.toLocaleString('pt-BR',{maximumFractionDigits:1})}%)</small></strong></div><span className="coverage-track"><i style={{width:`${pct}%`}}/></span></div> }
function Value({icon,title,text}:{icon:React.ReactNode;title:string;text:string}) { return <article><span>{icon}</span><h3>{title}</h3><p>{text}</p></article> }
