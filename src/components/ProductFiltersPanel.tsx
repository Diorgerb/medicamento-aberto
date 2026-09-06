import { Filter, Search } from 'lucide-react'
import { useMemo } from 'react'
import type { ProductCatalogItem } from '../types/data'
import type { ProductFilterValues } from '../lib/productFilters'

interface Props {
  products: ProductCatalogItem[]
  values: ProductFilterValues
  onChange: (next: ProductFilterValues) => void
  searchPlaceholder?: string
  showSearch?: boolean
}

export function ProductFiltersPanel({
  products,
  values,
  onChange,
  searchPlaceholder = 'Pesquisar nesta lista',
  showSearch = true,
}: Props) {
  const categories = useMemo(
    () => Array.from(new Set(products.map((item) => item.regulatoryCategory).filter(Boolean))).sort((a, b) => a.localeCompare(b, 'pt-BR')),
    [products],
  )
  const statuses = useMemo(
    () => Array.from(new Set(products.map((item) => item.status).filter(Boolean))).sort((a, b) => a.localeCompare(b, 'pt-BR')),
    [products],
  )

  const patch = (next: Partial<ProductFilterValues>) => onChange({ ...values, ...next })
  const clear = () => onChange({
    query: '',
    category: '',
    status: '',
    onlyLeaflet: false,
    onlyCmed: false,
    onlyAlert: false,
  })

  return <aside className="filters-panel" aria-label="Filtros rápidos de medicamentos">
    <div className="filters-title"><Filter size={16}/> Filtros rápidos</div>

    {showSearch && <label className="filter-search-label">
      Buscar na lista
      <span className="filter-search-input"><Search size={15}/><input value={values.query} onChange={(event) => patch({ query: event.target.value })} placeholder={searchPlaceholder}/></span>
    </label>}

    <label>Categoria regulatória
      <select value={values.category} onChange={(event) => patch({ category: event.target.value })}>
        <option value="">Todas</option>
        {categories.map((value) => <option value={value} key={value}>{value}</option>)}
      </select>
    </label>

    <label>Situação do registro
      <select value={values.status} onChange={(event) => patch({ status: event.target.value })}>
        <option value="">Todas</option>
        {statuses.map((value) => <option value={value} key={value}>{value}</option>)}
      </select>
    </label>

    <fieldset className="filter-fieldset">
      <legend>Camadas relacionadas</legend>
      <label className="check-row"><input type="checkbox" checked={values.onlyLeaflet} onChange={(event) => patch({ onlyLeaflet: event.target.checked })}/> Possui bula</label>
      <label className="check-row"><input type="checkbox" checked={values.onlyCmed} onChange={(event) => patch({ onlyCmed: event.target.checked })}/> Possui preço publicado na CMED</label>
      <label className="check-row"><input type="checkbox" checked={values.onlyAlert} onChange={(event) => patch({ onlyAlert: event.target.checked })}/> Possui ocorrência</label>
    </fieldset>

    <button type="button" className="ghost-button" onClick={clear}>Limpar filtros</button>
  </aside>
}
