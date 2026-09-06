export function normalizeText(value: string | null | undefined) {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export function matchesSearch(searchText: string, query: string) {
  const haystack = normalizeText(searchText)
  const tokens = normalizeText(query).split(' ').filter(Boolean)
  return tokens.every((token) => haystack.includes(token))
}

export function digits(value: string | null | undefined) {
  return (value ?? '').replace(/\D/g, '')
}

export function formatRegistration(value: string | null | undefined) {
  const d = digits(value)
  if (!d) return 'Não se aplica / não informado'
  if (d.length === 9) return `${d[0]}.${d.slice(1, 5)}.${d.slice(5, 9)}`
  if (d.length === 13) return `${d.slice(0, 9)}-${d.slice(9)}`
  return value || d
}

export function formatCnpj(value: string | null | undefined) {
  const d = digits(value)
  if (d.length !== 14) return value || '—'
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`
}

export function formatExpedient(value: string | null | undefined) {
  const d = digits(value)
  if (d.length !== 10) return valueOrDash(value)
  return `${d.slice(0, 7)}/${d.slice(7, 9)}-${d.slice(9)}`
}

export function formatNumber(value: number | undefined) {
  return new Intl.NumberFormat('pt-BR').format(value ?? 0)
}

export function formatBytes(value: number | undefined) {
  const bytes = value ?? 0
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / 1024 ** exponent).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} ${units[exponent]}`
}

function pad(value: number) {
  return String(value).padStart(2, '0')
}

function validDateParts(day: number, month: number, year: number) {
  if (year < 1900 || year > 2200 || month < 1 || month > 12 || day < 1 || day > 31) return false
  const date = new Date(Date.UTC(year, month - 1, day))
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day
}

/** Formata datas já publicadas como DD/MM/AAAA, sem reinterpretar timezone. */
export function formatDateDMY(value: string | null | undefined) {
  const text = valueOrDash(value)
  if (text === '—') return text
  const match = text.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?$/)
  if (!match) return text
  const day = Number(match[1]), month = Number(match[2]), year = Number(match[3])
  if (!validDateParts(day, month, year)) return text
  const time = match[4] ? ` ${match[4]}:${match[5]}${match[6] ? `:${match[6]}` : ''}` : ''
  return `${pad(day)}/${pad(month)}/${year}${time}`
}

/** Converte as datas MM/DD/YYYY HH:mm:ss dos exports ANVISA para DD/MM/AAAA HH:mm:ss. */
export function formatDateTimeMDY(value: string | null | undefined, includeTime = true) {
  const text = valueOrDash(value)
  if (text === '—') return text
  const match = text.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?$/)
  if (!match) return text
  const month = Number(match[1]), day = Number(match[2]), year = Number(match[3])
  if (!validDateParts(day, month, year)) return text
  const time = includeTime && match[4]
    ? ` ${match[4]}:${match[5]}${match[6] ? `:${match[6]}` : ''}`
    : ''
  return `${pad(day)}/${pad(month)}/${year}${time}`
}

/** DATA_VENCIMENTO_REGISTRO da base principal vem como MMAAAA. */
export function formatMonthYear(value: string | null | undefined) {
  const text = valueOrDash(value)
  if (text === '—') return text
  const d = digits(text)
  if (d.length !== 6) return text
  const month = Number(d.slice(0, 2))
  if (month < 1 || month > 12) return text
  return `${d.slice(0, 2)}/${d.slice(2)}`
}

/** Datas ISO geradas pelo próprio pipeline. */
export function humanDate(value: string | null | undefined) {
  if (!value) return '—'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
    timeZone: 'America/Sao_Paulo',
  }).format(parsed)
}

export function valueOrDash(value: unknown) {
  if (value === null || value === undefined) return '—'
  const text = String(value).trim()
  return text && !['nan', 'none', 'null', '<na>'].includes(text.toLowerCase()) ? text : '—'
}

export function formatPrice(value: string | null | undefined) {
  const text = valueOrDash(value)
  if (text === '—') return text
  const numeric = Number(text.replace(/\./g, '').replace(',', '.'))
  if (Number.isNaN(numeric)) return text
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numeric)
}

/** Formatação contextual dos valores brutos exibidos no site. */
export function formatSourceField(sourceKey: string, column: string, value: string | null | undefined) {
  const text = valueOrDash(value)
  if (text === '—') return text

  if (sourceKey === 'medicamentos') {
    if (column === 'DATA_FINALIZACAO_PROCESSO') return formatDateDMY(text)
    if (column === 'DATA_VENCIMENTO_REGISTRO') return formatMonthYear(text)
    if (column === 'NUMERO_REGISTRO_PRODUTO') return formatRegistration(text)
  }

  if (sourceKey === 'bula_produto') {
    if (column === 'DATA_ULTIMA_ATUALIZACAO_BULARIO' || column === 'DATA_CARGA_ETL') return formatDateTimeMDY(text)
    if (column === 'NUMERO_REGISTRO_PRODUTO') return formatRegistration(text)
    if (column === 'NUMERO_EXPEDIENTE_ATUAL') return formatExpedient(text)
    if (column === 'CNPJ_EMPRESA') return formatCnpj(text)
  }

  if (sourceKey === 'bula_documento') {
    if (column.startsWith('DATA_')) return formatDateTimeMDY(text)
    if (column === 'NUMERO_EXPEDIENTE') return formatExpedient(text)
  }

  if (sourceKey === 'irregulares') {
    if (column.startsWith('DT_')) return formatDateTimeMDY(text, false)
    if (column === 'REGISTRO') return formatRegistration(text)
    if (column === 'NU_CNPJ' || column === 'NU_CNPJ_EMPRESA_INVESTIGADA') return formatCnpj(text)
  }

  return text
}

export function sortTaxBands(bands: string[]) {
  return [...bands].sort((a, b) => {
    const key = (value: string): [number, number, number] => {
      if (normalizeText(value) === 'sem impostos') return [0, -1, 0]
      const match = value.match(/(\d+(?:[,.]\d+)?)/)
      const rate = match ? Number(match[1].replace(',', '.')) : 999
      return [1, rate, normalizeText(value).includes('alc') ? 1 : 0]
    }
    const ka = key(a), kb = key(b)
    return ka[0] - kb[0] || ka[1] - kb[1] || ka[2] - kb[2] || a.localeCompare(b, 'pt-BR')
  })
}
