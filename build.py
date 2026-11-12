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
        "address": {"@type": "PostalAddress", "streetAddress": "Av. 4 Oriente N° 14, Camino a Santa Cruz Nieto",
                    "addressLocality": "San Juan del Río", "addressRegion": "Querétaro",
                    "addressCountry": "MX"},
        "geo": {"@type": "GeoCoordinates", "latitude": M["lat"], "longitude": M["lng"]},
        "hasMap": MAP_OPEN,
        "openingHoursSpecification": spec,
        "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["titulo"]}}
                       for s in CFG["servicios"]],
    }
    if N["dominio"]:
        data["url"] = N["dominio"]
        data["image"] = N["dominio"] + "/img/logo-dya-800.jpg"
    if N["correo"]:
        data["email"] = N["correo"]
    return json.dumps(data, ensure_ascii=False)


NAV = [("Servicios y cómo trabajamos", "#servicios"),
       ("Contacto", "#contacto")]

LOGO = f'<img src="img/logo-dya.png" width="640" height="327" alt="{esc(N["nombre"])}">'


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
    email = f'<p>Correo: <a href="mailto:{esc(N["correo"])}">{esc(N["correo"])}</a></p>' if N["correo"] else ""
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
        <p>WhatsApp: <a href="{WA_LINK}" target="_blank" rel="noopener">{esc(N['whatsappMostrar'])}</a></p>
        <p>Llamadas: <a href="tel:{TEL}">{esc(N['telefonoMostrar'])}</a></p>
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
      <span class="footer__credit">Desarrollado por Mirai Nexus</span>
    </div>
  </div>
</footer>'''


ARROW = '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M1 7h11M7.5 2.5 12 7l-4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'


def fotos_word(n):
    return "1 foto" if n == 1 else f"{n} fotos"


CHEV_L = '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M9 2 4 7l5 5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
CHEV_R = '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="m5 2 5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'


def near(name, target):
    return min(variants(name), key=lambda v: abs(v - target))


def folio_html(sv):
    """Portafolio de un trabajo real del taller para el panel fijo del recorrido (escritorio)."""
    fotos, pf, gid = sv["galeria"], sv["portafolio"], esc(sv["id"])
    n = len(fotos)
    f0 = fotos[0]
    for f in fotos:
        check_image(f["nombre"])
    mid = near(f0["nombre"], 800)
    w, h = jpeg_size(IMG_DIR / f"{f0['nombre']}-{mid}.jpg")
    thumbs = []
    for j, f in enumerate(fotos):
        s = variants(f["nombre"])[0]
        tw, th = jpeg_size(IMG_DIR / f"{f['nombre']}-{s}.jpg")
        thumbs.append(f'<button type="button" class="folio__thumb" data-folio-to="{j}" aria-label="Ver foto {j + 1} de {n}"'
                      f' aria-current="{"true" if j == 0 else "false"}"><img src="img/{f["nombre"]}-{s}.jpg" width="{tw}" height="{th}"'
                      f' alt="" loading="lazy" decoding="async"></button>')
    return f'''<div class="folio" data-folio="{gid}">
  <a class="folio__main" href="{largest(f0['nombre'])}" data-gal="{gid}" data-index="0" aria-label="Ampliar foto 1 de {n}: {esc(f0['alt'])}">
    <img data-folio-img src="img/{f0['nombre']}-{mid}.jpg" srcset="{srcset_of(f0['nombre'])}" sizes="(min-width: 1280px) 560px, 45vw" width="{w}" height="{h}" alt="{esc(f0['alt'])}" loading="lazy" decoding="async">
    <span class="folio__zoom" aria-hidden="true">Ampliar</span>
  </a>
  <div class="folio__bar">
    <p class="folio__title"><span class="folio__eyebrow">Trabajo real del taller</span>{esc(pf['vehiculo'])}<span class="folio__job">{esc(pf['trabajo'])}</span></p>
    <div class="folio__nav">
      <button type="button" class="folio__btn" data-folio-prev aria-label="Foto anterior">{CHEV_L}</button>
      <p class="folio__count"><span data-folio-i>01</span> / {n:02d}</p>
      <button type="button" class="folio__btn" data-folio-next aria-label="Foto siguiente">{CHEV_R}</button>
    </div>
  </div>
  <p class="folio__pie" data-folio-pie aria-live="polite">{esc(f0.get('pie', ''))}</p>
  <div class="folio__strip">{"".join(thumbs)}</div>
</div>'''


def reel_html(sv):
    """Fotos del trabajo en fila deslizable (móvil, tablet y sin JavaScript)."""
    fotos, pf, gid = sv["galeria"], sv["portafolio"], esc(sv["id"])
    n = len(fotos)
    items = []
    for j, f in enumerate(fotos):
        m = near(f["nombre"], 480)
        w, h = jpeg_size(IMG_DIR / f"{f['nombre']}-{m}.jpg")
        items.append(f'<a class="reel__item" href="{largest(f["nombre"])}" data-gal="{gid}" data-index="{j}" aria-label="Ver foto {j + 1} de {n}: {esc(f["alt"])}">'
                     f'<img src="img/{f["nombre"]}-{m}.jpg" srcset="{srcset_of(f["nombre"])}" sizes="(min-width: 768px) 45vw, 80vw"'
                     f' width="{w}" height="{h}" alt="" loading="lazy" decoding="async"></a>')
    return f'''<p class="reel__title"><span>Trabajo real del taller</span>{esc(pf['vehiculo'])} · {esc(pf['trabajo'])} · {fotos_word(n)}</p>
    <div class="reel">{"".join(items)}</div>'''


SCENE_MAP = '''<svg class="scene__svg" viewBox="0 0 400 240" preserveAspectRatio="xMidYMid slice">
  <rect width="400" height="240" fill="#f2efe9"/>
  <path d="M-10 0 H70 Q60 40 20 70 Q0 84 -10 86 Z" fill="#c4dff4"/>
  <rect x="112" y="76" width="96" height="56" rx="10" fill="#d4ebc6"/>
  <rect x="252" y="168" width="64" height="40" rx="8" fill="#d4ebc6"/>
  <g fill="none" stroke-linecap="round" stroke-linejoin="round">
    <g stroke="#e2dccf" stroke-width="17"><path d="M-10 60 H410 M-10 150 H410 M-10 214 H410 M90 -10 V250 M230 -10 V250 M340 -10 V250 M150 250 L250 160"/></g>
    <g stroke="#fff" stroke-width="13"><path d="M-10 60 H410 M-10 150 H410 M-10 214 H410 M90 -10 V250 M230 -10 V250 M340 -10 V250 M150 250 L250 160"/></g>
    <path d="M90 250 V162 Q90 150 102 150 H218 Q230 150 230 138 V72 Q230 60 242 60 H300" stroke="#fff" stroke-width="11"/>
    <path data-route d="M90 250 V162 Q90 150 102 150 H218 Q230 150 230 138 V72 Q230 60 242 60 H300" stroke="#0a84ff" stroke-width="6.5"/>
  </g>
  <g class="map-pin" transform="translate(300 60)">
    <circle class="map-pin__pulse" r="14" fill="#e3262d"/>
    <circle r="13" fill="#e3262d" stroke="#fff" stroke-width="3"/>
    <path d="M-5 3 L2 -4 M1.5 -6.5 a3.2 3.2 0 1 0 4.5 4.5 M-5 3 a1.6 1.6 0 1 0 2.2 2.2" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
    <text y="31" text-anchor="middle" class="map-pin__label">Auto Servicio D&amp;A</text>
  </g>
  <g class="map-car" data-car transform="translate(300 60) rotate(90)">
    <circle r="13" fill="#fff" class="map-car__halo"/>
    <rect x="-5.5" y="-9" width="11" height="18" rx="4" fill="#0a84ff"/>
    <rect x="-4" y="-5.5" width="8" height="4" rx="1.4" fill="#cfe6ff"/>
    <rect x="-4" y="3" width="8" height="2.6" rx="1.2" fill="#cfe6ff"/>
  </g>
</svg>'''

CAR_BODY = ('<path d="M60 168 V142 Q62 128 80 124 L128 118 Q150 92 182 84 L250 82 Q276 84 298 112 L332 120 Q348 124 350 140 V168 Z" '
            'fill="#fff" stroke="#1d1d1f" stroke-width="2.5" stroke-linejoin="round"/>'
            '<path d="M140 117 Q157 98 182 92 L211 91 V117 Z M219 91 L248 90 Q265 92 282 115 L219 117 Z" fill="#dfe3e8"/>'
            '<path d="M215 120 V160 M150 128 H166 M238 128 H254" stroke="#1d1d1f" stroke-width="2" stroke-linecap="round"/>'
            '<circle cx="112" cy="170" r="22" fill="#1d1d1f"/><circle cx="112" cy="170" r="9" fill="#d2d2d7"/>'
            '<circle cx="296" cy="170" r="22" fill="#1d1d1f"/><circle cx="296" cy="170" r="9" fill="#d2d2d7"/>')

SCENE_SCAN = f'''<svg class="scene__svg" viewBox="0 0 400 240" preserveAspectRatio="xMidYMid meet">
  <defs>
    <g id="scan-car">{CAR_BODY}</g>
    <clipPath id="scan-lens"><circle data-lens-clip cx="70" cy="128" r="31"/></clipPath>
  </defs>
  <rect width="400" height="240" fill="#f5f5f7"/>
  <ellipse cx="205" cy="196" rx="160" ry="8" fill="#000" opacity=".07"/>
  <use href="#scan-car"/>
  <g class="scan-checks">
    <g data-check="112" transform="translate(112 132)"><circle r="10"/><path d="M-4 0 l3 3 5-6"/></g>
    <g data-check="190" transform="translate(186 70)"><circle r="10"/><path d="M-4 0 l3 3 5-6"/></g>
    <g data-check="250" transform="translate(262 146)"><circle r="10"/><path d="M-4 0 l3 3 5-6"/></g>
    <g data-check="300" transform="translate(326 104)"><circle r="10"/><path d="M-4 0 l3 3 5-6"/></g>
  </g>
  <g data-lens transform="translate(70 128)">
    <g clip-path="url(#scan-lens)" transform="translate(-70 -128)">
      <rect width="400" height="240" fill="#fff"/>
      <g data-lens-zoom transform="translate(70 128) scale(1.7) translate(-70 -128)"><use href="#scan-car"/></g>
    </g>
    <circle r="31" fill="none" stroke="#1d1d1f" stroke-width="5"/>
    <circle r="31" fill="none" stroke="#fff" stroke-width="1.5" opacity=".7"/>
    <path d="M23 23 L44 44" stroke="#1d1d1f" stroke-width="9" stroke-linecap="round"/>
  </g>
</svg>'''


_SCENES_N = 0


def scenes_html(q):
    """Escenas animadas de la cotización: llegada (mapa), revisión con lupa y cotización por WhatsApp."""
    esc_ = q["escenas"]
    steps = "".join(
        f'<li><button type="button" class="scenes__step" data-scene-to="{i}" aria-current="{"true" if i == 0 else "false"}">'
        f'<span class="scenes__n">{i + 1}</span><span class="scenes__txt"><strong>{esc(s["titulo"])}</strong>{esc(s["texto"])}</span>'
        f'<span class="scenes__bar" aria-hidden="true"><i></i></span></button></li>'
        for i, s in enumerate(esc_))
    calle = N["direccion"].split(",")[0]
    global _SCENES_N
    _SCENES_N += 1
    scan = SCENE_SCAN.replace("scan-car", f"scan-car-{_SCENES_N}").replace("scan-lens", f"scan-lens-{_SCENES_N}")
    return f'''<div class="scenes" data-scenes>
  <div class="scenes__stage" aria-hidden="true">
    <div class="scene scene--map is-active" data-scene="map" data-ms="3800">{SCENE_MAP}
      <div class="map-card"><img class="map-card__icon" src="img/logo-dya-mark.png" alt="" width="256" height="256" loading="lazy" decoding="async"><span><strong>{esc(N["nombre"])}</strong>{esc(calle)}</span><em class="map-card__chip">Llegaste</em></div>
    </div>
    <div class="scene scene--scan" data-scene="scan" data-ms="4200">{scan}
      <div class="scan-chip"><span class="scan-chip__ring"></span>Revisión · aprox. 2 h</div>
    </div>
    <div class="scene scene--wa" data-scene="wa" data-ms="3600">
      <div class="lock">
        <p class="lock__time">17:30</p>
        <div class="notif">
          <span class="notif__icon"><img src="img/logo-dya-mark.png" alt="" width="256" height="256" loading="lazy" decoding="async"><span class="notif__badge"><svg viewBox="0 0 24 24"><path d="M12 3.5a8.5 8.5 0 0 0-7.3 12.8L3.5 20.5l4.3-1.1A8.5 8.5 0 1 0 12 3.5Z" fill="none" stroke="#fff" stroke-width="2.4" stroke-linejoin="round"/></svg></span></span>
          <span class="notif__body"><span class="notif__app">WHATSAPP <em>ahora</em></span><strong>{esc(N["nombre"])}</strong>Tu cotización está lista. Con tu aprobación, iniciamos la reparación.</span>
        </div>
        <div class="notif notif--doc"><span class="notif__doc"></span><span><strong>Cotización</strong>Revisión presencial</span></div>
      </div>
    </div>
  </div>
  <ol class="scenes__steps">{steps}</ol>
</div>'''


def quote_panel(compact=False, clave="cotizacion"):
    """Panel tipográfico (sin foto) para las etapas de Cotización y Entrega."""
    q = CFG["recorrido"][clave]
    if q.get("escenas"):
        return f'''<div class="quote-panel quote-panel--scenes{' quote-panel--inline' if compact else ''}">
  <p class="quote-panel__title">{esc(q.get('panelTitulo', q['titulo']))}</p>
  {scenes_html(q)}
  <p class="quote-panel__num"><span>WhatsApp</span>{esc(N["whatsappMostrar"])}</p>
</div>'''
    items = "".join(f"<li><span>{i}</span>{esc(t)}</li>" for i, t in enumerate(q["lista"], start=1))
    num = (f'<p class="quote-panel__num"><span>WhatsApp</span>{esc(N["whatsappMostrar"])}</p>'
           if clave == "cotizacion" else "")
    return f'''<div class="quote-panel{' quote-panel--inline' if compact else ''}">
  <p class="quote-panel__title">{esc(q.get('panelTitulo', q['titulo']))}</p>
  <p class="quote-panel__label">Cómo funciona</p>
  <ul class="quote-panel__list">{items}</ul>
  {num}
</div>'''


TICKS = ('<svg class="msg__ticks" viewBox="0 0 18 11" aria-hidden="true"><path d="M1 6l3 3 6-7M7 8.5 8 9.5l7-8" fill="none"'
         ' stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def chat_html():
    """Conversación de WhatsApp (estilo iOS) que cuenta los pasos de la entrega; se anima en app.js."""
    e = CFG["recorrido"]["entrega"]
    ch = e["chat"]
    horas = ch.get("horas", [])
    lista = e["lista"]

    def hora(k):
        return f'<span class="msg__meta" aria-hidden="true">{esc(horas[k]) if k < len(horas) else ""}</span>'

    msgs, k = [], 0
    for j, texto in enumerate(lista):
        if j == len(lista) - 1 and ch.get("respuesta"):
            msgs.append(f'<li class="msg msg--out" data-from="cliente"><p><span class="sr-only">Tú: </span>{esc(ch["respuesta"])}'
                        f'{hora(k)}{TICKS}</p></li>')
            k += 1
        foto = ""
        if j == 0 and ch.get("foto"):
            name = ch["foto"]
            check_image(name)
            m = near(name, 480)
            w, h = jpeg_size(IMG_DIR / f"{name}-{m}.jpg")
            foto = (f'<img class="msg__photo" src="img/{name}-{m}.jpg" width="{w}" height="{h}" alt="{esc(ch.get("fotoAlt", ""))}"'
                    f' loading="lazy" decoding="async">')
        msgs.append(f'<li class="msg msg--in{" msg--photo" if foto else ""}" data-from="taller">{foto}'
                    f'<p><span class="sr-only">Paso {j + 1}: </span>{esc(texto)}{hora(k)}</p></li>')
        k += 1
    return f'''<figure class="chat" data-chat aria-label="{esc(e.get('panelTitulo', e['titulo']))}: así te avisamos por WhatsApp">
  <div class="chat__head" aria-hidden="true">
    <span class="chat__back"><svg viewBox="0 0 10 18"><path d="M9 1 1 9l8 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
    <span class="chat__avatar"><img src="img/logo-dya-mark.png" alt="" width="256" height="256" loading="lazy" decoding="async"></span>
    <span class="chat__who"><strong>{esc(ch['contacto'])}</strong><span data-chat-status data-idle="en línea">en línea</span></span>
  </div>
  <ol class="chat__log">
    <li class="chat__day" aria-hidden="true"><span>Hoy</span></li>
    {"".join(msgs)}
    <li class="msg msg--in msg--typing" data-chat-typing hidden aria-hidden="true"><p><i></i><i></i><i></i></p></li>
  </ol>
  <div class="chat__compose" aria-hidden="true"><span class="chat__input">Mensaje</span><span class="chat__send"></span></div>
</figure>'''


def services_html():
    """Recorrido por etapas: cotización + servicios en el orden del flujo del taller."""
    q = CFG["recorrido"]["cotizacion"]
    total = 2 + len(CFG["servicios"])  # cotización + servicios + entrega
    stages, shots = [], []

    # Etapa 1: cotización (sin foto: panel tipográfico)
    stages.append(f"""<li class="stage is-active" data-stage="cotizacion">
  <span class="stage__num" aria-hidden="true">01</span>
  <div class="stage__body">
    <h3>{esc(q['titulo'])}</h3>
    <p>{esc(q['descripcion'])}</p>
    <div class="stage__media">{quote_panel(compact=True)}</div>
    <div class="svc__actions">
      <a class="link-arrow" href="#contacto">Agendar evaluación {ARROW}</a>
      <a class="link-arrow" href="{WA_LINK}" target="_blank" rel="noopener">Escribir por WhatsApp {ARROW}</a>
    </div>
  </div>
</li>""")
    shots.append(f'<div class="shot shot--quote is-active" data-for="cotizacion">{quote_panel()}</div>')

    for i, sv in enumerate(CFG["servicios"], start=2):
        stages.append(f"""<li class="stage" data-stage="{esc(sv['id'])}">
  <span class="stage__num" aria-hidden="true">{i:02d}</span>
  <div class="stage__body">
    <h3>{esc(sv['titulo'])}</h3>
    <p>{esc(sv['descripcion'])}</p>
    <div class="stage__media stage__media--reel">{reel_html(sv)}</div>
    <div class="svc__actions">
      <a class="link-arrow" href="#contacto" data-service="{esc(sv['titulo'])}">Cotizar este servicio {ARROW}</a>
    </div>
  </div>
</li>""")
        shots.append(f'<div class="shot shot--folio" data-for="{esc(sv["id"])}">{folio_html(sv)}</div>')

    e = CFG["recorrido"]["entrega"]
    stages.append(f"""<li class="stage" data-stage="entrega">
  <span class="stage__num" aria-hidden="true">{total:02d}</span>
  <div class="stage__body">
    <h3>{esc(e['titulo'])}</h3>
    <p>{esc(e['descripcion'])}</p>
    <div class="stage__media stage__media--chat">{chat_html()}</div>
    <div class="svc__actions">
      <a class="link-arrow" href="#contacto">Agendar evaluación {ARROW}</a>
    </div>
  </div>
</li>""")
    shots.append(f'''<div class="shot shot--chat" data-for="entrega">
  <p class="shot__label">{esc(e.get('panelTitulo', e['titulo']))}</p>
  {chat_html()}
</div>''')

    return f"""<div class="journey" data-journey>
  <div class="journey__rail" aria-hidden="true"><span class="journey__fill" data-journey-fill></span></div>
  <ol class="journey__list">
{chr(10).join(stages)}
  </ol>
  <div class="journey__panel">
    <div class="journey__frame">{"".join(shots)}</div>
  </div>
</div>"""


def gallery_json():
    data = {}
    for sv in CFG["servicios"]:
        fotos = []
        for f in sv["galeria"]:
            big = max(variants(f["nombre"]))
            w, h = jpeg_size(IMG_DIR / f"{f['nombre']}-{big}.jpg")
            fotos.append({"src": f"img/{f['nombre']}-{big}.jpg", "srcset": srcset_of(f["nombre"]),
                          "alt": f["alt"], "pie": f.get("pie", ""), "ilu": bool(f.get("ilustrativa")), "w": w, "h": h})
        pf = sv.get("portafolio")
        titulo = f"{pf['vehiculo']} · {pf['trabajo']}" if pf else sv["titulo"]
        data[sv["id"]] = {"titulo": titulo, "fotos": fotos}
    # </ dentro de JSON no debe cerrar la etiqueta script
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def title_lines(name):
    """Divide el nombre en dos líneas (primera palabra / resto) para la animación de entrada."""
    first, _, rest = name.partition(" ")
    lines = [first, rest] if rest else [first]
    acento = CFG["hero"].get("acento", "")

    def ink(t):
        # La palabra de acento (D&A) va en rojo; app.js la pinta con un aerosol generativo al cargar
        if acento and acento in t:
            a, _, b = t.partition(acento)
            return f'{esc(a)}<span class="title-accent" data-spray>{esc(acento)}</span>{esc(b)}'
        return esc(t)
    return " ".join(f'<span class="title-line"><span class="title-ink">{ink(t)}</span></span>' for t in lines)


def particular_media():
    """Logotipo de la empresa para la pestaña de Reparación particular (se anima al mostrarse)."""
    return f'<img class="badge-logo" src="img/logo-dya-800.jpg" width="800" height="409" alt="{esc(N["nombre"])}" loading="lazy" decoding="async">'


def steps(items):
    return "\n".join(f'<li><span class="timeline__num">{i}</span><p>{esc(t)}</p></li>' for i, t in enumerate(items, start=1))


STAR = "9,1 11.4,6.6 17.5,7.2 12.9,11.2 14.3,17 9,13.9 3.7,17 5.1,11.2 0.5,7.2 6.6,6.6"


def stars():
    polys = "".join(f'<polygon transform="translate({i * 19} 0)" points="{STAR}"/>' for i in range(5))
    return f'<svg class="stars" viewBox="0 0 94 18" role="img" aria-label="5 de 5 estrellas" fill="currentColor">{polys}</svg>'


def autor_corto(nombre):
    """Nombre e inicial del apellido ("Armando C."), salvo que la configuración permita el nombre completo."""
    if CFG.get("resenasNombreCompleto"):
        return nombre
    partes = nombre.split()
    if len(partes) < 2:
        return nombre.title()
    return f"{partes[0].title()} {partes[-1][0].upper()}."


def reviews_html():
    total = len(CFG["resenas"])
    slides = "\n".join(f"""<figure class="review" role="group" aria-roledescription="opinión" aria-label="{i + 1} de {total}">
  {stars()}
  <blockquote><p>{esc(r['texto'])}</p></blockquote>
  <figcaption>{esc(autor_corto(r['autor']))}</figcaption>
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
  <div class="hero__depth">
    <div class="hero__tilt" data-hero-tilt>
      <picture class="hero__img">
        <source media="(max-width: 719px)" srcset="{srcset_of(P['alta'])}" sizes="100vw">
        <img src="img/{P['ancha']}-1200.jpg" srcset="{srcset_of(P['ancha'])}" sizes="100vw"
             width="{P['anchaDims'][0]}" height="{P['anchaDims'][1]}" alt="{esc(P['alt'])}" fetchpriority="high">
      </picture>
    </div>
  </div>
  <div class="wrap hero__inner">
    <h1 id="h1" class="hero__title">{title_lines(N['nombre'])}</h1>
    <p class="hero__lead">{esc(CFG['hero']['texto'])}</p>
  </div>
</section>

<section class="facts-bar" aria-label="Datos del taller">
  <dl class="wrap">
    <div class="fact"><dt>Dónde</dt><dd>{esc(N['ciudad'])}</dd></div>
    <div class="fact"><dt>WhatsApp</dt><dd><a href="{WA_LINK}" target="_blank" rel="noopener">{esc(N['whatsappMostrar'])}</a></dd></div>
    <div class="fact"><dt>Llamadas</dt><dd><a href="tel:{TEL}">{esc(N['telefonoMostrar'])}</a></dd></div>
    <div class="fact"><dt>Hoy</dt><dd><span class="status" data-open-status data-open=""></span> <span data-today-hours></span></dd></div>
  </dl>
</section>

<section class="section" id="servicios" aria-labelledby="h-servicios">
  <div class="wrap">
    <div class="section__head">
      <h2 id="h-servicios">{esc(CFG['recorrido']['titulo'])}</h2>
      <p class="lead">{esc(CFG['recorrido']['intro'])}</p>
    </div>
{services_html()}
  </div>
</section>

<section class="section section--dark on-dark" id="como-trabajamos" aria-labelledby="h-proceso">
  <div class="wrap">
    <h2 id="h-proceso" class="sr-only">Cómo trabajamos tu reparación</h2>
    <div class="flows" data-flows>
      <div class="flows__tabs js-only" role="tablist" aria-label="Tipo de reparación">
        <button class="flows__tab" type="button" role="tab" id="tab-qualitas" aria-selected="true" aria-controls="flow-qualitas">Con seguro Qualitas</button>
        <button class="flows__tab" type="button" role="tab" id="tab-particular" aria-selected="false" aria-controls="flow-particular" tabindex="-1">Reparación particular</button>
      </div>
      <div class="flow" id="flow-qualitas" role="tabpanel" aria-labelledby="tab-qualitas">
        <div class="qualitas">
          <div class="qualitas__badge"><img src="img/{CFG['qualitas']['logo']}" width="360" height="468" alt="{esc(CFG['qualitas']['logoAlt'])}" loading="lazy" decoding="async"></div>
          <div class="qualitas__copy">
            <h3>{esc(CFG['qualitas']['titulo'])}</h3>
            <p>{esc(CFG['qualitas']['texto'])}</p>
            <ul class="qualitas__facts">{"".join(f"<li>{esc(t)}</li>" for t in CFG['qualitas']['datos'])}</ul>
          </div>
        </div>
        <ol class="timeline">
{steps(CFG['procesoQualitas'])}
        </ol>
      </div>
      <div class="flow" id="flow-particular" role="tabpanel" aria-labelledby="tab-particular">
        <div class="qualitas">
          <div class="qualitas__badge qualitas__badge--logo">{particular_media()}</div>
          <div class="qualitas__copy">
            <h3>{esc(CFG['particular']['titulo'])}</h3>
            <p>{esc(CFG['particular']['texto'])}</p>
            <ul class="qualitas__facts">{"".join(f"<li>{esc(t)}</li>" for t in CFG['particular']['datos'])}</ul>
          </div>
        </div>
        <ol class="timeline">
{steps(CFG['procesoParticular'])}
        </ol>
      </div>
    </div>
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

<section class="section section--red on-dark" id="resenas" aria-labelledby="h-resenas">
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
      <p class="lead">Cuéntanos qué necesita tu vehículo y agenda la evaluación presencial (aprox. 2 horas) para recibir tu cotización precisa. Envías tu solicitud por WhatsApp o por correo.</p>
      <dl class="info-list">
        <div><dt>WhatsApp</dt><dd class="info-num"><span>{esc(N['whatsappMostrar'])}</span>
          <a href="{WA_LINK}" target="_blank" rel="noopener">Escribir por WhatsApp</a></dd></div>
        <div><dt>Llamadas</dt><dd class="info-num"><span>{esc(N['telefonoMostrar'])}</span>
          <a href="tel:{TEL}">Llamar</a></dd></div>
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
        <p>El formulario necesita JavaScript. Escríbenos por <a href="{WA_LINK}">WhatsApp ({esc(N['whatsappMostrar'])})</a>, llama al <a href="tel:{TEL}">{esc(N['telefonoMostrar'])}</a> o escribe a <a href="mailto:{esc(N['correo'])}">{esc(N['correo'])}</a>.</p></div></noscript>
      <form class="form js-only" id="quote-form" method="post" action="#contacto" novalidate data-wa="{N['whatsappNumero']}" data-mail="{esc(N['correo'])}">
        <h3>Agenda tu evaluación</h3>
        <p class="form__alt">Los campos con * son obligatorios.</p>
        <div class="field">
          <label for="nombre">Nombre *</label>
          <input id="nombre" name="nombre" type="text" autocomplete="name" maxlength="80" aria-describedby="nombre-err">
          <p class="err" id="nombre-err" hidden></p>
        </div>
        <fieldset class="field radios-wrap">
          <legend>¿Por dónde quieres enviar tu solicitud? *</legend>
          <div class="radios">
            <label><input type="radio" name="canal" value="whatsapp" checked> WhatsApp</label>
            <label><input type="radio" name="canal" value="correo"> Correo electrónico</label>
          </div>
          <p class="hint" id="canal-hint">Por correo se abre tu programa de correo con el mensaje listo para {esc(N['correo'])}.</p>
        </fieldset>
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
          <p class="hint" id="descripcion-hint">Máximo 600 caracteres. Las fotos las adjuntas tú en WhatsApp o en el correo.</p>
          <p class="err" id="descripcion-err" hidden></p>
        </div>
        <p class="form__privacy">Este formulario no guarda tus datos: arma un mensaje que tú decides enviar. Al enviarlo, el taller usará tus datos para responderte y cotizar, como explica el <a href="privacidad.html">aviso de privacidad</a>.</p>
        <button class="btn btn--primary" type="submit" id="form-submit" disabled>Continuar en WhatsApp</button>
        <p class="form__alt" id="form-help">Se abre WhatsApp con tu mensaje listo; revísalo y pulsa Enviar. Las fotos las adjuntas ahí.</p>
        <p id="form-status" role="alert" class="err"></p>
        <p id="form-done" class="form__done" role="status" hidden></p>
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
    cont = (f'WhatsApp <a href="{WA_LINK}" target="_blank" rel="noopener">{esc(N["whatsappMostrar"])}</a>, '
            f'teléfono <a href="tel:{TEL}">{esc(N["telefonoMostrar"])}</a> o correo <a href="mailto:{esc(N["correo"])}">{esc(N["correo"])}</a>')
    legal = N.get("responsableLegal", "").strip()
    quien = f"{esc(legal)}, que opera el taller con el nombre comercial {esc(N['responsable'])}" if legal else esc(N['responsable'])
    return f'''
{header(False)}
<main id="contenido" class="wrap legal">
  <h1>Aviso de privacidad</h1>
  <p>Última actualización: {esc(N['fechaPrivacidad'])}. Este aviso se emite conforme a la Ley Federal de Protección de Datos Personales en Posesión de los Particulares.</p>
  <section><h2>1. Responsable</h2>
    <p>{quien}, con domicilio en {esc(N['direccion'])}, es responsable del tratamiento de tus datos personales. Contacto: {cont}.</p></section>
  <section><h2>2. Datos que tratamos</h2>
    <p>Cuando nos pides una cotización por el formulario de este sitio, por WhatsApp, por teléfono o en el taller: nombre, número de WhatsApp o teléfono, correo electrónico (si eliges ese medio), datos del vehículo (marca, modelo, año, placas cuando hace falta para el servicio o el siniestro) y la descripción de lo que necesitas. Si la reparación es por siniestro, también el número de siniestro o de póliza.</p>
    <p>No solicitamos datos personales sensibles. Te pedimos no incluirlos en tus mensajes.</p>
    <p>El formulario no envía nada a un servidor de este sitio ni guarda información: arma en tu navegador un mensaje que tú decides enviar por WhatsApp o por correo.</p></section>
  <section><h2>3. Para qué los usamos</h2>
    <ul><li>Responder tu solicitud y agendar la evaluación presencial.</li><li>Elaborar y enviarte la cotización.</li><li>Realizar la reparación, avisarte de su avance y coordinar la entrega.</li><li>Atender el siniestro con tu aseguradora, cuando aplique.</li></ul>
    <p>Son finalidades necesarias para darte el servicio. No usamos tus datos para publicidad ni para otras finalidades.</p></section>
  <section><h2>4. Con quién los compartimos</h2>
    <p>No vendemos ni compartimos tus datos con terceros para sus propios fines. Si tu reparación es por siniestro, compartimos con tu aseguradora los datos necesarios para atenderlo, porque es indispensable para esa relación. Fuera de ese caso, solo los comunicaríamos en los supuestos que permite la ley o por requerimiento de una autoridad competente.</p>
    <p>Los mensajes que envías por WhatsApp o por correo viajan por esas plataformas y quedan sujetos a sus propios términos y avisos de privacidad.</p></section>
  <section><h2>5. Fotografías de trabajos</h2>
    <p>Las fotos de reparaciones que mostramos en este sitio se publican sin placas legibles ni datos de sus propietarios. Si reconoces tu vehículo y quieres que retiremos una foto, escríbenos y la quitamos.</p></section>
  <section><h2>6. Tus derechos (ARCO) y cómo ejercerlos</h2>
    <p>Puedes acceder a tus datos, rectificarlos, cancelarlos u oponerte a su uso; también revocar tu consentimiento o limitar su uso o divulgación. Envía tu solicitud a {esc(N['correo'])} o por WhatsApp al {esc(N['whatsappMostrar'])} con: tu nombre y un medio para responderte, una identificación que acredite tu identidad (o la de tu representante), qué derecho quieres ejercer y sobre qué datos, y cualquier documento que ayude a ubicarlos.</p>
    <p>Te responderemos en un plazo máximo de 20 días hábiles y, si procede, haremos efectiva tu solicitud dentro de los 15 días hábiles siguientes a la respuesta. Si consideras que no se atendió tu solicitud, puedes acudir a la autoridad de protección de datos personales (la Secretaría Anticorrupción y Buen Gobierno).</p></section>
  <section><h2>7. Cuánto tiempo los conservamos</h2>
    <p>Solo el tiempo necesario para el servicio, la garantía y las obligaciones fiscales y legales que correspondan; después los eliminamos.</p></section>
  <section><h2>8. Cookies y tecnologías de rastreo</h2>
    <p>Este sitio no usa cookies propias ni herramientas de analítica o publicidad. Usa servicios de terceros que reciben datos técnicos de tu visita (como tu dirección IP): las tipografías se cargan desde Google Fonts y el mapa de Google se carga solo si pulsas el botón para verlo; al hacerlo, Google puede usar sus propias cookies. Puedes bloquear o borrar cookies desde la configuración de tu navegador.</p></section>
  <section><h2>9. Cambios a este aviso</h2>
    <p>Cualquier cambio se publicará en esta misma página con su fecha de actualización.</p></section>
</main>
{footer(False)}
'''


FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@300;400;700&display=swap">'

CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; script-src 'self'; frame-src https://www.google.com; "
       "connect-src 'none'; form-action 'none'; base-uri 'self'; object-src 'none'")


def asset_version(rel):
    import hashlib
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()[:10]


def page(title, desc, body, inline, home):
    live = bool(N["dominio"]) and bool(N.get("publicado"))
    # La página de privacidad no se indexa nunca; la principal solo cuando "publicado" es true
    robots = "" if (live and home) else '<meta name="robots" content="noindex, nofollow">'
    canon = f'<link rel="canonical" href="{esc(N["dominio"])}/">' if (N["dominio"] and home) else ""
    og_url = (f'<meta property="og:url" content="{esc(N["dominio"])}/"><meta property="og:image" content="{esc(N["dominio"])}/img/logo-dya-800.jpg">'
              '<meta name="twitter:card" content="summary">') if (N["dominio"] and home) else ""
    css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
    js = (ROOT / "js" / "app.js").read_text(encoding="utf-8")
    if inline:
        head_css = f"<style>{css}</style>"
        tail_js = f"<script>{js}</script>"
        csp = ""
        meta_top = ""
        css_pad = ""
    else:
        # Versión por contenido: cada cambio de CSS o JS cambia la URL y el navegador no usa una copia vieja
        head_css = f'<link rel="stylesheet" href="css/styles.css?v={asset_version("css/styles.css")}">'
        tail_js = f'<script src="js/app.js?v={asset_version("js/app.js")}" defer></script>'
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
<link rel="icon" type="image/png" sizes="32x32" href="img/favicon-dya-32.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta property="og:type" content="website"><meta property="og:locale" content="es_MX">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">{og_url}
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
    live = bool(N["dominio"]) and bool(N.get("publicado"))
    robots = (f"User-agent: *\nAllow: /\nDisallow: /privacidad.html\nSitemap: {N['dominio']}/sitemap.xml\n" if live
              else "User-agent: *\nDisallow: /\n")
    sm = ROOT / "sitemap.xml"
    if live:
        sm.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                      f'  <url><loc>{N["dominio"]}/</loc></url>\n</urlset>\n', encoding="utf-8")
    elif sm.exists():
        sm.unlink()
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")
    print("OK: index.html, privacidad.html, robots.txt, artifact/")


if __name__ == "__main__":
    main()
