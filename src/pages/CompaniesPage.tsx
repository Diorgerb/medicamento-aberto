import { Building2, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState'
import { Loading } from '../components/Loading'
import { ProductFiltersPanel } from '../components/ProductFiltersPanel'
import { getCatalog, getCompanies } from '../lib/data'
import { formatCnpj, normalizeText } from '../lib/format'
import { EMPTY_PRODUCT_FILTERS, hasFacetFilters, productMatchesFilters, type ProductFilterValues } from '../lib/productFilters'
import type { CompanyCatalogItem, ProductCatalogItem } from '../types/data'

export function CompaniesPage() {
  const [items, setItems] = useState<CompanyCatalogItem[]>([])
  const [products, setProducts] = useState<ProductCatalogItem[]>([])
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<ProductFilterValues>(EMPTY_PRODUCT_FILTERS)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getCompanies(), getCatalog()])
      .then(([companies, catalog]) => { setItems(companies); setProducts(catalog) })
      .finally(() => setLoading(false))
  }, [])

  const facetActive = hasFacetFilters(filters)
  const matchingProducts = useMemo(() => {
    const productFilters = { ...filters, query: '' }
    return facetActive ? products.filter((product) => productMatchesFilters(product, productFilters)) : products
  }, [products, filters, facetActive])

  const matchCounts = useMemo(() => {
    const counts = new Map<string, number>()
    matchingProducts.forEach((product) => {
      if (product.companyId) counts.set(product.companyId, (counts.get(product.companyId) ?? 0) + 1)
    })
    return counts
  }, [matchingProducts])

  const filtered = useMemo(() => {
    const q = normalizeText(query)
    return items.filter((item) => {
      if (q && !normalizeText(`${item.name} ${item.cnpj}`).includes(q)) return false
      if (facetActive && !(matchCounts.get(item.id) ?? 0)) return false
      return true
    })
  }, [items, query, facetActive, matchCounts])

  return <section className="page-section"><div className="container">
    <div className="page-heading">
      <div><div className="eyebrow">Titulares e empresas</div><h1>Empresas</h1><p>Encontre empresas e refine a listagem pelas características regulatórias dos medicamentos associados.</p></div>
      <span className="result-count">{filtered.length.toLocaleString('pt-BR')} empresas</span>
    </div>

    <div className="inline-search entity-primary-search"><Search size={18}/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Razão social ou CNPJ"/></div>

    {loading ? <Loading/> : <div className="catalog-layout entity-catalog-layout">
      <ProductFiltersPanel products={products} values={filters} onChange={setFilters} showSearch={false}/>
      <div>
        <div className="entity-filter-summary">
          <strong>{filtered.length.toLocaleString('pt-BR')}</strong>
          <span>{facetActive ? 'empresas com medicamentos que atendem aos filtros' : 'empresas disponíveis na base'}</span>
        </div>
        {filtered.length === 0 ? <EmptyState title="Nenhuma empresa encontrada" text="Remova alguns filtros ou pesquise por outra razão social/CNPJ."/> : <div className="entity-grid">{filtered.slice(0, 500).map((item) => {
          const matched = matchCounts.get(item.id) ?? 0
          return <Link className="entity-card" to={`/empresas/${item.id}`} key={item.id}>
            <Building2 size={21}/>
            <div>
              <strong>{item.name || 'Empresa não informada'}</strong>
              <span>{formatCnpj(item.cnpj)}</span>
              <small>{facetActive ? `${matched} medicamento(s) atendem aos filtros` : `${item.productCount} medicamento(s) · ${item.presentationCount} apresentação(ões) comercializada(s)`}</small>
            </div>
          </Link>
        })}</div>}
        {filtered.length > 500 && <div className="callout info">Exibindo os primeiros 500 resultados. Refine a pesquisa ou os filtros rápidos.</div>}
      </div>
    </div>}
  </div></section>
}
