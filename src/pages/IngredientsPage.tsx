import { Search, Tags } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState'
import { Loading } from '../components/Loading'
import { ProductFiltersPanel } from '../components/ProductFiltersPanel'
import { getCatalog, getIngredients } from '../lib/data'
import { normalizeText } from '../lib/format'
import { EMPTY_PRODUCT_FILTERS, hasFacetFilters, productMatchesFilters, type ProductFilterValues } from '../lib/productFilters'
import type { IngredientCatalogItem, ProductCatalogItem } from '../types/data'

export function IngredientsPage() {
  const [items, setItems] = useState<IngredientCatalogItem[]>([])
  const [products, setProducts] = useState<ProductCatalogItem[]>([])
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<ProductFilterValues>(EMPTY_PRODUCT_FILTERS)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getIngredients(), getCatalog()])
      .then(([ingredients, catalog]) => { setItems(ingredients); setProducts(catalog) })
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
      product.activeIngredients.forEach((ingredient) => {
        const key = normalizeText(ingredient)
        if (key) counts.set(key, (counts.get(key) ?? 0) + 1)
      })
    })
    return counts
  }, [matchingProducts])

  const filtered = useMemo(() => {
    const q = normalizeText(query)
    return items.filter((item) => {
      const key = normalizeText(item.name)
      if (q && !key.includes(q)) return false
      if (facetActive && !(matchCounts.get(key) ?? 0)) return false
      return true
    })
  }, [items, query, facetActive, matchCounts])

  return <section className="page-section"><div className="container">
    <div className="page-heading">
      <div><div className="eyebrow">Substâncias</div><h1>Princípios ativos</h1><p>Explore os princípios ativos e refine pelas características dos medicamentos relacionados.</p></div>
      <span className="result-count">{filtered.length.toLocaleString('pt-BR')} princípios ativos</span>
    </div>

    <div className="inline-search entity-primary-search"><Search size={18}/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Pesquisar princípio ativo"/></div>

    {loading ? <Loading/> : <div className="catalog-layout entity-catalog-layout">
      <ProductFiltersPanel products={products} values={filters} onChange={setFilters} showSearch={false}/>
      <div>
        <div className="entity-filter-summary">
          <strong>{filtered.length.toLocaleString('pt-BR')}</strong>
          <span>{facetActive ? 'princípios ativos com medicamentos que atendem aos filtros' : 'princípios ativos disponíveis na base'}</span>
        </div>
        {filtered.length === 0 ? <EmptyState title="Nenhum princípio ativo encontrado" text="Remova alguns filtros ou use outro termo de pesquisa."/> : <div className="entity-grid">{filtered.slice(0, 500).map((item) => {
          const matched = matchCounts.get(normalizeText(item.name)) ?? 0
          return <Link className="entity-card" to={`/principios-ativos/${item.id}`} key={item.id}>
            <Tags size={21}/>
            <div>
              <strong>{item.name}</strong>
              <span>{facetActive ? `${matched} medicamento(s) atendem aos filtros` : `${item.productCount} medicamento(s)`}</span>
              <small>{item.companyCount} empresa(s)</small>
            </div>
          </Link>
        })}</div>}
        {filtered.length > 500 && <div className="callout info">Exibindo os primeiros 500 resultados. Refine a pesquisa ou os filtros rápidos.</div>}
      </div>
    </div>}
  </div></section>
}
