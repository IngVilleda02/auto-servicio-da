# DESIGN.md — Auto Servicio D&A

Dirección: **showroom de taller**, inspirada en la organización y el ritmo editorial de BMW (sin usar su marca, fotos, logotipos ni textos).

## Mundo visual
- Ritmo de secciones (grises y rojo): encabezado blanco → hero oscuro con línea roja de 4px abajo → franja de datos gris → recorrido de servicios en blanco → proceso en carbón → reseñas en banda roja → contacto blanco → ubicación gris → pie carbón con línea roja arriba.
- Logotipo: `img/logo-da.png` (recorte de `Imagenes/LOGONEW.png`, fondo blanco). Va siempre sobre blanco.
- Ángulos rectos en todo (radio 0). Sin sombras: la profundidad viene del contraste oscuro/claro y de la fotografía.
- Líneas finas (1px) como estructura: listas, tablas, reseñas y FAQ separan con reglas, no con tarjetas.
- Paleta roja y gris (preferencia del cliente). El rojo solo marca acciones (botón principal, foco, hover de enlaces); nunca como fondo decorativo. El azul queda solo dentro del logotipo.
- Hover solo en dispositivos con puntero (`@media (hover: hover) and (pointer: fine)`).

## Tokens (`css/styles.css`, `:root`)
| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#ffffff` | Fondo principal |
| `--bg-alt` | `#eceef0` | Gris frío: franja de datos y secciones secundarias |
| `--ink` | `#1e2023` | Texto |
| `--meta` | `#5a5f66` | Texto secundario (≥4.5:1 sobre blanco y gris) |
| `--line` | `#d0d4d9` | Reglas |
| `--dark` / `--dark-2` | `#1c1e21` / `#26292d` | Gris carbón: proceso, panel de cotización, pie |
| `--silver` | `#b9bec5` | Texto secundario sobre carbón |
| `--accent-deep` | `#7a0d12` | Banda roja de reseñas (blanco 10:1) |
| `--accent` / `--accent-dark` | `#c4161c` / `#8f0f14` | Rojo del logotipo: acción / hover y foco (blanco sobre rojo 6:1) |

## Tipografía
- Una sola familia: **Archivo** (Google Fonts) en 300, 400 y 700.
- Títulos H1/H2 en 300, mayúsculas, interlineado 1.02–1.1. H1 máx. 5.75rem.
- Subtítulos de servicio y trabajo en 400; botones, navegación y etiquetas en 700.
- Etiquetas de datos (Teléfono, Hoy…) en 0.78rem, mayúsculas, tracking 0.1em.

## Componentes
- **Botón:** 52px de alto, 1px de borde, sin radio. Primario rojo; sobre negro, contorno blanco. Feedback de 120–160 ms (color y `scale(.98)` al presionar).
- **Qualitas:** logotipo sobre placa blanca en la banda negra del proceso.
- **Enlace con flecha:** texto 700 subrayado por borde, flecha SVG que avanza 4px al hover.
- **Recorrido de servicios:** 6 etapas numeradas en rojo (Cotización → Refacciones → Taller mecánico, con alineación y balanceo si se requiere → Hojalatería → Pintura → Entrega). Cotización y Entrega usan un panel tipográfico oscuro en lugar de foto. En escritorio, panel fijo a la derecha que cambia de imagen (opacidad + escala 1.04 → 1, 600–900 ms) cuando la etapa cruza el centro de la pantalla (IntersectionObserver), barra roja de avance (`scaleY`) y contador 01/06; las etapas inactivas bajan a 38 % de opacidad. En móvil y tablet, cada etapa muestra su imagen.
- **Qualitas:** insignia blanca cuadrada con el logotipo y borde rojo inferior de 6px; título, texto y tres datos con línea roja superior.
- **Proceso:** pestañas Qualitas / particular; línea de tiempo de 4 pasos por tramos: aparece el nodo, se dibuja su tramo rojo hasta el siguiente (600 ms por paso) y aparece el siguiente. La línea nunca pasa por debajo de un número. En tablet y móvil, vertical (`scaleY`).
- **Proceso:** números ligeros grandes (contador CSS) con reglas oscuras.
- **Filtros:** pestañas de texto con subrayado de 3px.

## Movimiento
- Momento principal: al cargar, cada línea del título se descubre de izquierda a derecha como cinta de enmascarar que se despega (`clip-path`), con un filo blanco de 2px que viaja en el corte y desaparece al final. La foto del hero entra como una cámara que llega al carro (rotateY −11° y profundidad → reposo, 2.2 s) y después sube el texto. Con ratón, el carro se inclina en 3D siguiendo el puntero (máx. 6° en Y, 4° en X, un solo elemento, solo transform). Al salir del hero la imagen se aleja (CSS scroll-driven `animation-timeline: view()` donde hay soporte). El hero no lleva botones.
- Reseñas: carrusel automático (7 s por reseña) con barra de progreso, contador y botón Pausar; se detiene al pasar el cursor o enfocarlo. Sin flechas.
- Proceso: la línea roja se dibuja y los pasos entran escalonados al llegar a la sección y al cambiar de pestaña; sin JavaScript se ven los dos flujos completos.
- Cruce de opacidad en la vista previa de servicios.
- `prefers-reduced-motion`: sin animaciones de entrada (el título aparece completo) y el carrusel cambia de reseña sin deslizar.
