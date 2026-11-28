# Identidad visual de Mueblería Iván

## Concepto

La marca conserva el emblema de la referencia: una silueta arquitectónica en forma de M que contiene dos puertas de gabinete. Las líneas rectas, el encuentro central y las hojas simétricas evocan diseño a medida y precisión de fabricación. El símbolo se dibuja con formas vectoriales planas, sin degradados, sombras ni texturas.

La firma escribe exactamente **Mueblería Iván**. Usa Inter Bold para “Mueblería” e Inter Bold Italic para “Iván”. El descriptor **DISEÑO A TU MEDIDA** va en mayúsculas con espaciado amplio. Playfair Display queda reservada a titulares editoriales de la interfaz; no forma parte del logotipo.

## Color y producción

| Nombre | Código | Uso |
| --- | --- | --- |
| Marrón nogal | `#3D2B1F` | Estructura del emblema y nombre |
| Terracota | `#A45C40` | “Iván” y acento de marca |
| Beige natural | `#D8C4AD` | Frentes de puertas y divisor |
| Marfil | `#F5F2ED` | Fondo claro y tinta de versión invertida |
| Negro cálido | `#26221E` | Descriptor y versión monocromática |

El símbolo principal combina nogal y beige (dos tintas). La variante monocromática usa una sola tinta y conserva las puertas como espacios negativos. La variante invertida usa colores planos sobre un fondo negro cálido. Los SVG se imprimen directamente como vectores y mantienen separadas la estructura, las puertas y las manijas.

## Tipografía

- **Logotipo:** Inter Bold; “Iván” en Inter Bold Italic.
- **Descriptor:** Inter Semibold, mayúsculas y tracking amplio.
- **Interfaz:** Inter para controles, navegación y texto funcional; Playfair Display para titulares editoriales.

Los SVG de firma mantienen el texto editable. Si Inter no está disponible, usan Arial como alternativa sans serif.

## Archivos vectoriales

Todos son SVG editables en Illustrator y aptos para web e impresión.

| Archivo | Uso |
| --- | --- |
| `frontend/public/assets/brand/muebleria-ivan-horizontal.svg` | Logotipo principal con descriptor |
| `frontend/public/assets/brand/muebleria-ivan-vertical.svg` | Composición vertical |
| `frontend/public/assets/brand/muebleria-ivan-logo.svg` | Emblema independiente |
| `frontend/public/assets/brand/muebleria-ivan-emblem-inverse.svg` | Emblema claro para fondos oscuros |
| `frontend/public/assets/brand/muebleria-ivan-monochrome.svg` | Logotipo de una tinta |
| `frontend/public/assets/brand/muebleria-ivan-inverse.svg` | Logotipo claro sobre negro cálido |
| `frontend/public/assets/brand/favicon-16.svg` | Emblema para 16 × 16 px |
| `frontend/public/assets/brand/favicon-32.svg` | Emblema para 32 × 32 px |
| `frontend/public/assets/brand/identity-board.svg` | Lámina editorial y aplicación de cabecera web |

## Movimiento e implementación

`frontend/src/components/BrandMark.tsx` dibuja el emblema con paths SVG inline. La cabecera puede animar cada puerta de forma independiente; la animación respeta `prefers-reduced-motion`. El mismo emblema existe como SVG estático para favicon, documentación e impresión.

La firma principal está en la cabecera junto al divisor y descriptor. El portal de acceso usa el emblema claro sobre fondo oscuro. Se recomienda conservar el espacio libre equivalente al ancho de una manija y no estirar, inclinar, contornear ni añadir efectos al símbolo.
