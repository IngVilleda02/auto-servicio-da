#!/usr/bin/env python3
"""Genera el sitio estático de Auto Servicio D&A a partir de data/config.json.

Uso:   py build.py
Salida:
  index.html, privacidad.html, robots.txt   -> versión de sitio (CSS y JS en archivos externos, con CSP estricta)
  artifact/index.html, artifact/privacidad.html -> versión con CSS y JS integrados, para publicar como artefacto
"""
import json
import re
from html import escape as esc
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CFG = json.loads((ROOT / "data" / "config.json").read_text(encoding="utf-8"))
N, M, P = CFG["negocio"], CFG["mapa"], CFG["portada"]
YEAR = 2026

IMG_DIR = ROOT / "img"


def variants(name):
    out = []
    for p in IMG_DIR.glob(f"{name}-*.jpg"):
        m = re.match(rf"{re.escape(name)}-(\d+)\.jpg$", p.name)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def jpeg_size(path):
    """Ancho y alto de un JPEG leyendo su marcador SOF (sin dependencias)."""
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h = int.from_bytes(data[i + 5:i + 7], "big")
            w = int.from_bytes(data[i + 7:i + 9], "big")
            return w, h
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    raise ValueError(f"No se pudo leer el tamaño de {path}")


def check_image(name):
    if not variants(name):
        raise SystemExit(f"Falta la imagen '{name}' en img/. Prepárala con tools\\nueva-foto.ps1.")


def pic(name, sizes, alt, cls="", eager=False, style=""):
    check_image(name)
    vs = variants(name)
    srcset = ", ".join(f"img/{name}-{v}.jpg {v}w" for v in vs)
    mid = min(vs, key=lambda v: abs(v - 800))
    w, h = jpeg_size(IMG_DIR / f"{name}-{mid}.jpg")
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    st = f' data-foco="{esc(style)}"' if style else ""
    return (f'<img{c}{st} src="img/{name}-{mid}.jpg" srcset="{srcset}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" {load}>')


def srcset_of(name):
    return ", ".join(f"img/{name}-{v}.jpg {v}w" for v in variants(name))


def largest(name):
    return f"img/{name}-{max(variants(name))}.jpg"

WA_LINK = f"https://wa.me/{N['whatsappNumero']}"
MAP_OPEN = M["enlaceGoogleMaps"]
MAP_DIR = f"https://www.google.com/maps/dir/?api=1&destination={M['lat']},{M['lng']}"
MAP_EMBED = f"https://www.google.com/maps?q={M['lat']},{M['lng']}&z=17&output=embed"
TEL = N["telefonoTel"]


def hours_rows(prefix=""):
    rows = []
    for d in CFG["horarios"]:
        val = "Cerrado" if not d["abre"] else f"{fmt(d['abre'])} a {fmt(d['cierra'])}"
        rows.append(f'<tr data-day="{esc(d["dia"])}"><th scope="row">{esc(d["dia"])}</th><td>{val}</td></tr>')
    return "\n".join(rows)


def fmt(hhmm):
    h, m = map(int, hhmm.split(":"))
    suf = "a. m." if h < 12 else "p. m."
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {suf}" if m else f"{h12} {suf}"


def jsonld():
    dias = {"Lunes": "Monday", "Martes": "Tuesday", "Miércoles": "Wednesday", "Jueves": "Thursday",
            "Viernes": "Friday", "Sábado": "Saturday", "Domingo": "Sunday"}
    spec = [{"@type": "OpeningHoursSpecification", "dayOfWeek": dias[d["dia"]],
             "opens": d["abre"], "closes": d["cierra"]} for d in CFG["horarios"] if d["abre"]]
    data = {
        "@context": "https://schema.org",
        "@type": "AutoBodyShop",
        "name": N["nombre"],
        "description": N["descripcionCorta"],
        "telephone": TEL,
        "address": {"@type": "PostalAddress", "streetAddress": "Av. 4 Ote. N° 97, La Loma",
                    "addressLocality": "San Juan del Río", "addressRegion": "Querétaro",
                    "postalCode": "76804", "addressCountry": "MX"},
        "geo": {"@type": "GeoCoordinates", "latitude": M["lat"], "longitude": M["lng"]},
        "hasMap": MAP_OPEN,
        "openingHoursSpecification": spec,
        "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["titulo"]}}
                       for s in CFG["servicios"]],
    }
    if N["dominio"]:
        data["url"] = N["dominio"]
    if N["correo"]:
        data["email"] = N["correo"]
    return json.dumps(data, ensure_ascii=False)


NAV = [("Servicios y cómo trabajamos", "#servicios"),
       ("Contacto", "#contacto")]

LOGO = f'<img src="img/logo-da.png" width="320" height="170" alt="{esc(N["nombre"])}">'


def header(home):
    base = "" if home else "index.html"
    links = "\n".join(f'<a href="{base}{h}">{esc(t)}</a>' for t, h in NAV)
    return f'''<a class="skip-link" href="#contenido">Saltar al contenido</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{base or 'index.html'}#inicio" aria-label="{esc(N['nombre'])}, inicio">{LOGO}</a>
    <button class="btn btn--sm menu-toggle js-only" id="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menú</button>
    <nav class="nav" id="site-nav" aria-label="Principal">
      {links}
      <a class="btn btn--primary btn--sm" href="{base}#contacto">Solicitar cotización</a>
    </nav>
  </div>
</header>'''


def footer(home):
    base = "" if home else "index.html"
    nav = "\n".join(f'<a href="{base}{h}">{esc(t)}</a>' for t, h in NAV)
    email = f'<p><a href="mailto:{esc(N["correo"])}">{esc(N["correo"])}</a></p>' if N["correo"] else ""
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="footer__grid">
      <div class="footer__brand">
        <a class="brand brand--plate" href="{base or 'index.html'}#inicio" aria-label="{esc(N['nombre'])}, inicio">{LOGO}</a>
        <p>{esc(N['descripcionCorta'])}</p>
      </div>
      <div class="footer__col">
        <h2>Navegación</h2>
        {nav}
      </div>
      <div class="footer__col footer__col--wide">
        <h2>Contacto</h2>
        <p>{esc(N['direccion'])}</p>
        <p>Teléfono: <a href="tel:{TEL}">{esc(N['telefonoMostrar'])}</a></p>
        <p>WhatsApp: <a href="{WA_LINK}" target="_blank" rel="noopener">{esc(N['whatsappMostrar'])}</a></p>
        {email}
      </div>
      <div class="footer__col footer__col--wide">
        <h2>Horario</h2>
        <table><tbody>
        {hours_rows()}
        </tbody></table>
      </div>
    </div>
    <div class="footer__legal">
      <span>© {YEAR} {esc(N['nombre'])}. Todos los derechos reservados.</span>
      <a href="privacidad.html">Aviso de privacidad</a>
      <span class="footer__credit">Desarrollado por MIRAI NEXUS</span>
    </div>
  </div>
</footer>'''


ARROW = '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M1 7h11M7.5 2.5 12 7l-4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
GRID_ICON = '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M1 1h5v5H1zM8 1h5v5H8zM1 8h5v5H1zM8 8h5v5H8z" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>'


def fotos_word(n):
    return "1 foto" if n == 1 else f"{n} fotos"


def thumbs_html(sv):
    fotos = sv["galeria"]
    out = []
    for j, f in enumerate(fotos[:4]):
        check_image(f["nombre"])
        small = variants(f["nombre"])[0]
        w, h = jpeg_size(IMG_DIR / f"{f['nombre']}-{small}.jpg")
        extra = len(fotos) - 4 if (j == 3 and len(fotos) > 4) else 0
        more = f'<span class="thumb__more" aria-hidden="true">+{extra}</span>' if extra else ""
        label = f"Ver foto {j + 1} de {len(fotos)} de {sv['titulo']}"
        foco = f' data-foco="{esc(f["foco"])}"' if f.get("foco") else ""
        out.append(f'<a class="thumb" href="{largest(f["nombre"])}" data-gal="{esc(sv["id"])}" data-index="{j}" aria-label="{esc(label)}">'
                   f'<img{foco} src="img/{f["nombre"]}-{small}.jpg" width="{w}" height="{h}" alt="" loading="lazy" decoding="async">{more}</a>')
    return "".join(out)


def services_html():
    rows, previews = [], []
    for i, sv in enumerate(CFG["servicios"]):
        fotos = sv["galeria"]
        cover = fotos[:max(1, int(sv.get("portada", 1)))]
        multi = len(cover) > 1
        act = " is-active" if i == 0 else ""
        mobile = "".join(pic(f["nombre"], "50vw" if multi else "100vw", f["alt"], "svc__img", style=f.get("foco", ""))
                         for f in cover)
        rows.append(f"""<li class="svc{act}" data-svc="{esc(sv['id'])}">
  <h3>{esc(sv['titulo'])}</h3>
  <p>{esc(sv['descripcion'])}</p>
  <p class="svc__use"><strong>Aplicación:</strong> {esc(sv['aplicacion'])}</p>
  <div class="svc__imgs{' svc__imgs--2' if multi else ''}">{mobile}</div>
  <div class="svc__gallery">
    <div class="thumbs">{thumbs_html(sv)}</div>
  </div>
  <div class="svc__actions">
    <a class="link-arrow" href="{largest(fotos[0]['nombre'])}" data-gal="{esc(sv['id'])}" data-index="0">Ver galería · {fotos_word(len(fotos))} {GRID_ICON}</a>
    <a class="link-arrow" href="#contacto" data-service="{esc(sv['titulo'])}">Cotizar este servicio {ARROW}</a>
  </div>
</li>""")
        shots = []
        for f in cover:
            foco = f' data-foco="{esc(f["foco"])}"' if f.get("foco") else ""
            mid = min(variants(f["nombre"]), key=lambda v: abs(v - 800))
            load = 'decoding="async"' if i == 0 else 'loading="lazy" decoding="async"'
            shots.append(f'<img{foco} src="img/{f["nombre"]}-{mid}.jpg" srcset="{srcset_of(f["nombre"])}" '
                         f'sizes="{"280px" if multi else "560px"}" alt="" {load}>')
        previews.append(f'<div class="svc-shot{act}{" svc-shot--2" if multi else ""}" data-for="{esc(sv["id"])}">{"".join(shots)}</div>')
    return ('<div class="svc-wrap"><ul class="svc-list">' + "\n".join(rows) + '</ul>'
            '<div class="svc-preview" aria-hidden="true">' + "".join(previews) + '</div></div>')


def gallery_json():
    data = {}
    for sv in CFG["servicios"]:
        fotos = []
        for f in sv["galeria"]:
            big = max(variants(f["nombre"]))
            w, h = jpeg_size(IMG_DIR / f"{f['nombre']}-{big}.jpg")
            fotos.append({"src": f"img/{f['nombre']}-{big}.jpg", "srcset": srcset_of(f["nombre"]),
                          "alt": f["alt"], "pie": f.get("pie", ""), "w": w, "h": h})
        data[sv["id"]] = {"titulo": sv["titulo"], "fotos": fotos}
    # </ dentro de JSON no debe cerrar la etiqueta script
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def title_lines(name):
    """Divide el nombre en dos líneas (primera palabra / resto) para la animación de entrada."""
    first, _, rest = name.partition(" ")
    lines = [first, rest] if rest else [first]
    return " ".join(f'<span class="title-line"><span class="title-ink">{esc(t)}</span></span>' for t in lines)


def steps(items):
    return "\n".join(f"<li><span>{esc(t)}</span></li>" for t in items)


STAR = "9,1 11.4,6.6 17.5,7.2 12.9,11.2 14.3,17 9,13.9 3.7,17 5.1,11.2 0.5,7.2 6.6,6.6"


def stars():
    polys = "".join(f'<polygon transform="translate({i * 19} 0)" points="{STAR}"/>' for i in range(5))
    return f'<svg class="stars" viewBox="0 0 94 18" role="img" aria-label="5 de 5 estrellas" fill="currentColor">{polys}</svg>'


def reviews_html():
    total = len(CFG["resenas"])
    slides = "\n".join(f"""<figure class="review" role="group" aria-roledescription="opinión" aria-label="{i + 1} de {total}">
  {stars()}
  <blockquote><p>{esc(r['texto'])}</p></blockquote>
  <figcaption>{esc(r['autor'])}</figcaption>
</figure>""" for i, r in enumerate(CFG["resenas"]))
    prev = '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M13 7H2M6.5 2.5 2 7l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
    return f"""<div class="carousel" id="reviews-carousel" role="region" aria-roledescription="carrusel" aria-label="Opiniones de clientes">
  <div class="carousel__viewport">
    <div class="carousel__track" id="reviews-track" aria-live="off">
{slides}
    </div>
  </div>
  <div class="carousel__controls js-only">
    <span class="carousel__count" aria-hidden="true"><span data-carousel-current>1</span> / {total}</span>
    <button class="carousel__toggle" type="button" data-carousel-toggle>Pausar</button>
    <span class="carousel__progress" aria-hidden="true"><span data-carousel-bar></span></span>
  </div>
</div>"""


def service_options():
    opts = ['<option value="">Elige un servicio</option>']
    for s in CFG["servicios"]:
        opts.append(f'<option value="{esc(s["titulo"])}">{esc(s["titulo"])}</option>')
    opts.append('<option value="Reparación con seguro Qualitas">Reparación con seguro Qualitas</option>')
    opts.append('<option value="Aún no lo sé">Aún no lo sé</option>')
    return "\n".join(opts)


def home_body():
    email_dt = (f'<div><dt>Correo</dt><dd><a href="mailto:{esc(N["correo"])}">{esc(N["correo"])}</a></dd></div>'
                if N["correo"] else "")
    hours_json = json.dumps({"tz": N["zonaHoraria"], "days": CFG["horarios"]}, ensure_ascii=False)
    return f'''
{header(True)}
<main id="contenido">
<section class="hero" id="inicio" aria-labelledby="h1">
  <picture class="hero__img">
    <source media="(max-width: 719px)" srcset="{srcset_of(P['alta'])}" sizes="100vw">
    <img src="img/{P['ancha']}-1200.jpg" srcset="{srcset_of(P['ancha'])}" sizes="100vw"
         width="{P['anchaDims'][0]}" height="{P['anchaDims'][1]}" alt="{esc(P['alt'])}" fetchpriority="high">
  </picture>
  <div class="wrap hero__inner">
    <h1 id="h1" class="hero__title">{title_lines(N['nombre'])}</h1>
    <p class="hero__lead">Hojalatería y pintura de alta calidad. La diferencia está en cada detalle. Restauramos la estética de tu auto con precisión, acabados impecables y atención personalizada.</p>
    <div class="hero__ctas">
      <a class="btn btn--primary" href="#contacto">Solicitar cotización</a>
      <a class="btn btn--light" href="#servicios">Trabajos</a>
    </div>
  </div>
</section>

<section class="facts-bar" aria-label="Datos del taller">
  <dl class="wrap">
    <div class="fact"><dt>Dónde</dt><dd>{esc(N['ciudad'])}</dd></div>
    <div class="fact"><dt>WhatsApp</dt><dd><a href="{WA_LINK}" target="_blank" rel="noopener">{esc(N['whatsappMostrar'])}</a></dd></div>
    <div class="fact"><dt>Teléfono</dt><dd><a href="tel:{TEL}">{esc(N['telefonoMostrar'])}</a></dd></div>
    <div class="fact"><dt>Hoy</dt><dd><span class="status" data-open-status data-open=""></span> <span data-today-hours></span></dd></div>
  </dl>
</section>

<section class="section" id="servicios" aria-labelledby="h-servicios">
  <div class="wrap">
    <div class="section__head">
      <h2 id="h-servicios">Lo que hacemos en el taller</h2>
      <p class="lead">Cada servicio incluye seguimiento personal de tu vehículo. Abre su galería para ver trabajos realizados.</p>
    </div>
{services_html()}
  </div>
</section>

<section class="section section--dark on-dark" id="como-trabajamos" aria-labelledby="h-proceso">
  <div class="wrap">
    <div class="qualitas">
      <h2 id="h-proceso">{esc(CFG['qualitas']['titulo'])}</h2>
      <p>{esc(CFG['qualitas']['texto'])}</p>
    </div>
    <div class="process">
      <div class="process__col">
        <h3>Reparación particular</h3>
        <ol class="steps">
{steps(CFG['procesoParticular'])}
        </ol>
      </div>
      <div class="process__col">
        <h3>Reparación con seguro Qualitas</h3>
        <ol class="steps">
{steps(CFG['procesoQualitas'])}
        </ol>
      </div>
    </div>
    <p class="process__note">La cotización se entrega después de revisar tu vehículo. Esta página no calcula precios ni tiempos.</p>
  </div>
</section>

<dialog class="lightbox" id="lightbox" aria-labelledby="lb-title">
  <div class="lightbox__head">
    <div>
      <h3 id="lb-title" data-lb-title></h3>
      <p class="lightbox__count" data-lb-count aria-live="polite"></p>
    </div>
    <button class="lightbox__close" type="button" data-lb-close aria-label="Cerrar galería"><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2 2l10 10M12 2 2 12" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
  </div>
  <figure class="lightbox__figure">
    <img data-lb-img alt="" width="1200" height="800">
    <figcaption data-lb-pie></figcaption>
  </figure>
  <div class="lightbox__nav">
    <button class="carousel__btn carousel__btn--light" type="button" data-lb-prev aria-label="Foto anterior"><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M13 7H2M6.5 2.5 2 7l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
    <div class="lightbox__strip" data-lb-strip></div>
    <button class="carousel__btn carousel__btn--light" type="button" data-lb-next aria-label="Foto siguiente">{ARROW}</button>
  </div>
</dialog>

<section class="section section--alt" id="resenas" aria-labelledby="h-resenas">
  <div class="wrap reviews">
    <div class="reviews__head">
      <h2 id="h-resenas">Lo que dicen nuestros clientes</h2>
      <p class="reviews__src">Reseñas publicadas en Google Maps, transcritas tal como aparecen.</p>
    </div>
{reviews_html()}
  </div>
</section>

<section class="section" id="contacto" aria-labelledby="h-contacto">
  <div class="wrap contact">
    <div class="contact__info">
      <h2 id="h-contacto">Solicita tu cotización</h2>
      <p class="lead">Cuéntanos qué necesita tu vehículo. Preparamos tu mensaje y lo envías desde WhatsApp.</p>
      <dl class="info-list">
        <div><dt>Teléfono</dt><dd><a href="tel:{TEL}">{esc(N['telefonoMostrar'])}</a></dd></div>
        <div><dt>WhatsApp</dt><dd><a href="{WA_LINK}" target="_blank" rel="noopener">{esc(N['whatsappMostrar'])}</a></dd></div>
        {email_dt}
        <div><dt>Dirección</dt><dd>{esc(N['direccion'])}</dd></div>
      </dl>
      <div>
        <p class="status" data-open-status data-open="" role="status"></p>
        <table class="hours" aria-label="Horario de atención"><tbody>
{hours_rows()}
        </tbody></table>
        <p class="form__alt hours-note">Horario del centro de México.</p>
      </div>
    </div>
    <div class="contact__form">
      <noscript><div class="noscript-box"><h3>Contáctanos directamente</h3>
        <p>El formulario necesita JavaScript. Escríbenos por <a href="{WA_LINK}">WhatsApp ({esc(N['whatsappMostrar'])})</a> o llama al <a href="tel:{TEL}">{esc(N['telefonoMostrar'])}</a>.</p></div></noscript>
      <form class="form js-only" id="quote-form" method="post" action="#contacto" novalidate data-wa="{N['whatsappNumero']}">
        <h3>Preparar solicitud</h3>
        <p class="form__alt">Los campos con * son obligatorios.</p>
        <div class="field">
          <label for="nombre">Nombre *</label>
          <input id="nombre" name="nombre" type="text" autocomplete="name" maxlength="80" aria-describedby="nombre-err">
          <p class="err" id="nombre-err" hidden></p>
        </div>
        <fieldset class="field radios-wrap">
          <legend>Medio de contacto preferido *</legend>
          <div class="radios">
            <label><input type="radio" name="medio" value="whatsapp" checked> WhatsApp</label>
            <label><input type="radio" name="medio" value="llamada"> Llamada</label>
          </div>
        </fieldset>
        <div class="field" id="row-telefono">
          <label for="telefono">Teléfono *</label>
          <input id="telefono" name="telefono" type="tel" inputmode="tel" autocomplete="tel" maxlength="20" aria-describedby="telefono-hint telefono-err">
          <p class="hint" id="telefono-hint">10 dígitos. Puedes escribirlo con espacios o guiones.</p>
          <p class="err" id="telefono-err" hidden></p>
        </div>
        <div class="field">
          <label for="servicio">Servicio de interés *</label>
          <select id="servicio" name="servicio" aria-describedby="servicio-err">
{service_options()}
          </select>
          <p class="err" id="servicio-err" hidden></p>
        </div>
        <div class="field">
          <label for="vehiculo">Vehículo <span class="opt">(opcional)</span></label>
          <input id="vehiculo" name="vehiculo" type="text" maxlength="80" aria-describedby="vehiculo-hint">
          <p class="hint" id="vehiculo-hint">Marca, modelo y año, si los conoces.</p>
        </div>
        <div class="field">
          <label for="descripcion">Descripción del requerimiento *</label>
          <textarea id="descripcion" name="descripcion" maxlength="600" aria-describedby="descripcion-hint descripcion-err"></textarea>
          <p class="hint" id="descripcion-hint">Máximo 600 caracteres. Las fotos se adjuntan manualmente dentro de la conversación de WhatsApp.</p>
          <p class="err" id="descripcion-err" hidden></p>
        </div>
        <p class="form__privacy">Usamos estos datos solo para armar tu mensaje en este navegador. Consulta el <a href="privacidad.html">aviso de privacidad</a>.</p>
        <button class="btn btn--primary" type="submit">Preparar solicitud por WhatsApp</button>
        <p id="form-status" role="alert" class="err"></p>
        <div class="prepared" id="prepared" hidden>
          <p id="prepared-title" tabindex="-1">Tu solicitud está preparada. Continúa en WhatsApp y pulsa Enviar.</p>
          <label for="prepared-text" class="form__alt">Mensaje preparado (puedes editarlo en WhatsApp):</label>
          <textarea id="prepared-text" readonly></textarea>
          <div class="prepared__actions">
            <a class="btn btn--primary" id="prepared-link" href="{WA_LINK}" target="_blank" rel="noopener">Continuar en WhatsApp</a>
            <button class="btn" type="button" id="prepared-copy">Copiar mensaje</button>
          </div>
          <p class="form__alt">Abrir WhatsApp no envía el mensaje: la solicitud llega hasta que pulses Enviar. Si necesitas mandar fotos, adjúntalas ahí.</p>
        </div>
      </form>
    </div>
  </div>
</section>

<section class="section section--alt" id="ubicacion" aria-labelledby="h-ubicacion">
  <div class="wrap">
    <div class="location">
      <div class="location__info">
        <h2 id="h-ubicacion">Cómo llegar</h2>
        <address><strong>{esc(N['nombre'])}</strong><br>{esc(N['direccion'])}</address>
        <p>{esc(M['instruccionesLlegada'])}</p>
        <div class="location__actions">
          <a class="btn btn--primary" href="{MAP_OPEN}" target="_blank" rel="noopener">Abrir en Google Maps</a>
          <a class="btn" href="{MAP_DIR}" target="_blank" rel="noopener">Cómo llegar</a>
        </div>
      </div>
      <div class="map" id="map" data-embed="{MAP_EMBED}" data-title="Ubicación de {esc(N['nombre'])}">
        <div class="map__ph">
          <p>El mapa de Google se carga solo si lo pides, para no compartir datos de tu visita antes.</p>
          <button class="btn js-only" type="button" id="load-map">Cargar mapa</button>
          <a class="btn" href="{MAP_OPEN}" target="_blank" rel="noopener">Ver en Google Maps</a>
        </div>
      </div>
    </div>
  </div>
</section>
</main>
{footer(True)}
<script type="application/json" id="hours-data">{hours_json}</script>
<script type="application/json" id="gallery-data">{gallery_json()}</script>
<script type="application/ld+json">{jsonld()}</script>
'''


def privacy_body():
    cont = f'WhatsApp <a href="{WA_LINK}" target="_blank" rel="noopener">{esc(N["whatsappMostrar"])}</a> o teléfono <a href="tel:{TEL}">{esc(N["telefonoMostrar"])}</a>'
    return f'''
{header(False)}
<main id="contenido" class="wrap legal">
  <h1>Aviso de privacidad</h1>
  <p>Última actualización: {esc(N['fechaPrivacidad'])}.</p>
  <section><h2>Responsable</h2>
    <p>{esc(N['responsable'])}, con domicilio en {esc(N['direccion'])}. Contacto: {cont}.</p></section>
  <section><h2>Qué datos se capturan en este sitio</h2>
    <p>El formulario de cotización pide nombre, medio de contacto preferido (WhatsApp o llamada), teléfono, servicio de interés, vehículo (opcional) y la descripción de lo que necesitas. Esta página no envía esos datos a un servidor propio ni los guarda: se usan en tu navegador para armar un mensaje de WhatsApp.</p></section>
  <section><h2>Para qué se usan</h2>
    <ul><li>Preparar el mensaje con el que solicitas una cotización.</li><li>Si decides enviarlo por WhatsApp, el taller lo recibe y lo usa para responderte y cotizar el servicio.</li></ul></section>
  <section><h2>Con quién se comparten</h2>
    <p>El mensaje viaja por WhatsApp solo cuando pulsas Enviar, y queda sujeto a los términos y al aviso de privacidad de esa plataforma. Si cargas el mapa, Google recibe tu visita a ese contenido. Las tipografías se cargan desde Google Fonts.</p></section>
  <section><h2>Cookies y analítica</h2>
    <p>Este sitio no usa cookies propias ni herramientas de analítica.</p></section>
  <section><h2>Tus derechos</h2>
    <p>Puedes solicitar el acceso, rectificación o cancelación de tus datos, u oponerte a su uso, escribiendo a los medios de contacto indicados arriba.</p></section>
  <section><h2>Cambios a este aviso</h2>
    <p>Cualquier cambio se publicará en esta misma página con su fecha de actualización.</p></section>
</main>
{footer(False)}
'''


FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@300;400;700&display=swap">'

CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; script-src 'self'; frame-src https://www.google.com; "
       "connect-src 'none'; form-action 'none'; base-uri 'self'; object-src 'none'")


def page(title, desc, body, inline, home):
    robots = "" if N["dominio"] else '<meta name="robots" content="noindex, nofollow">'
    canon = f'<link rel="canonical" href="{esc(N["dominio"])}{"" if home else "/privacidad.html"}">' if N["dominio"] else ""
    css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
    js = (ROOT / "js" / "app.js").read_text(encoding="utf-8")
    if inline:
        head_css = f"<style>{css}</style>"
        tail_js = f"<script>{js}</script>"
        csp = ""
        meta_top = ""
        css_pad = ""
    else:
        head_css = '<link rel="stylesheet" href="css/styles.css">'
        tail_js = '<script src="js/app.js" defer></script>'
        csp = f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'
        meta_top = ""
        css_pad = ""
    head = f'''<title>{esc(title)}</title>
{meta_top}
{csp}
<meta name="description" content="{esc(desc)}">
{robots}{canon}
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="img/favicon-32.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta property="og:type" content="website"><meta property="og:locale" content="es_MX">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
{FONTS}
{head_css}{css_pad}'''
    if inline:
        # El artefacto se envuelve con doctype/head; la página de privacidad se publica tal cual.
        pre = "" if home else '<!doctype html><html lang="es-MX"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        post_head = "" if home else "</head><body>"
        end = "" if home else "</body></html>"
        return f"{pre}{head}{post_head}{body}{tail_js}{end}"
    return f'''<!doctype html>
<html lang="es-MX">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{head}
</head>
<body>
{body}
{tail_js}
</body>
</html>
'''


def main():
    desc_home = (f"{N['nombre']} en {N['ciudad']}: hojalatería y pintura, taller mecánico, alineación y balanceo, "
                 "y refacciones a tu medida. Solicita tu cotización por WhatsApp.")
    titles = (f"{N['nombre']} | Hojalatería y pintura en San Juan del Río", f"Aviso de privacidad | {N['nombre']}")
    (ROOT / "index.html").write_text(page(titles[0], desc_home, home_body(), False, True), encoding="utf-8")
    (ROOT / "privacidad.html").write_text(page(titles[1], f"Aviso de privacidad de {N['nombre']}.", privacy_body(), False, False), encoding="utf-8")
    art = ROOT / "artifact"
    art.mkdir(exist_ok=True)
    (art / "index.html").write_text(page(N["nombre"], desc_home, home_body(), True, True), encoding="utf-8")
    (art / "privacidad.html").write_text(page(titles[1], f"Aviso de privacidad de {N['nombre']}.", privacy_body(), True, False), encoding="utf-8")
    robots = "User-agent: *\nDisallow: /\n" if not N["dominio"] else f"User-agent: *\nAllow: /\nSitemap: {N['dominio']}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")
    print("OK: index.html, privacidad.html, robots.txt, artifact/")


if __name__ == "__main__":
    main()
