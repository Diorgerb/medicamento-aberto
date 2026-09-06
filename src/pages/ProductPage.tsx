import { BookOpenCheck, Building2, CalendarClock, Clock3, ExternalLink, FileClock, FileText, HeartPulse, History, LayoutDashboard, PackageOpen, Pill, ReceiptText, ShieldAlert, ShieldCheck, Stethoscope, TableProperties, Tag } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { Loading } from '../components/Loading'
import { RegistrationStatus, registrationState } from '../components/RegistrationStatus'
import { StatusBadge } from '../components/StatusBadge'
import { ViewModeSelector } from '../components/ViewModeSelector'
import { useViewMode } from '../components/ViewModeContext'
import { getManifest, getProduct } from '../lib/data'
import { anvisaLeafletUrl, anvisaMedicineProcessUrl, anvisaMedicineRegistrationUrl } from '../lib/anvisa'
import {
  formatCnpj,
  formatDateDMY,
  formatExpedient,
  formatMonthYear,
  formatPrice,
  formatRegistration,
  formatSourceField,
  valueOrDash,
} from '../lib/format'
import type { CmedRow, CommercialPresentation, Manifest, ProductDetail, RelatedRecord } from '../types/data'

type Tab = 'overview' | 'timeline' | 'presentations' | 'cmed' | 'leaflets' | 'alerts'

export function ProductPage() {
  const { id = '' } = useParams()
  const [params] = useSearchParams()
  const bucket = params.get('bucket') ?? undefined
  const [item, setItem] = useState<ProductDetail | null>(null)
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<Tab>('overview')
  const { mode } = useViewMode()

  useEffect(() => {
    setLoading(true)
    setError('')
    Promise.all([getProduct(id, bucket), getManifest()])
      .then(([product, dataManifest]) => { setItem(product); setManifest(dataManifest) })
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false))
  }, [id, bucket])

  if (loading) return <PageFrame><Loading/></PageFrame>
  if (error) return <PageFrame><ErrorState message={error}/></PageFrame>
  if (!item || !manifest) return <PageFrame><EmptyState title="Medicamento não encontrado"/></PageFrame>

  return <section className="page-section product-page"><div className="container">
    <div className="breadcrumb"><Link to="/medicamentos">Medicamentos</Link><span>/</span><span>{item.name}</span></div>
    <div className="product-hero-card">
      <div className="product-icon"><Pill size={28}/></div>
      <div className="product-heading-content">
        <div className="eyebrow">Medicamento</div>
        <h1>{item.name}</h1>
        <p>{item.activeIngredients.join(' · ') || 'Princípio ativo não informado'}</p>
        <div className="badge-row">
          <RegistrationStatus status={item.status} compact/>
          {item.regulatoryCategory && <StatusBadge label={item.regulatoryCategory} tone="info"/>}
          {item.leafletLatest.length > 0 && <StatusBadge label="Bulário atualizado" tone="good"/>}
          {item.sourceLayers.cmed && <StatusBadge label="Preço publicado na CMED" tone="info"/>}
          {item.sourceLayers.inspection && <StatusBadge label={`${item.alerts.length} ocorrência(s)`} tone="warn"/>}
        </div>
      </div>
      <div className="product-key-data">
        <small>Registro</small><OfficialValueLink href={anvisaMedicineRegistrationUrl(item.registrationNumber)} value={formatRegistration(item.registrationNumber)} label="Consultar registro na Anvisa"/>
        <small>Processo</small><OfficialValueLink href={anvisaMedicineProcessUrl(item.processNumber)} value={valueOrDash(item.processNumber)} label="Consultar processo na Anvisa"/>
      </div>
    </div>

    <div className={`profile-context-card ${mode}`}>
      <div className="profile-context-copy">{mode === 'patient' ? <><HeartPulse/><div><strong>Visualização para paciente / cidadão</strong><span>Linguagem mais simples e foco em situação do registro, apresentações, bula e informações essenciais. Não substitui orientação de profissional de saúde.</span></div></> : <><Stethoscope/><div><strong>Visualização profissional</strong><span>Exibe maior densidade técnica, processo, parâmetros da CMED e histórico detalhado para análise regulatória, pesquisa e saúde.</span></div></>}</div>
      <ViewModeSelector/>
    </div>

    <div className="product-navigation-shell">
      <div className="registration-context" aria-label="Situação do registro">
        <RegistrationStatus status={item.status}/>
        <span className="registration-context-note">Situação atual do registro do medicamento</span>
      </div>
      <nav className="tabs product-tabs" aria-label="Seções do medicamento">
        <TabButton active={tab==='overview'} onClick={()=>setTab('overview')} label="Geral" icon={<LayoutDashboard size={17}/>} />
        <TabButton active={tab==='timeline'} onClick={()=>setTab('timeline')} label="Linha do tempo" icon={<History size={17}/>} />
        <TabButton active={tab==='presentations'} onClick={()=>setTab('presentations')} label="Apresentações" count={item.presentations.length} icon={<PackageOpen size={17}/>} />
        <TabButton active={tab==='cmed'} onClick={()=>setTab('cmed')} label="CMED" count={item.cmed.length} icon={<TableProperties size={17}/>} />
        <TabButton active={tab==='leaflets'} onClick={()=>setTab('leaflets')} label="Bulário" count={item.leafletHistory.length} icon={<BookOpenCheck size={17}/>} />
        <TabButton active={tab==='alerts'} onClick={()=>setTab('alerts')} label="Fiscalização" count={item.alerts.length} icon={<ShieldAlert size={17}/>} />
      </nav>
    </div>

    {tab==='overview' && <Overview item={item} mode={mode}/>} 
    {tab==='timeline' && <IntegratedTimeline item={item} manifest={manifest}/>}
    {tab==='presentations' && <Presentations rows={item.presentations} mode={mode}/>} 
    {tab==='cmed' && <CmedData rows={item.cmed} bands={manifest.cmedTaxBands} mode={mode}/>} 
    {tab==='leaflets' && <LeafletSection item={item} manifest={manifest} mode={mode}/>} 
    {tab==='alerts' && <InspectionSection rows={item.alerts} manifest={manifest}/>} 
  </div></section>
}

function PageFrame({ children }: { children: React.ReactNode }) { return <section className="page-section"><div className="container">{children}</div></section> }
function TabButton({ active, onClick, label, count, icon }: { active:boolean; onClick:()=>void; label:string; count?:number; icon:React.ReactNode }) { return <button type="button" className={active?'active':''} aria-current={active?'page':undefined} onClick={onClick}><span className="tab-icon">{icon}</span><span className="tab-copy"><strong>{label}</strong>{count !== undefined && <small>{count.toLocaleString('pt-BR')}</small>}</span></button> }

function Overview({ item, mode }: { item: ProductDetail; mode: 'patient' | 'professional' }) {
  const state = registrationState(item.status)
  const currentLeaflet = item.leafletLatest.length > 0
  const registrationUrl = anvisaMedicineRegistrationUrl(item.registrationNumber)
  const processUrl = anvisaMedicineProcessUrl(item.processNumber)
  return <>
    <section className="overview-summary" aria-labelledby="overview-summary-title">
      <div className="overview-summary-heading">
        <div><div className="eyebrow">Visão geral</div><h2 id="overview-summary-title">{mode === 'patient' ? 'O que é importante saber nesta consulta' : 'O essencial sobre este medicamento'}</h2><p>{mode === 'patient' ? 'Veja primeiro a situação do registro, a empresa responsável, as apresentações localizadas e quando houve atualização no Bulário.' : 'Os principais indicadores regulatórios e informações relacionadas reunidos em uma única visão.'}</p></div>
        <RegistrationStatus status={item.status}/>
      </div>
      <div className="overview-indicators">
        <OverviewIndicator className={`registration ${state}`} icon={<ShieldCheck/>} label="Situação do registro" value={item.status || 'Não informado'} detail="Status regulatório do medicamento"/>
        <OverviewIndicator icon={<Pill/>} label="Registro" value={formatRegistration(item.registrationNumber)} detail={item.validProductRegistration ? 'Número de registro sanitário' : 'Registro sanitário não informado na base'} />
        <OverviewIndicator icon={<CalendarClock/>} label="Vencimento" value={formatMonthYear(item.registrationExpiry)} detail="Vencimento do registro"/>
        <OverviewIndicator icon={<PackageOpen/>} label="Apresentações comercializadas" value={item.presentations.length.toLocaleString('pt-BR')} detail={item.presentations.length ? 'Apresentações localizadas para o medicamento' : 'Nenhuma apresentação localizada'} />
        <OverviewIndicator icon={<TableProperties/>} label="Preço publicado na CMED" value={item.sourceLayers.cmed ? 'Sim' : 'Não'} detail={item.sourceLayers.cmed ? 'Há informação econômica publicada' : 'Não localizado na lista de preços'} />
        <OverviewIndicator icon={<BookOpenCheck/>} label="Bulário Eletrônico" value={currentLeaflet ? 'Atualização localizada' : 'Sem atualização atual'} detail={item.leafletHistory.length ? `${item.leafletHistory.length.toLocaleString('pt-BR')} atualização(ões) no histórico` : 'Sem histórico relacionado'} />
        <OverviewIndicator className={item.alerts.length ? 'warning' : ''} icon={<ShieldAlert/>} label="Fiscalização" value={item.alerts.length.toLocaleString('pt-BR')} detail={item.alerts.length ? 'Ocorrência(s) pública(s) relacionada(s)' : 'Nenhuma ocorrência localizada'} />
      </div>
    </section>

    <div className="layer-grid" aria-label="Informações disponíveis">
      <LayerCard active title="Situação regulatória" text="Categoria e situação do registro"/>
      <LayerCard active={item.sourceLayers.presentations} title="Apresentações" text={item.sourceLayers.presentations?`${item.presentations.length} apresentação(ões) comercializada(s)`:'Nenhuma apresentação localizada'}/>
      <LayerCard active={currentLeaflet} title="Bulário" text={currentLeaflet?`Última atualização localizada${item.leafletHistory.length ? ` · ${item.leafletHistory.length} no histórico` : ''}`:'Sem atualização atual localizada'}/>
      <LayerCard active={item.sourceLayers.cmed} title="CMED" text={item.sourceLayers.cmed?'Possui preço publicado na CMED':'Sem preço publicado localizado'}/>
      <LayerCard active={item.sourceLayers.inspection} title="Fiscalização" text={item.sourceLayers.inspection?`${item.alerts.length} ocorrência(s) localizada(s)`:'Nenhuma ocorrência localizada'}/>
    </div>
    <div className="detail-grid">
      <InfoCard icon={<ShieldCheck/>} title="Informações regulatórias">
        <div className="info-status-row"><span>Situação do registro</span><RegistrationStatus status={item.status} compact/></div>
        <Info label="Categoria regulatória" value={item.regulatoryCategory}/>
        <Info label="Registro" value={formatRegistration(item.registrationNumber)} href={registrationUrl} externalLabel="Consultar registro na Anvisa"/>
        <Info label="Vencimento do registro" value={formatMonthYear(item.registrationExpiry)}/>
      </InfoCard>
      <InfoCard icon={<Building2/>} title="Empresa">
        <Info label="Razão social" value={item.companyName}/>
        <Info label="CNPJ" value={formatCnpj(item.companyCnpj)}/>
        {item.companyId && <Link className="text-link" to={`/empresas/${item.companyId}`}>Ver medicamentos da empresa</Link>}
      </InfoCard>
      <InfoCard icon={<Tag/>} title="Classificação">
        <Info label="Princípio ativo" value={item.activeIngredients.join(' · ')}/>
        <Info label="Classe terapêutica" value={item.therapeuticClass}/>
      </InfoCard>
      {mode === 'professional' && <InfoCard icon={<FileText/>} title="Processo">
        <Info label="Número do processo" value={item.processNumber} href={processUrl} externalLabel="Consultar processo na Anvisa"/>
        <Info label="Data de finalização" value={formatDateDMY(item.processFinalizationDate)}/>
      </InfoCard>}
    </div>
    {mode === 'patient' && <div className="patient-guidance"><HeartPulse/><div><strong>Como usar esta informação</strong><p>Esta página ajuda a conferir informações públicas sobre o medicamento. Para dúvidas sobre indicação, dose, troca de medicamento, reações adversas ou tratamento, consulte a bula e um profissional de saúde.</p></div></div>}
  </>
}

function OverviewIndicator({ icon, label, value, detail, className = '' }: { icon:React.ReactNode; label:string; value:string; detail:string; className?:string }) {
  return <article className={`overview-indicator ${className}`}><span className="overview-indicator-icon">{icon}</span><div><small>{label}</small><strong>{value}</strong><p>{detail}</p></div></article>
}
function LayerCard({active,title,text}:{active:boolean;title:string;text:string}) { return <div className={`layer-card ${active?'active':''}`}><span className="layer-dot"/><div><strong>{title}</strong><small>{text}</small></div></div> }

function Presentations({ rows, mode }: { rows: CommercialPresentation[]; mode: 'patient' | 'professional' }) {
  if (!rows.length) return <EmptyState text="Nenhuma apresentação comercializada foi localizada para este medicamento."/>
  return <>
    <SectionIntro eyebrow="Apresentações comercializadas" title={`${rows.length.toLocaleString('pt-BR')} apresentação(ões) localizada(s)`} text="Consulte as formas de apresentação e as principais características comerciais publicadas para o medicamento."/>
    <div className="presentation-list">{rows.map((row)=><article className="presentation-card" key={row.registrationNumber}>
      <div className="presentation-title"><ReceiptText size={18}/><strong>{row.description || 'Apresentação sem descrição'}</strong></div>
      <div className="presentation-grid presentation-grid-clean">
        {mode === 'professional' && <Info label="Código da apresentação" value={row.registrationNumber}/>}
        <Info label="EAN" value={row.eans.join(' · ')}/>
        <Info label="Laboratório" value={row.laboratory}/>
        <Info label="Substância" value={row.substance}/>
        {mode === 'professional' && <><Info label="Classe terapêutica" value={row.therapeuticClass}/><Info label="Categoria na CMED" value={row.productType}/></>}
        <Info label="Restrição hospitalar" value={row.hospitalRestriction}/>
        <Info label="Tarja" value={row.stripe}/>
        {mode === 'professional' && <Info label="Destinação comercial" value={row.commercialDestination}/>}
      </div>
    </article>)}</div>
  </>
}

function CmedData({ rows, bands, mode }: { rows: CmedRow[]; bands: string[]; mode: 'patient' | 'professional' }) {
  if (!rows.length) return <EmptyState text="Não foi localizado preço publicado na CMED para este medicamento."/>
  return <>
    <SectionIntro eyebrow="Informações econômicas" title="Preço publicado na CMED" text={mode === 'patient' ? 'Este medicamento foi localizado na lista oficial da CMED. Os valores são tetos regulatórios e não significam que esse seja o preço cobrado em uma farmácia.' : 'Consulte os parâmetros oficiais publicados para as apresentações deste medicamento. Os valores não representam oferta, promoção, cotação ou preço efetivamente praticado.'}/>
    <div className="cmed-list">{rows.map((row)=><article className="cmed-card" key={row.ggremCode}>
      <div className="cmed-card-head"><div><div className="eyebrow">Apresentação</div><h2>{row.presentation || row.product || 'Informação CMED'}</h2><p>{row.laboratory}{row.eans.length ? ` · EAN ${row.eans.join(' · ')}` : ''}</p></div><div className="badge-row">{row.priceRegime&&<StatusBadge label={row.priceRegime} tone="info"/>}{row.cap&&<StatusBadge label={`CAP: ${row.cap}`} tone="neutral"/>}</div></div>
      <div className="cmed-meta-grid"><Info label="Substância" value={row.substance}/>{mode === 'professional' && <><Info label="Classe terapêutica" value={row.therapeuticClass}/><Info label="PIS/Cofins" value={row.taxCreditList}/><Info label="Destinação comercial" value={row.commercialDestination}/></>}</div>
      <details className="cmed-tax-details" open={mode === 'professional'}>
        <summary>Ver parâmetros por tributação</summary>
        <div className="tax-band-grid">{bands.map((band,index)=><article className="tax-band-card" key={band}>
          <strong>{band}</strong>
          <div className="price-values"><PriceValue label="PF" value={row.factoryPrices[index]}/><PriceValue label="PMC" value={row.consumerPrices[index]}/><PriceValue label="PMVG" value={row.governmentPrices[index]}/></div>
        </article>)}</div>
      </details>
      <p className="cmed-source-note"><strong>PF</strong> = Preço Fábrica · <strong>PMC</strong> = Preço Máximo ao Consumidor · <strong>PMVG</strong> = Preço Máximo de Venda ao Governo.</p>
    </article>)}</div>
  </>
}

function PriceValue({label,value}:{label:string;value:string}) { return <div><small>{label}</small><strong>{formatPrice(value)}</strong></div> }

function recordAsObject(record: RelatedRecord, columns: string[]) {
  return Object.fromEntries(columns.map((column, index) => [column, record.values[index] ?? '']))
}
function mdyTimestamp(value: string) {
  const match = value.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}):(\d{2}))?$/)
  if (!match) return 0
  return Date.UTC(Number(match[3]), Number(match[1]) - 1, Number(match[2]), Number(match[4] || 0), Number(match[5] || 0), Number(match[6] || 0))
}

function LeafletSection({ item, manifest, mode }: { item: ProductDetail; manifest: Manifest; mode: 'patient' | 'professional' }) {
  const latest = item.leafletLatest
  const history = useMemo(() => [...item.leafletHistory].sort((a, b) => {
    const ao = recordAsObject(a, manifest.schemas.bula_documento)
    const bo = recordAsObject(b, manifest.schemas.bula_documento)
    return mdyTimestamp(bo.DATA_ATUALIZACAO_BULARIO || '') - mdyTimestamp(ao.DATA_ATUALIZACAO_BULARIO || '')
  }), [item.leafletHistory, manifest.schemas.bula_documento])

  const officialLeafletUrl = anvisaLeafletUrl(item.registrationNumber)

  return <div className="leaflet-section">
    <SectionIntro eyebrow="Bulário Eletrônico" title="Atualizações da bula" text="Acompanhe a atualização mais recente e o histórico disponível para este medicamento."/>
    {officialLeafletUrl && <div className="official-source-actions"><a href={officialLeafletUrl} target="_blank" rel="noreferrer" className="official-source-button"><BookOpenCheck size={17}/><span><strong>Consultar no Bulário da Anvisa</strong><small>Abrir a consulta oficial pelo número de registro</small></span><ExternalLink size={15}/></a></div>}
    {!latest.length && !history.length && <EmptyState text="Nenhuma atualização do Bulário Eletrônico foi localizada nesta base integrada. Você ainda pode consultar o Bulário oficial da Anvisa pelo botão acima."/>}
    {(latest.length > 0 || history.length > 0) && <>
    <section className="leaflet-current-block">
      <div className="section-heading compact"><div><div className="eyebrow">Mais recente</div><h2>Última atualização</h2></div><Clock3 size={22}/></div>
      {!latest.length ? <EmptyState text="Não foi localizada uma atualização atual para este medicamento."/> : latest.map((record, index) => {
        const obj = recordAsObject(record, manifest.schemas.bula_produto)
        return <article className="related-card featured-update" key={`latest-${record.matchValue}-${index}`}>
          <header><div><div className="eyebrow">Bulário Eletrônico</div><strong>{valueOrDash(obj.NOME_PRODUTO_BULARIO)}</strong></div><StatusBadge label="Última atualização" tone="good"/></header>
          <div className="presentation-grid presentation-grid-clean">
            <Info label="Data da atualização" value={formatSourceField('bula_produto', 'DATA_ULTIMA_ATUALIZACAO_BULARIO', obj.DATA_ULTIMA_ATUALIZACAO_BULARIO)}/>
            <Info label="Expediente" value={formatExpedient(obj.NUMERO_EXPEDIENTE_ATUAL)}/>
            <Info label="Processo" value={obj.NUMERO_PROCESSO} href={anvisaMedicineProcessUrl(obj.NUMERO_PROCESSO)} externalLabel="Consultar processo na Anvisa"/>
            <Info label="Empresa" value={obj.RAZAO_SOCIAL_EMPRESA}/>
          </div>
        </article>
      })}
    </section>

    <section className="leaflet-history-block">
      <div className="section-heading compact"><div><div className="eyebrow">Histórico</div><h2>{mode === 'patient' ? 'Histórico disponível' : 'Todas as atualizações'}</h2><p>{history.length.toLocaleString('pt-BR')} atualização(ões) localizada(s).</p></div><FileClock size={22}/></div>
      {mode === 'patient' && history.length > 0 && <p className="simple-explainer">O histórico mostra quando registros relacionados à bula foram atualizados no Bulário. Para detalhes de expediente e situação documental, altere para a visualização Profissional.</p>}
      {!history.length ? <EmptyState text="Nenhuma atualização anterior foi localizada."/> : <div className="timeline-list">{(mode === 'patient' ? history.slice(0, 8) : history).map((record, index) => {
        const obj = recordAsObject(record, manifest.schemas.bula_documento)
        return <article className="timeline-card" key={`history-${obj.ID_DOCUMENTO || index}`}>
          <span className="timeline-dot"/>
          <div className="timeline-date">{formatSourceField('bula_documento', 'DATA_ATUALIZACAO_BULARIO', obj.DATA_ATUALIZACAO_BULARIO)}</div>
          <div className="timeline-content"><strong>{mode === 'patient' ? 'Atualização registrada' : formatExpedient(obj.NUMERO_EXPEDIENTE)}</strong>{mode === 'professional' && <span>{valueOrDash(obj.SITUACAO_DOCUMENTO)}</span>}</div>
        </article>
      })}</div>}
    </section>
    </>}
  </div>
}

function IntegratedTimeline({ item, manifest }: { item: ProductDetail; manifest: Manifest }) {
  const events = useMemo(() => {
    const rows: { date:number; label:string; title:string; text:string; tone:string }[] = []
    const dmy = (value:string) => { const m=value.match(/^(\d{2})\/(\d{2})\/(\d{4})/); return m?Date.UTC(+m[3],+m[2]-1,+m[1]):0 }
    if (item.processFinalizationDate) rows.push({date:dmy(item.processFinalizationDate),label:formatDateDMY(item.processFinalizationDate),title:'Finalização do processo',text:'Data de finalização informada na base de medicamentos.',tone:'registration'})
    item.leafletHistory.forEach((record) => { const obj=recordAsObject(record,manifest.schemas.bula_documento); const raw=obj.DATA_ATUALIZACAO_BULARIO||''; const ts=mdyTimestamp(raw); if(ts) rows.push({date:ts,label:formatSourceField('bula_documento','DATA_ATUALIZACAO_BULARIO',raw),title:'Atualização no Bulário',text:valueOrDash(obj.SITUACAO_DOCUMENTO),tone:'leaflet'}) })
    item.alerts.forEach((record) => { const obj=recordAsObject(record,manifest.schemas.irregulares); const raw=obj.DT_PUBLICACAO_MEDIDA||obj.DT_PUBLICACAO||''; const ts=mdyTimestamp(raw); if(ts) rows.push({date:ts,label:formatSourceField('irregulares','DT_PUBLICACAO_MEDIDA',raw),title:'Publicação de fiscalização',text:valueOrDash(obj.ACAO_ATIVIDADE||obj.DS_ACAO_FISCALIZACAO),tone:'inspection'}) })
    return rows.filter((row)=>row.date>0).sort((a,b)=>b.date-a.date)
  }, [item, manifest])
  return <>
    <SectionIntro eyebrow="Histórico público" title="Linha do tempo integrada" text="Eventos datados de diferentes dimensões públicas organizados em uma única sequência. A linha do tempo não cria eventos: ela apenas reúne datas presentes nas fontes integradas."/>
    {events.length===0?<EmptyState text="Nenhum evento datado foi localizado para montar a linha do tempo."/>:<div className="integrated-timeline">{events.map((event,index)=><article className={`integrated-timeline-item ${event.tone}`} key={`${event.date}-${index}`}><time>{event.label}</time><span className="timeline-node"/><div><strong>{event.title}</strong><p>{event.text}</p></div></article>)}</div>}
  </>
}

function InspectionSection({rows, manifest}:{rows:RelatedRecord[];manifest:Manifest}) {
  if (!rows.length) return <EmptyState text="Nenhuma ocorrência pública de fiscalização foi localizada para este medicamento."/>
  return <>
    <SectionIntro eyebrow="Fiscalização" title={`${rows.length.toLocaleString('pt-BR')} ocorrência(s) localizada(s)`} text="Consulte as informações públicas de fiscalização relacionadas ao medicamento. A ausência de ocorrência não constitui certificação de regularidade."/>
    <div className="inspection-list">{rows.map((record,index)=>{
      const obj = recordAsObject(record, manifest.schemas.irregulares)
      const publication = obj.DT_PUBLICACAO_MEDIDA || obj.DT_PUBLICACAO
      const action = obj.ACAO_ATIVIDADE || obj.DS_ACAO_FISCALIZACAO || obj.DS_ATIVIDADE_FISCALIZACAO
      return <article className="inspection-card" key={`${record.matchValue}-${index}`}>
        <header><div><div className="eyebrow">{formatSourceField('irregulares','DT_PUBLICACAO_MEDIDA',publication)}</div><h2>{valueOrDash(obj.PRODUTO || obj.PRODUTOS_CONCATENADOS)}</h2></div><StatusBadge label="Ocorrência de fiscalização" tone="warn"/></header>
        {action && <p className="inspection-action">{action}</p>}
        <div className="presentation-grid presentation-grid-clean">
          <Info label="Empresa" value={obj.NO_EMPRESA_INVESTIGADA || obj.NO_RAZAO_SOCIAL}/>
          <Info label="CNPJ" value={formatCnpj(obj.NU_CNPJ_EMPRESA_INVESTIGADA || obj.NU_CNPJ)}/>
          <Info label="Processo" value={obj.NU_PROCESSO}/>
          <Info label="Risco informado" value={obj.DS_RISCO_PRODUTO}/>
        </div>
      </article>
    })}</div>
  </>
}

function SectionIntro({eyebrow,title,text}:{eyebrow:string;title:string;text:string}) { return <div className="section-intro"><div className="eyebrow">{eyebrow}</div><h2>{title}</h2><p>{text}</p></div> }
function InfoCard({icon,title,children}:{icon:React.ReactNode;title:string;children:React.ReactNode}) { return <article className="info-card"><div className="info-card-title">{icon}<h2>{title}</h2></div>{children}</article> }
function OfficialValueLink({href,value,label}:{href:string|null;value:string;label:string}) {
  if (!href || value === '—') return <strong>{value}</strong>
  return <a className="official-query-link" href={href} target="_blank" rel="noreferrer" aria-label={label} title={label}><span>{value}</span><ExternalLink size={12}/></a>
}
function Info({label,value,href,externalLabel}:{label:string;value:unknown;href?:string|null;externalLabel?:string}) {
  const display = valueOrDash(value)
  return <div className="info-row"><span>{label}</span>{href && display !== '—' ? <OfficialValueLink href={href} value={display} label={externalLabel || `Consultar ${label} na Anvisa`}/> : <strong>{display}</strong>}</div>
}
