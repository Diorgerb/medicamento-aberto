import type { ProductCatalogItem } from '../types/data'
import { matchesSearch } from './format'

export interface ProductFilterValues {
  query: string
  category: string
  status: string
  onlyLeaflet: boolean
  onlyCmed: boolean
  onlyAlert: boolean
}

export const EMPTY_PRODUCT_FILTERS: ProductFilterValues = {
  query: '',
  category: '',
  status: '',
  onlyLeaflet: false,
  onlyCmed: false,
  onlyAlert: false,
}

export function productMatchesFilters(item: ProductCatalogItem, filters: ProductFilterValues) {
  if (filters.query && !matchesSearch([
    item.name,
    item.registrationNumber,
    item.processNumber,
    item.companyName,
    item.companyCnpj,
    item.regulatoryCategory,
    ...item.activeIngredients,
  ].join(' '), filters.query)) return false

  if (filters.category && item.regulatoryCategory !== filters.category) return false
  if (filters.status && item.status !== filters.status) return false
  if (filters.onlyLeaflet && !item.hasLeaflet) return false
  if (filters.onlyCmed && !item.hasCmed) return false
  if (filters.onlyAlert && !item.hasAlert) return false
  return true
}

export function hasFacetFilters(filters: ProductFilterValues) {
  return Boolean(
    filters.category ||
    filters.status ||
    filters.onlyLeaflet ||
    filters.onlyCmed ||
    filters.onlyAlert
  )
}
