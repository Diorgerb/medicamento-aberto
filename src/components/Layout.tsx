import { Menu, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { BrandLogo, BrandMark } from './Brand'
import { ViewModeSelector } from './ViewModeSelector'

const nav = [
  ['Medicamentos', '/medicamentos'],
  ['Empresas', '/empresas'],
  ['Princípios ativos', '/principios-ativos'],
  ['Transparência', '/transparencia'],
  ['Atualizações', '/atualizacoes'],
  ['Sobre', '/sobre'],
]

export function Layout() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  }, [pathname])
  return <div className="app-shell">
    <a className="skip-link" href="#conteudo-principal">Ir para o conteúdo principal</a>
    <header className="site-header">
      <div className="container header-inner">
        <Link to="/" className="brand" aria-label="Medicamento Aberto — página inicial" onClick={() => setOpen(false)}>
          <BrandLogo compact/>
        </Link>
        <nav className={`main-nav ${open ? 'open' : ''}`} aria-label="Navegação principal">
          {nav.map(([label, href]) => <NavLink key={href} to={href} onClick={() => setOpen(false)}>{label}</NavLink>)}
        </nav>
        <div className="header-actions"><ViewModeSelector compact/><button className="menu-button" aria-label={open ? 'Fechar menu' : 'Abrir menu'} aria-expanded={open} onClick={() => setOpen((current) => !current)}>{open ? <X size={22}/> : <Menu size={22}/>}</button></div>
      </div>
    </header>
    <main id="conteudo-principal" tabIndex={-1}><Outlet/></main>
    <footer className="site-footer">
      <div className="container footer-brand-row">
        <BrandLogo inverse/>
        <p className="footer-tagline">Dados públicos para uma saúde mais transparente.</p>
      </div>
      <div className="container footer-grid">
        <div><strong>Medicamento Aberto</strong><p>Plataforma integrada de dados abertos sobre medicamentos no Brasil.</p></div>
        <div><strong>Informação em contexto</strong><p>Regularização, apresentações, Bulário, CMED e fiscalização reunidos em uma experiência única.</p></div>
        <div><strong>Transparência e reúso</strong><p><Link to="/transparencia">Explore os indicadores</Link> · <Link to="/reutilize">Reutilize os dados</Link></p><p className="footer-author">Criado por <a href="https://diorgerb.github.io/Portfolio/" target="_blank" rel="noreferrer">Diórger Bretas</a></p></div>
      </div>
      <BrandMark size={170} className="footer-watermark"/>
    </footer>
  </div>
}
