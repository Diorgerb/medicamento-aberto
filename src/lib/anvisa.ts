const ANVISA_CONSULTAS_BASE = 'https://consultas.anvisa.gov.br/#'

function onlyDigits(value: string | null | undefined) {
  return String(value ?? '').replace(/\D/g, '')
}

/** Consulta oficial de medicamentos da Anvisa por registro do produto (9 dígitos). */
export function anvisaMedicineRegistrationUrl(value: string | null | undefined) {
  const registration = onlyDigits(value)
  if (registration.length !== 9) return null
  return `${ANVISA_CONSULTAS_BASE}/medicamentos/q/?numeroRegistro=${encodeURIComponent(registration)}`
}

/** Consulta oficial de medicamentos da Anvisa por número de processo. */
export function anvisaMedicineProcessUrl(value: string | null | undefined) {
  const process = onlyDigits(value)
  if (!process) return null
  return `${ANVISA_CONSULTAS_BASE}/medicamentos/q/?numeroProcesso=${encodeURIComponent(process)}`
}

/** Consulta oficial do Bulário Eletrônico da Anvisa por registro do produto (9 dígitos). */
export function anvisaLeafletUrl(value: string | null | undefined) {
  const registration = onlyDigits(value)
  if (registration.length !== 9) return null
  return `${ANVISA_CONSULTAS_BASE}/bulario/q/?numeroRegistro=${encodeURIComponent(registration)}`
}
