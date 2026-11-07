# Auto Servicio D&A — sitio web (versión de revisión)

Sitio estático, sin Node. Se genera con Python desde un solo archivo de datos.

## Estructura

| Ruta | Qué es |
|---|---|
| `data/config.json` | Todos los datos: negocio, horarios, servicios, trabajos, reseñas, procesos, FAQ, mapa |
| `build.py` | Generador. Ejecuta `py build.py` tras editar datos |
| `css/styles.css`, `js/app.js` | Estilos y comportamiento (menú, filtros, galería, FAQ, formulario, mapa) |
| `img/` | Imágenes en varios anchos (`nombre-480.jpg`, `-800`, `-1200`) |
| `index.html`, `privacidad.html`, `robots.txt` | Salida del sitio (se regeneran) |
| `artifact/` | Versión con CSS/JS integrados que se publicó como artefacto |
| `vercel.json` | Cabeceras de seguridad para cuando se despliegue |
| `DESIGN.md` | Sistema visual (tokens, tipografía, componentes, movimiento) |

## Cómo cambiar cosas

- **Datos y textos:** edita `data/config.json` y ejecuta `py build.py`. Un campo vacío (`""`) se omite sin dejar rastro (por ejemplo `correo`, `dominio`).
- **Agregar un trabajo:** copia la foto a una carpeta, genera variantes de 480, 800 y 1200 px de ancho como `img/<nombre>-480.jpg`, añade el objeto en `proyectos` (con `ancho` y `alto` originales) y ejecuta `py build.py`. Si añades un servicio con foto nueva, agrega sus dimensiones en `DIMS` dentro de `build.py`.
- **Horario:** `horarios` (formato 24 h; domingo vacío = cerrado). El estado “Abierto ahora” usa `zonaHoraria`.
- **Dominio definitivo:** al llenar `negocio.dominio` se activan canonical, `url` en datos estructurados y se quita `noindex`. Después genera `sitemap.xml` y quita el `Disallow: /` de `robots.txt` (el build lo hace solo).

## Variables de entorno

Ninguna. No hay servidor, claves ni APIs. El mapa usa el embed público de Google sin clave.

## Seguridad y privacidad

- El formulario no envía nada a un servidor: valida en el navegador, arma un mensaje y ofrece abrirlo en WhatsApp. No usa GET ni guarda datos (sin consola, almacenamiento local ni URLs).
- Sin JavaScript el formulario se oculta y se muestran WhatsApp y teléfono.
- La versión del sitio incluye CSP por `<meta>` (scripts y estilos solo propios; `frame-src` solo `https://www.google.com`). `vercel.json` añade cabeceras. Si despliegas en otro servidor, replica esas cabeceras. Prueba primero la CSP en `Content-Security-Policy-Report-Only`.
- No hay analítica. Si se añade después, registrar solo eventos (inicio de cotización, clic en WhatsApp, clic en cómo llegar), sin datos personales.

## Información pendiente del proveedor

1. Correo de contacto (hoy se omite).
2. Dominio definitivo (canonical, sitemap, imagen social, quitar `noindex`).
4. Logotipo o imagen de referencia de Qualitas con autorización de uso (hoy solo se menciona en texto).
5. Confirmar el texto “Refacciones a tu medida” (el original decía “a tu media”).
6. Validar los textos de “Situación / Servicio / Resultado” de los 4 trabajos: se redactaron solo con lo visible en cada foto. Agregar vehículo, fecha o cliente solo si hay permiso.
7. Fotografías propias de refacciones (hoy se reutiliza la de suspensión) y del equipo o fachada.
8. Confirmar que las reseñas de Google pueden mostrarse con nombre.
9. Revisión legal del aviso de privacidad.
10. Imagen social para Open Graph.
11. Confirmar el origen y permiso de uso de `Img1`, `Img2` e `Img3` (portada y Taller mecánico). No parecen tomadas en el taller; si son de un banco de imágenes, revisar su licencia.
