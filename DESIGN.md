# DESIGN.md — Auto Servicio D&A

Dirección: **showroom de taller**, inspirada en la organización y el ritmo editorial de BMW (sin usar su marca, fotos, logotipos ni textos).

## Mundo visual
- Ritmo de secciones: encabezado blanco con logotipo → hero oscuro a sangre → franja de datos blanca → servicios en blanco → proceso en banda negra → trabajos en blanco → reseñas en gris → contacto blanco → ubicación gris → pie negro (logotipo sobre placa blanca).
- Logotipo: `img/logo-da.png` (recorte de `Imagenes/LOGONEW.png`, fondo blanco). Va siempre sobre blanco.
- Ángulos rectos en todo (radio 0). Sin sombras: la profundidad viene del contraste oscuro/claro y de la fotografía.
- Líneas finas (1px) como estructura: listas, tablas, reseñas y FAQ separan con reglas, no con tarjetas.
- El azul solo marca acciones (botón principal, foco, hover de enlaces). Nunca como fondo decorativo.

## Tokens (`css/styles.css`, `:root`)
| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#ffffff` | Fondo principal |
| `--bg-alt` | `#f2f2f2` | Secciones secundarias |
| `--ink` | `#262626` | Texto |
| `--meta` | `#666666` | Texto secundario (≥4.5:1 sobre blanco y gris) |
| `--line` | `#d4d4d4` | Reglas |
| `--dark` | `#0e0e0e` | Hero, proceso, encabezado, pie |
| `--silver` | `#bdbdbd` | Texto secundario sobre negro |
| `--blue` / `--blue-dark` | `#1c69d4` / `#0653b6` | Acción / hover y foco |

## Tipografía
- Una sola familia: **Archivo** (Google Fonts) en 300, 400 y 700.
- Títulos H1/H2 en 300, mayúsculas, interlineado 1.02–1.1. H1 máx. 5.75rem.
- Subtítulos de servicio y trabajo en 400; botones, navegación y etiquetas en 700.
- Etiquetas de datos (Teléfono, Hoy…) en 0.78rem, mayúsculas, tracking 0.1em.

## Componentes
- **Botón:** 52px de alto, 1px de borde, sin radio. Primario azul; sobre negro, contorno blanco.
- **Enlace con flecha:** texto 700 subrayado por borde, flecha SVG que avanza 4px al hover.
- **Servicios:** lista con reglas a la izquierda y vista previa fija a la derecha que cambia con la fila activa (hover o foco). En móvil cada fila muestra su foto.
- **Proceso:** números ligeros grandes (contador CSS) con reglas oscuras.
- **Filtros:** pestañas de texto con subrayado de 3px.

## Movimiento
- Momento principal: al cargar, cada línea del título se descubre de izquierda a derecha como cinta de enmascarar que se despega (`clip-path`), con un filo blanco de 2px que viaja en el corte y desaparece al final. La foto del hero se asienta (escala 1.06 → 1) y después suben el texto y los botones.
- Reseñas: carrusel automático (7 s por reseña) con barra de progreso, contador y botón Pausar; se detiene al pasar el cursor o enfocarlo. Sin flechas.
- Cruce de opacidad en la vista previa de servicios.
- `prefers-reduced-motion`: sin animaciones de entrada (el título aparece completo) y el carrusel cambia de reseña sin deslizar.
