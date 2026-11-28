# Identidad visual de Mueblería Iván

## Idea de marca

El símbolo es un monograma geométrico M/I. La M se construye con tres trazos rectos y un vértice central; el asta de la I nace en ese ensamble y se integra en el espacio negativo. Las proporciones aluden a cortes precisos y uniones de carpintería sin ilustrar muebles, casas ni herramientas. La silueta funciona en una tinta y conserva su lectura a tamaño favicon.

La firma escribe siempre **Mueblería Iván**, con ambas tildes. Playfair Display aporta el tono editorial: “Mueblería” va en redonda e “Iván” en cursiva. Inter se reserva para navegación, etiquetas y texto de interfaz.

## Paleta

| Nombre | Código | Uso |
| --- | --- | --- |
| Marrón nogal | `#3D2B1F` | Símbolo, títulos y firma principal |
| Terracota | `#A45C40` | Asta I del monograma y acento tipográfico |
| Beige natural | `#D8C4AD` | Acento para la versión invertida |
| Marfil | `#F5F2ED` | Fondo claro y tinta de la versión invertida |
| Negro cálido | `#26221E` | Texto y versión monocromática |

El símbolo principal combina nogal y terracota. No se añaden degradados, sombras, texturas ni contenedores decorativos. La versión monocromática utiliza una única tinta; la invertida usa marfil y beige sobre negro cálido.

## Tipografía

- **Firma:** Playfair Display Semibold. `Mueblería` en redonda y `Iván` en cursiva.
- **Interfaz:** Inter para navegación, controles, etiquetas y texto funcional.
- Si un entorno no carga las fuentes web, los SVG declaran Georgia/serif como alternativa para la firma. El texto de los logotipos permanece como texto editable.

## Archivos vectoriales

Todos los archivos SVG son editables en Illustrator y pueden implementarse directamente en web.

| Archivo | Uso |
| --- | --- |
| `frontend/public/assets/brand/muebleria-ivan-horizontal.svg` | Logotipo principal horizontal |
| `frontend/public/assets/brand/muebleria-ivan-vertical.svg` | Composición vertical |
| `frontend/public/assets/brand/muebleria-ivan-logo.svg` | Monograma independiente |
| `frontend/public/assets/brand/muebleria-ivan-monochrome.svg` | Firma monocromática de una tinta |
| `frontend/public/assets/brand/muebleria-ivan-inverse.svg` | Firma invertida sobre negro cálido |
| `frontend/public/assets/brand/favicon-16.svg` | Favicon de 16 × 16 |
| `frontend/public/assets/brand/favicon-32.svg` | Favicon de 32 × 32 |
| `frontend/public/assets/brand/identity-board.svg` | Lámina de identidad y aplicación de cabecera web |

El área libre mínima recomendada alrededor del monograma equivale al ancho de su asta central. En tamaños de interfaz se recomienda usar el monograma solo desde 16 px y la firma horizontal desde 180 px de ancho. No inclinar, estirar ni añadir contornos al símbolo.

## Uso en el producto

La cabecera del frontend usa el monograma nogal/terracota junto a la firma tipográfica. El portal de acceso usa la variante clara del monograma sobre su fondo oscuro. El favicon enlaza versiones optimizadas para 16 y 32 píxeles. La lámina `identity-board.svg` presenta las composiciones, la paleta, la tipografía y una aplicación esquemática de la cabecera.
