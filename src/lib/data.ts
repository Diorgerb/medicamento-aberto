import type {
  CompanyCatalogItem,
  IngredientCatalogItem,
  Manifest,
  ProductCatalogItem,
  ProductDetail,
  QualityReport,
  SourceCatalogItem,
  ActivityFeed,
} from '../types/data'

const BASE = '/data'
const cache = new Map<string, unknown>()
const bucketCache = new Map<string, ProductDetail[]>()

async function getJson<T>(url: string): Promise<T> {
  if (cache.has(url)) return cache.get(url) as T
  const response = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!response.ok) throw new Error(`Falha ao carregar ${url} (${response.status})`)
  const data = await response.json() as T
  cache.set(url, data)
  return data
}

export const getManifest = () => getJson<Manifest>(`${BASE}/manifest.json`)
export const getCatalog = () => getJson<ProductCatalogItem[]>(`${BASE}/catalog/products.json`)
export const getCompanies = () => getJson<CompanyCatalogItem[]>(`${BASE}/catalog/companies.json`)
export const getIngredients = () => getJson<IngredientCatalogItem[]>(`${BASE}/catalog/ingredients.json`)
export const getSources = () => getJson<SourceCatalogItem[]>(`${BASE}/catalog/sources.json`)
export const getQualityReport = () => getJson<QualityReport>(`${BASE}/quality-report.json`)
export const getActivityFeed = () => getJson<ActivityFeed>(`${BASE}/catalog/activity.json`)

export async function getProduct(id: string, bucket?: string): Promise<ProductDetail | null> {
  let selectedBucket = bucket
  if (!selectedBucket) {
    const catalog = await getCatalog()
    selectedBucket = catalog.find((item) => item.id === id)?.bucket
  }
  if (!selectedBucket) return null

  let items = bucketCache.get(selectedBucket)
  if (!items) {
    items = await getJson<ProductDetail[]>(`${BASE}/products/${selectedBucket}.json`)
    bucketCache.set(selectedBucket, items)
  }
  return items.find((item) => item.id === id) ?? null
}
