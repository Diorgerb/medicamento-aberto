import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { Loading } from '../components/Loading'
import { ProductFiltersPanel } from '../components/ProductFiltersPanel'
import { RegistrationStatus } from '../components/RegistrationStatus'
import { SearchBox } from '../components/SearchBox'
import { StatusBadge } from '../components/StatusBadge'
import { useViewMode } from '../components/ViewModeContext'
import { getCatalog } from '../lib/data'
import { formatRegistration } from '../lib/format'
import { EMPTY_PRODUCT_FILTERS, productMatchesFilters, type ProductFilterValues } from '../lib/productFilters'
import type { ProductCatalogItem } from '../types/data'

const PAGE_SIZE = 30

export function MedicinesPage() {
  const { mode } = useViewMode()
  const [params] = useSearchParams()
  const query = params.get('q') ?? ''
  const [items, setItems] = useState<ProductCatalogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<ProductFilterValues>(EMPTY_PRODUCT_FILTERS)

  useEffect(() => {
    setLoading(true)
    getCatalog().then(setItems).catch((err) => setError(String(err))).finally(() => setLoading(false))
  }, [])

  useEffect(() => { setPage(1) }, [query, filters])

  const effectiveFilters = useMemo(() => ({ ...filters, query }), [filters, query])
  const filtered = useMemo(() => items.filter((item) => productMatchesFilters(item, effectiveFilters)), [items, effectiveFilters])
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const visible = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  return <section className="page-section"><div className="container">
    <div className="page-heading">
      <div><div className="eyebrow">Base integrada</div><h1>Medicamentos</h1><p>{mode === 'patient' ? 'Pesquise um medicamento e confira situação do registro, empresa, princípio ativo, apresentações, Bulário, CMED e fiscalização em linguagem mais simples.' : 'Explore medicamentos por nome, princípio ativo, empresa, categoria regulatória e situação do registro, com acesso aos detalhes técnicos integrados.'}</p></div>
      <span className="result-count" aria-live="polite">{filtered.length.toLocaleString('pt-BR')} resultados</span>
    </div>
    <SearchBox initial={query}/>

    <div className="catalog-layout">
      <ProductFiltersPanel products={items} values={filters} onChange={setFilters} showSearch={false}/>
      <div>
        {loading ? <Loading/> : error ? <ErrorState message={error}/> : visible.length === 0 ? <EmptyState title="Nenhum resultado" text="Tente remover filtros ou usar outros termos de busca."/> : <div className="result-list">{visible.map((item) => <Link className="medicine-row" to={`/medicamentos/${item.id}?bucket=${item.bucket}`} key={item.id}>
          <div className="medicine-main"><div className="medicine-name">{item.name}</div><div className="medicine-sub">{item.activeIngredients.join(' · ') || 'Princípio ativo não informado'}</div><div className="medicine-company">{item.companyName || 'Empresa não informada'}</div></div>
          <div className="medicine-meta"><span>{formatRegistration(item.registrationNumber)}</span><span>{item.regulatoryCategory || 'Categoria regulatória não informada'}</span><span>{item.presentationCount} apresentação(ões) comercializada(s)</span></div>
          <div className="row-badges"><RegistrationStatus status={item.status} compact/>{item.hasLeaflet && <StatusBadge label={mode === 'patient' ? 'Bulário' : 'Bula'} tone="good"/>}{item.hasCmed && <StatusBadge label={mode === 'patient' ? 'Preço na CMED' : 'Preço publicado na CMED'} tone="info"/>}{item.hasAlert && <StatusBadge label="Ocorrência" tone="warn"/>}</div>
        </Link>)}</div>}
        {!loading && !error && filtered.length > PAGE_SIZE && <nav className="pagination" aria-label="Paginação"><button disabled={currentPage <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}><ChevronLeft size={16}/> Anterior</button><span>Página {currentPage} de {totalPages}</span><button disabled={currentPage >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>Próxima <ChevronRight size={16}/></button></nav>}
      </div>
    </div>
  </div></section>
}
