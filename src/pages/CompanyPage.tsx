import { Building2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState'
import { Loading } from '../components/Loading'
import { RelatedProductsExplorer } from '../components/RelatedProductsExplorer'
import { getCatalog, getCompanies } from '../lib/data'
import { formatCnpj } from '../lib/format'
import type { CompanyCatalogItem, ProductCatalogItem } from '../types/data'

export function CompanyPage() {
  const { id = '' } = useParams()
  const [company, setCompany] = useState<CompanyCatalogItem | null>(null)
  const [products, setProducts] = useState<ProductCatalogItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getCompanies(), getCatalog()])
      .then(([companies, catalog]) => {
        setCompany(companies.find((item) => item.id === id) ?? null)
        setProducts(catalog.filter((product) => product.companyId === id))
      })
      .finally(() => setLoading(false))
  }, [id])

  const ingredients = useMemo(() => Array.from(new Set<string>(products.flatMap((product) => product.activeIngredients))).sort((a, b) => a.localeCompare(b, 'pt-BR')), [products])
  const activeCount = useMemo(() => products.filter((product) => product.status === 'Ativo').length, [products])
  const inactiveCount = useMemo(() => products.filter((product) => product.status === 'Inativo').length, [products])

  if (loading) return <section className="page-section"><div className="container"><Loading/></div></section>
  if (!company) return <section className="page-section"><div className="container"><EmptyState title="Empresa não encontrada"/></div></section>

  return <section className="page-section"><div className="container">
    <div className="entity-hero">
      <div className="product-icon"><Building2 size={28}/></div>
      <div><div className="eyebrow">Empresa</div><h1>{company.name}</h1><p>{formatCnpj(company.cnpj)}</p></div>
    </div>

    <div className="stats-grid entity-stats-grid">
      <div className="metric-card"><strong>{company.productCount}</strong><span>Produtos</span></div>
      <div className="metric-card"><strong>{activeCount}</strong><span>Registros ativos</span></div>
      <div className="metric-card"><strong>{inactiveCount}</strong><span>Registros inativos</span></div>
      <div className="metric-card"><strong>{company.presentationCount}</strong><span>Apresentações comercializadas</span></div>
      <div className="metric-card"><strong>{ingredients.length}</strong><span>Princípios ativos</span></div>
    </div>

    <RelatedProductsExplorer
      products={products}
      searchPlaceholder="Nome, registro, processo ou princípio ativo"
      emptyText="Nenhum medicamento desta empresa corresponde aos filtros selecionados."
    />
  </div></section>
}
