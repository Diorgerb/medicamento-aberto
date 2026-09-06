import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from './EmptyState'
import { ProductFiltersPanel } from './ProductFiltersPanel'
import { RegistrationStatus } from './RegistrationStatus'
import { StatusBadge } from './StatusBadge'
import { formatRegistration } from '../lib/format'
import { EMPTY_PRODUCT_FILTERS, productMatchesFilters, type ProductFilterValues } from '../lib/productFilters'
import type { ProductCatalogItem } from '../types/data'

const PAGE_SIZE = 24

export function RelatedProductsExplorer({
  products,
  searchPlaceholder = 'Nome, registro, processo ou empresa',
  emptyText = 'Nenhum medicamento corresponde aos filtros selecionados.',
}: {
  products: ProductCatalogItem[]
  searchPlaceholder?: string
  emptyText?: string
}) {
  const [filters, setFilters] = useState<ProductFilterValues>(EMPTY_PRODUCT_FILTERS)
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => products.filter((product) => productMatchesFilters(product, filters)), [products, filters])
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const visible = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  useEffect(() => { setPage(1) }, [filters])

  return <div className="related-products-explorer">
    <div className="related-products-toolbar">
      <div>
        <div className="eyebrow">Medicamentos relacionados</div>
        <h2 className="section-title">Explore os medicamentos desta entidade</h2>
      </div>
      <span className="result-count" aria-live="polite">{filtered.length.toLocaleString('pt-BR')} de {products.length.toLocaleString('pt-BR')}</span>
    </div>

    <div className="catalog-layout related-catalog-layout">
      <ProductFiltersPanel products={products} values={filters} onChange={setFilters} searchPlaceholder={searchPlaceholder}/>
      <div>
        {visible.length === 0
          ? <EmptyState title="Nenhum resultado" text={emptyText}/>
          : <div className="result-list">{visible.map((item) => <Link className="medicine-row" to={`/medicamentos/${item.id}?bucket=${item.bucket}`} key={item.id}>
            <div className="medicine-main">
              <div className="medicine-name">{item.name}</div>
              <div className="medicine-sub">{item.activeIngredients.join(' · ') || 'Princípio ativo não informado'}</div>
              <div className="medicine-company">{item.companyName || 'Empresa não informada'}</div>
            </div>
            <div className="medicine-meta">
              <span>{formatRegistration(item.registrationNumber)}</span>
              <span>{item.regulatoryCategory || 'Categoria regulatória não informada'}</span>
              <span>{item.presentationCount} apresentação(ões) comercializada(s)</span>
            </div>
            <div className="row-badges">
              <RegistrationStatus status={item.status} compact/>
              {item.hasLeaflet && <StatusBadge label="Bula" tone="good"/>}
              {item.hasCmed && <StatusBadge label="Preço publicado na CMED" tone="info"/>}
              {item.hasAlert && <StatusBadge label="Ocorrência" tone="warn"/>}
            </div>
          </Link>)}</div>}

        {filtered.length > PAGE_SIZE && <nav className="pagination" aria-label="Paginação dos medicamentos relacionados">
          <button disabled={currentPage <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}><ChevronLeft size={16}/> Anterior</button>
          <span>Página {currentPage} de {totalPages}</span>
          <button disabled={currentPage >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>Próxima <ChevronRight size={16}/></button>
        </nav>}
      </div>
    </div>
  </div>
}
