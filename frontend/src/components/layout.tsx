import { useState, type ReactNode } from 'react';
import { useAuth } from '../auth/AuthProvider';
import { Button } from './ui';
export function Logo(){return <button className="logo" onClick={()=>navigate('/')} aria-label="Mueblería Iván, ir al inicio"><img className="logo-symbol" src="/assets/brand/muebleria-ivan-logo.png" alt="" aria-hidden="true"/></button>}
export const navigate=(to:string)=>{window.history.pushState({},'',to);window.dispatchEvent(new PopStateEvent('popstate'))};
export function Navbar(){
  const auth=useAuth();
  const [menuOpen,setMenuOpen]=useState(false);
  const isStaff=auth?.profile?.role==='admin'||auth?.profile?.role==='operator';
  const accountPath=!auth?.session?'/iniciar-sesion':isStaff?'/admin':'/mi-cuenta';
  const accountLabel=!auth?.session?'Iniciar sesión':isStaff?'Panel administrativo':'Mi cuenta';
  const handleLink=(event:React.MouseEvent<HTMLAnchorElement>)=>{go(event);setMenuOpen(false)};

  return <div className="navbar-wrap"><header className="navbar"><Logo/><button className="menu-toggle" type="button" aria-label={menuOpen?'Cerrar menú':'Abrir menú'} aria-expanded={menuOpen} onClick={()=>setMenuOpen(value=>!value)}><span/><span/></button><nav className={menuOpen?'primary-nav is-open':'primary-nav'} aria-label="Navegación principal"><a href="/" onClick={handleLink}>Inicio</a><a href="/catalogo" onClick={handleLink}>Catálogo</a><a href="/#como-funciona" onClick={handleLink}>¿Cómo trabajamos?</a><div className="nav-mobile-actions"><button onClick={()=>navigate(accountPath)}>{accountLabel}</button><Button onClick={()=>navigate('/cotizador')}>Cotizar proyecto</Button></div></nav><div className="nav-actions"><button className="view-switch" onClick={()=>navigate(accountPath)}>{accountLabel}</button><Button onClick={()=>navigate('/cotizador')}>Cotizar proyecto</Button></div></header></div>
}
function go(e:React.MouseEvent<HTMLAnchorElement>){e.preventDefault();navigate(e.currentTarget.getAttribute('href')!.replace('/#como-funciona','/'));setTimeout(()=>document.getElementById('como-funciona')?.scrollIntoView({behavior:'smooth'}),0)}
export function Footer(){return <footer className="footer"><div><div className="footer-logo">Mueblería <i>Iván</i></div><p>Diseñamos muebles que hacen hogar.</p></div><p>Lima, Perú · Atención personalizada</p><div className="footer-links"><a href="/catalogo" onClick={go}>Catálogo</a><a href="/cotizador" onClick={go}>Cotiza tu mueble</a></div></footer>}
const side=[['/admin','▦','Resumen'],['/admin/cotizaciones','▧','Cotizaciones'],['/admin/pedidos','□','Pedidos'],['/admin/kanban','▤','Producción'],['/admin/pagos','◉','Pagos'],['/admin/clientes','♙','Clientes'],['/admin/catalogo','◇','Catálogo'],['/admin/analitica','✦','Análisis IA'],['/admin/optimizaciones','↗','Optimizaciones']];
export function AdminLayout({children,title,subtitle}:{children:ReactNode;title:string;subtitle:string}){const current=window.location.pathname;return <div className="admin-shell"><aside className="sidebar"><Logo/><p className="sidebar-caption">PANEL ADMINISTRATIVO</p><nav aria-label="Navegación administrativa">{side.map(([href,icon,label])=><a key={href} href={href} onClick={go} className={current===href?'active':''} aria-label={label} title={label}><span aria-hidden="true">{icon}</span>{label}</a>)}</nav><div className="sidebar-bottom"><button onClick={()=>navigate('/')} className="back-client">← Vista cliente</button><small>Mueblería Iván<br/>Lima, Perú</small></div></aside><main className="admin-main"><header className="admin-header"><div><p>{subtitle}</p><h1>{title}</h1></div><div className="admin-user"><span aria-hidden="true">MI</span><div><b>Iván Ramos</b><small>Administrador</small></div></div></header>{children}</main></div>}
