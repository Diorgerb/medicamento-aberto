import { BellRing, BookOpenCheck, ShieldAlert, SlidersHorizontal } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { Loading } from '../components/Loading'
import { RegistrationStatus } from '../components/RegistrationStatus'
import { getActivityFeed } from '../lib/data'
import { formatRegistration, humanDate } from '../lib/format'
import type { ActivityEvent, ActivityFeed, ActivityType } from '../types/data'

type PublicUpdateType = Extract<ActivityType, 'leaflet' | 'inspection'>

const labels: Record<PublicUpdateType, string> = {
  leaflet: 'Bulário',
  inspection: 'Alerta',
}

export function UpdatesPage() {
  const [feed,setFeed]=useState<ActivityFeed|null>(null)
  const [error,setError]=useState('')
  const [loading,setLoading]=useState(true)
  const [type,setType]=useState<PublicUpdateType|''>('')

  useEffect(()=>{
    getActivityFeed()
      .then(setFeed)
      .catch((err)=>setError(String(err)))
      .finally(()=>setLoading(false))
  },[])

  const events=useMemo(()=>{
    const publicEvents=(feed?.recentEvents??[]).filter((event): event is ActivityEvent & {type: PublicUpdateType} => event.type==='leaflet'||event.type==='inspection')
    return type ? publicEvents.filter((event)=>event.type===type) : publicEvents
  },[feed,type])

  const leafletCount=useMemo(()=>events.filter((event)=>event.type==='leaflet').length,[events])
  const alertCount=useMemo(()=>events.filter((event)=>event.type==='inspection').length,[events])

  if(loading)return <section className="page-section"><div className="container"><Loading/></div></section>
  if(error||!feed)return <section className="page-section"><div className="container"><ErrorState message={error||'Atualizações indisponíveis.'}/></div></section>

  return <section className="page-section updates-page"><div className="container">
    <div className="page-heading"><div><div className="eyebrow">Bulário e alertas</div><h1>Atualizações</h1><p>Esta área reúne exclusivamente atualizações identificadas no Bulário Eletrônico e alertas ou ocorrências de fiscalização relacionados aos medicamentos.</p></div></div>

    <section className="updates-scope-card" aria-label="Escopo da página de atualizações">
      <div><span className="updates-scope-icon leaflet"><BookOpenCheck size={20}/></span><span><strong>Atualizações do Bulário</strong><small>Novas atualizações e documentos identificados no histórico integrado do medicamento.</small></span></div>
      <div><span className="updates-scope-icon inspection"><ShieldAlert size={20}/></span><span><strong>Alertas de fiscalização</strong><small>Publicações e ocorrências de fiscalização sanitária localizadas nas dados abertos integrados.</small></span></div>
    </section>

    <div className="public-disclaimer compact-disclaimer"><BellRing/><div><strong>O que não aparece aqui</strong><p>Alterações de situação do registro, presença na CMED ou quantidade de apresentações não são tratadas como “Atualizações” nesta página. Esses dados permanecem disponíveis nas áreas específicas da plataforma.</p></div></div>

    <div className="updates-toolbar"><span><SlidersHorizontal size={16}/> Filtrar</span><select value={type} onChange={(event)=>setType(event.target.value as PublicUpdateType|'')}><option value="">Bulário e alertas</option><option value="leaflet">Somente Bulário</option><option value="inspection">Somente alertas</option></select><span className="updates-count">{events.length.toLocaleString('pt-BR')} eventos</span></div>

    <div className="updates-summary" aria-label="Resumo das atualizações filtradas"><div><BookOpenCheck size={17}/><span><strong>{leafletCount.toLocaleString('pt-BR')}</strong><small>Bulário</small></span></div><div><ShieldAlert size={17}/><span><strong>{alertCount.toLocaleString('pt-BR')}</strong><small>Alertas</small></span></div></div>

    {events.length===0?<EmptyState title="Nenhuma atualização localizada" text="Não há eventos do Bulário ou alertas de fiscalização para o filtro selecionado."/>:<div className="updates-timeline">{events.slice(0,250).map((event)=><UpdateCard event={event as ActivityEvent & {type: PublicUpdateType}} key={event.id}/>)}</div>}
  </div></section>
}

function UpdateCard({event}:{event:ActivityEvent & {type: PublicUpdateType}; key?: string}) {
  const Icon=event.type==='leaflet'?BookOpenCheck:ShieldAlert
  return <Link to={`/medicamentos/${event.productId}?bucket=${event.bucket}`} className="update-card"><span className={`update-icon ${event.type}`}><Icon size={19}/></span><div className="update-content"><div className="update-meta"><span>{labels[event.type]}</span><time>{humanDate(event.date)}</time></div><h3>{event.productName}</h3><strong>{event.title}</strong><p>{event.description}</p><div className="update-foot"><span>{formatRegistration(event.registrationNumber)}</span><RegistrationStatus status={event.status} compact/></div></div></Link>
}
