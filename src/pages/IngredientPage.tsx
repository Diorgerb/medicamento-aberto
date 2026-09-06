import { Tags } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState'
import { Loading } from '../components/Loading'
import { RelatedProductsExplorer } from '../components/RelatedProductsExplorer'
import { getCatalog, getIngredients } from '../lib/data'
import { normalizeText } from '../lib/format'
import type { IngredientCatalogItem, ProductCatalogItem } from '../types/data'

export function IngredientPage() {
  const { id = '' } = useParams()
  const [item, setItem] = useState<IngredientCatalogItem | null>(null)
  const [products, setProducts] = useState<ProductCatalogItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getIngredients(), getCatalog()])
      .then(([ingredients, catalog]) => {
        const found = ingredients.find((ingredient) => ingredient.id === id) ?? null
        setItem(found)
        if (found) setProducts(catalog.filter((product) => product.activeIngredients.some((ingredient) => normalizeText(ingredient) === normalizeText(found.name))))
      })
      .finally(() => setLoading(false))
  }, [id])

  const activeCount = useMemo(() => products.filter((product) => product.status === 'Ativo').length, [products])
  const inactiveCount = useMemo(() => products.filter((product) => product.status === 'Inativo').length, [products])
  const presentationCount = useMemo(() => products.reduce((sum, product) => sum + product.presentationCount, 0), [products])

  if (loading) return <section className="page-section"><div className="container"><Loading/></div></section>
  if (!item) return <section className="page-section"><div className="container"><EmptyState title="Princípio ativo não encontrado"/></div></section>

  return <section className="page-section"><div className="container">
    <div className="entity-hero">
      <div className="product-icon"><Tags size={28}/></div>
      <div><div className="eyebrow">Princípio ativo</div><h1>{item.name}</h1><p>{item.productCount} medicamento(s) em {item.companyCount} empresa(s)</p></div>
    </div>

    <div className="stats-grid entity-stats-grid">
      <div className="metric-card"><strong>{item.productCount}</strong><span>Produtos</span></div>
      <div className="metric-card"><strong>{activeCount}</strong><span>Registros ativos</span></div>
      <div className="metric-card"><strong>{inactiveCount}</strong><span>Registros inativos</span></div>
      <div className="metric-card"><strong>{presentationCount}</strong><span>Apresentações comercializadas</span></div>
      <div className="metric-card"><strong>{item.companyCount}</strong><span>Empresas</span></div>
    </div>

    <RelatedProductsExplorer
      products={products}
      searchPlaceholder="Nome, empresa, registro ou processo"
      emptyText="Nenhum medicamento com este princípio ativo corresponde aos filtros selecionados."
    />
  </div></section>
}
