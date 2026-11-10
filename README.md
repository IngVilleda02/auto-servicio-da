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
- **Agregar una foto a la galería de un servicio** (el portafolio vive en "Lo que hacemos en el taller"):
  1. Prepárala (crea las versiones de 480, 800 y 1200 px en `img/`):
     `powershell -ExecutionPolicy Bypass -File tools\nueva-foto.ps1 -Origen "C:\ruta\foto.jpg" -Nombre "pintura-puerta-azul"`
  2. En `data/config.json`, dentro del servicio, agrega a `galeria`: `{ "nombre": "pintura-puerta-azul", "alt": "Descripción de lo que se ve", "pie": "Texto opcional bajo la foto" }`.
  3. Ejecuta `py build.py`. Las miniaturas, el contador "Ver galería · n fotos" y el visor se actualizan solos.
- **Recorrido de servicios:** el orden de `servicios` en `data/config.json` es el orden del recorrido (después de la etapa fija de Cotización, que se edita en `recorrido.cotizacion`). En escritorio, cada etapa cambia el panel de imagen al pasar por el centro de la pantalla.
- **Portada de un servicio:** son las primeras fotos de su `galeria`; `"portada": 2` muestra dos (como en Taller mecánico). `"foco": "50% 60%"` ajusta el encuadre de una foto recortada.
- **Horario:** `horarios` (formato 24 h; domingo vacío = cerrado). El estado “Abierto ahora” usa `zonaHoraria`.
- **Dominio definitivo:** al llenar `negocio.dominio` se activan canonical, `url` en datos estructurados y se quita `noindex`. Después genera `sitemap.xml` y quita el `Disallow: /` de `robots.txt` (el build lo hace solo).

## Publicación

- Repositorio (privado): https://github.com/IngVilleda02/auto-servicio-da
- Vercel: proyecto `auto-servicio-da` del equipo IngVilleda. Producción: https://auto-servicio-da.vercel.app
- Cada `git push` a `main` despliega solo en producción. Flujo para un cambio:
  1. Edita `data/config.json` (o CSS/JS) y ejecuta `py build.py`.
  2. `git add -A`, `git commit -m "..."` y `git push`.
- `index.html` y `privacidad.html` se guardan ya generados en el repositorio: Vercel no ejecuta `build.py`.
- `.vercelignore` evita publicar `build.py`, `data/`, `README.md` y `DESIGN.md`.
- Las imágenes se cachean un día porque sus nombres no llevan versión. Si quieres caché larga, cambia el nombre del archivo cada vez que reemplaces una foto.

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
11. Confirmar origen y licencia de `Img1` a `Img5` e `img7`. Se muestran como **imágenes ilustrativas** (`"ilustrativa": true` en `config.json`); si alguna es un trabajo real del taller, quita esa marca.
12. Datos de contacto (tarjeta del taller): WhatsApp 427 202 5184, llamadas 427 101 7856, correo autoserviciodya@hotmail.com; domicilio Av. 4 Oriente N° 14, Camino a Santa Cruz Nieto, San Juan del Río, Qro. Falta el código postal si se quiere mostrar.
13. Autorización para usar el logotipo de Qualitas.

## Salir en Google (sin dominio propio)

Está preparado pero **apagado**. En `data/config.json`, `negocio.publicado` está en `false`: el sitio lleva `noindex` y `robots.txt` bloquea todo.

Para abrirlo a Google:
1. Pon `negocio.publicado` en `true` y ejecuta `py build.py`. Se quita `noindex` de la página principal, `robots.txt` la permite, se crea `sitemap.xml` y quedan activos canonical, `og:url` y `og:image`. El aviso de privacidad sigue sin indexarse.
2. `git add -A`, `git commit`, `git push`.
3. En Google Search Console agrega la propiedad `https://auto-servicio-da.vercel.app`, envía `sitemap.xml` y pide indexar la página principal.
4. En el Perfil de Empresa de Google (el de Maps) enlaza este sitio.

Con dominio propio: cambia `negocio.dominio`, repite los pasos 1 a 3 y agrega una redirección desde la dirección `.vercel.app`.

Antes de abrirlo: el plan Hobby de Vercel es solo para uso personal no comercial; un sitio de negocio debería estar en el plan Pro. Los datos estructurados ya llevan nombre, domicilio, teléfono, horario y mapa del taller.
