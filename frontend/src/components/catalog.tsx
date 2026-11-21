import type { Product } from '../types';
import { Button, ProductVisual } from './ui';
import { navigate } from './layout';
import { money } from '../utils/format';
export function ProductCard({product}:{product:Product}){return <article className="product-card"><ProductVisual kind={product.visual}/><div className="product-copy"><span className="eyebrow">{product.category}</span><h3>{product.name}</h3><p>{product.description}</p><strong>Desde {money(product.priceReference)}</strong><div className="card-actions"><Button variant="secondary" onClick={()=>navigate(`/producto/${product.id}`)}>Ver detalle</Button><button className="text-button" onClick={()=>navigate(`/cotizador?producto=${product.id}`)}>Cotizar similar →</button></div></div></article>}
