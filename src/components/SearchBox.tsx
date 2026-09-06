import { Search } from 'lucide-react'
import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export function SearchBox({ initial = '', large = false }: { initial?: string; large?: boolean }) {
  const [value, setValue] = useState(initial)
  const navigate = useNavigate()

  function submit(event: FormEvent) {
    event.preventDefault()
    const q = value.trim()
    navigate(q ? `/medicamentos?q=${encodeURIComponent(q)}` : '/medicamentos')
  }

  return (
    <form className={`search-box ${large ? 'large' : ''}`} onSubmit={submit}>
      <Search size={large ? 22 : 18} />
      <input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Medicamento, princípio ativo, registro, empresa, CNPJ ou processo"
        aria-label="Pesquisar base de medicamentos"
      />
      <button type="submit">Pesquisar</button>
    </form>
  )
}
