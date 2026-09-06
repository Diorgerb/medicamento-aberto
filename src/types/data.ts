export type RawValue = string | number | boolean | null

export interface SourceFileInfo {
  key: string
  label: string
  fileName: string
  rows: number
  columns: number
  bytes: number
  sha256: string
  downloadUrl: string
  officialPageUrl: string
  catalogUrl: string
  organization: string
  layer: string
  publicationDate: string
  headerMode: string
}

export interface SourceCatalogItem {
  key: string
  label: string
  organization: string
  description: string
  filenames: string[]
  download_url: string
  official_page_url: string
  catalog_url: string
  license_label: string
  format: string
  layer: string
  header_mode: string
  detected: boolean
  fileName: string
  rows: number
  columns: number
  bytes: number
  sha256: string
  publicationDate: string
}

export interface RelatedRecord {
  sourceKey: 'bula_produto' | 'bula_documento' | 'irregulares'
  matchMethod: string
  matchValue: string
  values: string[]
}

export interface CommercialPresentation {
  registrationNumber: string
  productRegistrationNumber: string
  description: string
  descriptions: string[]
  eans: string[]
  ggremCodes: string[]
  product: string
  substance: string
  companyCnpj: string
  laboratory: string
  therapeuticClass: string
  productType: string
  hospitalRestriction: string
  commercialization2025: string
  stripe: string
  commercialDestination: string
  economicRecordCount: number
}

export interface CmedRow {
  ggremCode: string
  registrationNumber: string
  registrationBase: string
  presentationRegistrationNumber: string
  productRegistrationNumber: string
  eans: string[]
  substance: string
  companyCnpj: string
  laboratory: string
  product: string
  presentation: string
  therapeuticClass: string
  productType: string
  priceRegime: string
  hospitalRestriction: string
  cap: string
  confaz87: string
  icmsZero: string
  appealAnalysis: string
  taxCreditList: string
  commercialization2025: string
  stripe: string
  commercialDestination: string
  factoryPrices: string[]
  consumerPrices: string[]
  governmentPrices: string[]
  governmentFactoryPriceMarkers: string[]
  factoryPriceConsistency: boolean | null
}

export interface ProductDetail {
  id: string
  bucket: string
  name: string
  processFinalizationDate: string
  regulatoryCategory: string
  registrationNumber: string
  registrationNumberDigits: string
  validProductRegistration: boolean
  registrationExpiry: string
  processNumber: string
  therapeuticClass: string
  companyId: string
  companyName: string
  companyCnpj: string
  status: string
  activeIngredients: string[]
  presentations: CommercialPresentation[]
  cmed: CmedRow[]
  leafletLatest: RelatedRecord[]
  leafletHistory: RelatedRecord[]
  alerts: RelatedRecord[]
  sourceLayers: {
    registration: boolean
    presentations: boolean
    cmed: boolean
    leaflets: boolean
    inspection: boolean
  }
  rawValues: string[]
}

export interface ProductCatalogItem {
  id: string
  bucket: string
  name: string
  registrationNumber: string
  registrationNumberDigits: string
  validProductRegistration: boolean
  regulatoryCategory: string
  activeIngredients: string[]
  companyId: string
  companyName: string
  companyCnpj: string
  processNumber: string
  status: string
  presentationCount: number
  hasLeaflet: boolean
  hasLeafletHistory: boolean
  hasCmed: boolean
  hasAlert: boolean
  leafletLatestDate?: string
  latestAlertDate?: string
}

export interface CompanyCatalogItem {
  id: string
  name: string
  cnpj: string
  authorization: string
  productCount: number
  presentationCount: number
}

export interface IngredientCatalogItem {
  id: string
  name: string
  productCount: number
  companyCount: number
}

export interface QualityMetrics {
  sourceMedicineRows?: number
  exactDuplicateMedicineRowsRemoved?: number
  products?: number
  productsWithRegistration?: number
  productsWithoutRegistration?: number
  productsWithMalformedRegistrationLength?: number
  productsWithoutCompany?: number
  productsWithoutActiveIngredient?: number
  productsWithLeaflet?: number
  productsWithLeafletHistory?: number
  productsWithCmed?: number
  productsWithInspectionOccurrence?: number
  commercialPresentations13?: number
  linkedCommercialPresentations13?: number
  unlinkedCommercialPresentations13?: number
  presentationLinkRate?: number
  cmedEconomicRecordsGgrem?: number
  linkedCmedEconomicRecordsGgrem?: number
  unlinkedCmedEconomicRecordsGgrem?: number
  cmedLinkRate?: number
  cmedPfMismatchGgrem?: number
  cmedInvalidPresentationRegistrationLength?: number
}

export interface QualityReport {
  pipelineVersion?: string
  metrics: QualityMetrics
  relationships?: Record<string, unknown>
  warnings?: string[]
}

export interface Manifest {
  project: string
  description: string
  generatedAt: string
  dataVersion: string
  pipelineVersion: string
  sourceMode: 'real'
  cmedTaxBands: string[]
  schemas: {
    medicamentos: string[]
    bula_produto: string[]
    bula_documento: string[]
    irregulares: string[]
  }
  counts: {
    products: number
    presentations: number
    linkedPresentations: number
    cmedEconomicRecords: number
    companies: number
    ingredients: number
    productsWithLeaflet: number
    productsWithLeafletHistory: number
    productsWithCmed: number
    productsWithAlert: number
  }
  sources: SourceFileInfo[]
}

export type ActivityType = 'leaflet' | 'inspection' | 'registration' | 'presentation' | 'cmed' | 'new'

export interface ActivityEvent {
  id: string
  type: ActivityType
  productId: string
  bucket: string
  productName: string
  registrationNumber: string
  status: string
  date: string
  title: string
  description: string
  sourceLabel: string
  detectedChange: boolean
}

export interface ActivityFeed {
  generatedAt: string
  previousVersion: string
  currentVersion: string
  hasPreviousSnapshot: boolean
  changes: ActivityEvent[]
  recentEvents: ActivityEvent[]
  counts: Record<string, number>
}
