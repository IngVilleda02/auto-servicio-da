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
- **Portafolio de un servicio:** cada servicio muestra un trabajo real: `portafolio` (`vehiculo`, `trabajo`) y sus fotos en `galeria`, en el orden en que se verán. En escritorio aparece en el panel derecho al llegar a la etapa (foto grande, flechas, miniaturas y visor); en celular, como fila deslizable dentro de la etapa.
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

## Antes de lanzar: revisión legal (pendientes del cliente)

Revisión hecha el 12 de noviembre de 2026. No sustituye la opinión de un abogado; los puntos 1 a 5 conviene cerrarlos antes de abrir el sitio a Google.

1. **Responsable del aviso de privacidad:** nombre de la persona física o razón social dueña del taller. Ponlo en `negocio.responsableLegal` y ejecuta `py build.py`. Hoy el aviso solo dice el nombre comercial.
2. **Logotipo de Qualitas:** es una marca registrada. Usarlo requiere autorización por escrito de Qualitas (o del convenio). Si no la hay, vacía `qualitas.logo` y deja solo el texto.
3. **Convenio con Qualitas:** el sitio dice que trabajan "de la mano con Qualitas". Debe existir el convenio; si no, cambia el texto (Ley Federal de Protección al Consumidor: publicidad veraz).
4. **Foto de la portada (hero):** confirmar que el taller tiene derecho a usarla (es de `Imagenes/Img3`, de origen desconocido). Si es de un banco de imágenes, guardar la licencia; si no, reemplazarla por una foto propia.
5. **Fotos de clientes:** las placas ya están difuminadas en todas las fotos donde se leían (`tools` no lo hace solo: si regeneras una foto desde `Galeria`, vuelve a difuminarla). Conviene tener el permiso del dueño de cada vehículo; el aviso ofrece retirar una foto si alguien lo pide.
6. **Reseñas de Google:** se muestran con nombre e inicial del apellido. Para mostrar el nombre completo, pide permiso a los autores y pon `resenasNombreCompleto` en `true`.
7. **Plan de Vercel:** el plan Hobby es solo para uso no comercial; un sitio de negocio debe estar en Pro (riesgo de suspensión de la cuenta, no de demanda).
8. **Opcional (privacidad):** servir la tipografía Archivo desde el propio sitio en lugar de Google Fonts para no enviar la IP de los visitantes a Google.
9. Código postal del domicilio, si se quiere mostrar.

Ya resuelto en el sitio:
- Aviso de privacidad con los elementos del artículo 15 de la LFPDPPP (2025): responsable y domicilio, datos, finalidades, transferencias (aseguradora en siniestros), derechos ARCO con requisitos y plazos, revocación, conservación, cookies de terceros y cambios.
- El formulario no guarda ni envía datos a un servidor; avisa qué pasa al enviarlo y enlaza el aviso.
- Sin cookies propias ni analítica; el mapa de Google se carga solo si el visitante lo pide.
- Sin datos estructurados de reseñas (Google no permite marcar reseñas propias).
- Accesibilidad: un solo H1, navegación con teclado, textos alternativos, contraste revisado con Impeccable, animaciones con alternativa para "reducir movimiento" y carrusel con pausa.
- No se usan logotipos de Apple ni de WhatsApp; solo se menciona WhatsApp como medio de contacto.

## Salir en Google (sin dominio propio)

Está preparado pero **apagado**. En `data/config.json`, `negocio.publicado` está en `false`: el sitio lleva `noindex` y `robots.txt` bloquea todo.

Para abrirlo a Google:
1. Pon `negocio.publicado` en `true` y ejecuta `py build.py`. Se quita `noindex` de la página principal, `robots.txt` la permite, se crea `sitemap.xml` y quedan activos canonical, `og:url` y `og:image`. El aviso de privacidad sigue sin indexarse.
2. `git add -A`, `git commit`, `git push`.
3. En Google Search Console agrega la propiedad `https://auto-servicio-da.vercel.app`, envía `sitemap.xml` y pide indexar la página principal.
4. En el Perfil de Empresa de Google (el de Maps) enlaza este sitio.

Con dominio propio: cambia `negocio.dominio`, repite los pasos 1 a 3 y agrega una redirección desde la dirección `.vercel.app`.

Antes de abrirlo: el plan Hobby de Vercel es solo para uso personal no comercial; un sitio de negocio debería estar en el plan Pro. Los datos estructurados ya llevan nombre, domicilio, teléfono, horario y mapa del taller.
