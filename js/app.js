/* Auto Servicio D&A: comportamiento de la página.
   Cada pieza se inicia una sola vez al cargar el documento y solo toca elementos que existen en esa página.
   No guarda datos personales (ni consola, ni almacenamiento, ni URLs internas). */
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  function onReady(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  /* ---------- Menú móvil ---------- */
  function initMenu() {
    var toggle = document.getElementById("menu-toggle");
    var nav = document.getElementById("site-nav");
    if (!toggle || !nav) return;
    function setOpen(open, restoreFocus) {
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.textContent = open ? "Cerrar" : "Menú";
      if (!open && restoreFocus) toggle.focus();
    }
    toggle.addEventListener("click", function () {
      setOpen(!nav.classList.contains("is-open"), false);
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false, false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) setOpen(false, true);
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth >= 1024) setOpen(false, false);
    });
    window.addEventListener("hashchange", function () { setOpen(false, false); });
    window.addEventListener("pagehide", function () { setOpen(false, false); });
  }

  /* ---------- Hero: inclinación 3D del carro siguiendo el puntero ----------
     Solo con ratón (hover real) y sin "reducir movimiento". Un único elemento, solo transform;
     el bucle de animación se detiene en cuanto la imagen alcanza su posición. */
  function initHeroTilt() {
    var hero = document.querySelector(".hero");
    var tilt = document.querySelector("[data-hero-tilt]");
    if (!hero || !tilt) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    var cur = { x: 0, y: 0 }, tgt = { x: 0, y: 0 }, raf = 0;
    function frame() {
      cur.x += (tgt.x - cur.x) * 0.08;
      cur.y += (tgt.y - cur.y) * 0.08;
      tilt.style.transform = "scale(1.04) rotateX(" + (cur.y * -4).toFixed(3) + "deg) rotateY(" + (cur.x * 6).toFixed(3) +
        "deg) translate3d(" + (cur.x * -16).toFixed(2) + "px," + (cur.y * -10).toFixed(2) + "px,0)";
      if (Math.abs(tgt.x - cur.x) > 0.0008 || Math.abs(tgt.y - cur.y) > 0.0008) raf = requestAnimationFrame(frame);
      else raf = 0;
    }
    function kick() { if (!raf) raf = requestAnimationFrame(frame); }
    hero.addEventListener("pointermove", function (e) {
      var r = hero.getBoundingClientRect();
      tgt.x = (e.clientX - r.left) / r.width - 0.5;
      tgt.y = (e.clientY - r.top) / r.height - 0.5;
      kick();
    });
    hero.addEventListener("pointerleave", function () { tgt.x = 0; tgt.y = 0; kick(); });
  }

  /* ---------- Horario: hoy y estado abierto/cerrado ---------- */
  function initHours() {
    var dataEl = document.getElementById("hours-data");
    if (!dataEl) return;
    var cfg;
    try { cfg = JSON.parse(dataEl.textContent); } catch (err) { return; }
    var parts = {};
    try {
      new Intl.DateTimeFormat("es-MX", { timeZone: cfg.tz, weekday: "long", hour: "2-digit", minute: "2-digit", hour12: false })
        .formatToParts(new Date()).forEach(function (p) { parts[p.type] = p.value; });
    } catch (err) { return; }
    var day = (parts.weekday || "").toLowerCase();
    var minutes = (parseInt(parts.hour, 10) % 24) * 60 + parseInt(parts.minute, 10);
    var today = null;
    cfg.days.forEach(function (d) {
      if (d.dia.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "") ===
          day.normalize("NFD").replace(/[̀-ͯ]/g, "")) today = d;
    });
    document.querySelectorAll("[data-day]").forEach(function (row) {
      if (today && row.getAttribute("data-day") === today.dia) row.classList.add("is-today");
    });
    if (!today) return;
    function toMin(s) { var p = s.split(":"); return parseInt(p[0], 10) * 60 + parseInt(p[1], 10); }
    function fmt(s) {
      var p = s.split(":"), h = parseInt(p[0], 10), m = p[1];
      return (h % 12 || 12) + (m === "00" ? "" : ":" + m) + (h < 12 ? " a. m." : " p. m.");
    }
    var open = false, label = "Cerrado hoy", range = "";
    if (today.abre && today.cierra) {
      var a = toMin(today.abre), c = toMin(today.cierra);
      open = minutes >= a && minutes < c;
      label = open ? "Abierto ahora" : "Cerrado ahora";
      range = fmt(today.abre) + " a " + fmt(today.cierra);
    }
    document.querySelectorAll("[data-open-status]").forEach(function (el) {
      el.setAttribute("data-open", open ? "true" : "false");
      el.textContent = label;
    });
    document.querySelectorAll("[data-today-hours]").forEach(function (el) { el.textContent = range; });
  }

  /* ---------- Recorrido de servicios: la etapa que cruza el centro de la pantalla se activa ----------
     Sin escuchar el scroll en cada frame: IntersectionObserver marca la etapa y el cambio
     visual es solo opacity/transform (barra de avance con scaleY). */
  function initJourney() {
    var root = document.querySelector("[data-journey]");
    if (!root) return;
    var stages = Array.prototype.slice.call(root.querySelectorAll(".stage"));
    var shots = root.querySelectorAll(".shot");
    var fill = root.querySelector("[data-journey-fill]");
    var current = root.querySelector("[data-journey-current]");
    var name = root.querySelector("[data-journey-name]");
    if (!stages.length) return;
    var active = -1;

    function activate(i) {
      if (i === active) return;
      active = i;
      var id = stages[i].getAttribute("data-stage");
      stages.forEach(function (s, j) { s.classList.toggle("is-active", j === i); s.classList.toggle("is-past", j < i); });
      shots.forEach(function (sh) { sh.classList.toggle("is-active", sh.getAttribute("data-for") === id); });
      if (fill) fill.style.transform = "scaleY(" + ((i + 1) / stages.length) + ")";
      if (current) current.textContent = (i + 1 < 10 ? "0" : "") + (i + 1);
      if (name) name.textContent = stages[i].querySelector("h3").textContent;
    }

    root.classList.add("is-enhanced");
    activate(0);
    if (!("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) activate(stages.indexOf(e.target));
      });
    }, { rootMargin: "-38% 0px -52% 0px", threshold: 0 });
    stages.forEach(function (s) { io.observe(s); });
    // Hover o foco dentro de una etapa también la activa (teclado y ratón)
    stages.forEach(function (s, i) {
      s.addEventListener("focusin", function () { activate(i); });
    });
    // Con teclado, entrar a un portafolio del panel muestra su etapa
    Array.prototype.forEach.call(shots, function (sh) {
      sh.addEventListener("focusin", function () {
        var id = sh.getAttribute("data-for");
        for (var k = 0; k < stages.length; k++) {
          if (stages[k].getAttribute("data-stage") === id) { activate(k); break; }
        }
      });
    });
  }

  /* ---------- Entrega: conversación de WhatsApp que se escribe sola ---------- */
  function initChats() {
    var chats = document.querySelectorAll("[data-chat]");
    if (!chats.length || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    Array.prototype.forEach.call(chats, function (chat) {
      var msgs = Array.prototype.slice.call(chat.querySelectorAll(".msg:not(.msg--typing)"));
      var typing = chat.querySelector("[data-chat-typing]");
      var status = chat.querySelector("[data-chat-status]");
      var log = chat.querySelector(".chat__log");
      var timers = [], state = "idle";

      function later(fn, ms) { timers.push(setTimeout(fn, ms)); }
      function setTyping(on) {
        typing.hidden = !on;
        status.textContent = on ? "escribiendo…" : status.getAttribute("data-idle");
        status.classList.toggle("is-typing", on);
      }
      function reset() {
        timers.forEach(clearTimeout); timers = [];
        msgs.forEach(function (m) { m.classList.remove("is-in", "is-read"); });
        setTyping(false);
        state = "idle";
      }
      function play() {
        if (state !== "idle") return;
        state = "playing";
        var t = 120;
        msgs.forEach(function (m, i) {
          if (m.getAttribute("data-from") === "cliente") {
            t += 900;
            later(function () { m.classList.add("is-in"); }, t);
            later(function () { m.classList.add("is-read"); }, t + 900);
            t += 700;
          } else {
            var think = i === 0 ? 650 : 1100;
            later(function () { log.insertBefore(typing, m); setTyping(true); }, t);
            t += think;
            later(function () { setTyping(false); m.classList.add("is-in"); }, t);
            t += 500;
          }
        });
        later(function () { state = "done"; }, t);
      }

      chat.classList.add("is-armed");
      watchShown(chat, play, reset);
    });
  }

  /* Llama a onShow cuando el elemento está en pantalla (y, si vive en el panel del recorrido, su etapa está activa);
     onHide al dejar de estarlo. Así las animaciones solo corren cuando alguien las ve. */
  function watchShown(el, onShow, onHide) {
    var shot = el.closest(".shot");
    var visible = false, active = !shot, on = false;
    function update() {
      var now = visible && active;
      if (now === on) return;
      on = now;
      if (now) onShow(); else onHide();
    }
    if (shot) {
      active = shot.classList.contains("is-active");
      new MutationObserver(function () { active = shot.classList.contains("is-active"); update(); })
        .observe(shot, { attributes: true, attributeFilter: ["class"] });
    }
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting && e.intersectionRatio >= 0.3) visible = true;
          else if (!e.isIntersecting) visible = false;
          update();
        });
      }, { threshold: [0, 0.3] }).observe(el);
    } else { visible = true; update(); }
  }

  /* ---------- Hero: aerosol generativo que pinta D&A (primer gris → rojo) ----------
     "Niebla de cabina": una boquilla recorre las letras; cada cuadro atomiza gotas con tamaño
     log-normal (como la pintura real), dispersión gaussiana alrededor del abanico y arrastre del aire.
     Semilla fija: el mismo gesto en cada visita. */
  function initSpray() {
    var el = document.querySelector("[data-spray]");
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    // La capa roja es un ::after con el mismo texto (no agrega texto al título para lectores ni buscadores)
    el.setAttribute("data-text", el.textContent);
    var canvas = document.createElement("canvas");
    canvas.className = "title-accent__mist";
    canvas.setAttribute("aria-hidden", "true");
    el.appendChild(canvas);
    el.classList.add("is-armed");
    var ctx = canvas.getContext("2d");
    if (!ctx) { el.classList.remove("is-armed"); return; }

    var seed = 0x0da;  // mulberry32
    function rand() {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    }
    function gauss() { var u = 1 - rand(), v = rand(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
    var palette = ["227,38,45", "196,22,28", "255,82,88", "160,16,22"];

    function start() {
      var r = canvas.getBoundingClientRect();
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var W = r.width, H = r.height;
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      // Las letras ocupan el centro del lienzo (12 % de margen a los lados, 30 % arriba)
      var x0 = W * 0.0968, x1 = W * 0.9032, cy = H * 0.5, letterH = H / 1.6;
      var drops = [], t0 = performance.now(), PASS = 1100, FADE = 650, last = t0;
      function ease(k) { return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; }

      function frame(now) {
        var dt = Math.min(now - last, 40); last = now;
        var k = Math.min((now - t0) / PASS, 1), e = ease(k);
        var hx = x0 + (x1 - x0) * (e * 1.08 - 0.04), hy = cy + Math.sin(e * Math.PI * 3) * letterH * 0.08;
        // La pintura cubre hasta donde ya pasó la boquilla
        var pct = Math.max(0, Math.min(1, (hx - x0) / (x1 - x0)));
        el.style.setProperty("--paint-clip", ((1 - pct) * 100).toFixed(2) + "%");
        if (k < 1) {
          var n = Math.round(dt * 2.2);
          for (var i = 0; i < n; i++) {
            var size = Math.exp(gauss() * 0.55) * 1.05;            // atomizado log-normal
            var spread = letterH * 0.42;
            drops.push({
              x: hx + gauss() * spread * 0.55, y: hy + gauss() * spread,
              vx: (rand() - 0.35) * 0.05, vy: (rand() - 0.5) * 0.04,
              s: size, life: 260 + rand() * 520, age: 0,
              c: palette[(rand() * palette.length) | 0], a: 0.35 + rand() * 0.5,
              mist: rand() < 0.06
            });
          }
        }
        ctx.clearRect(0, 0, W, H);
        var fadeAll = k < 1 ? 1 : Math.max(0, 1 - (now - t0 - PASS) / FADE);
        for (var j = drops.length - 1; j >= 0; j--) {
          var d = drops[j];
          d.age += dt; d.vx *= 0.96; d.vy *= 0.96; d.x += d.vx * dt; d.y += d.vy * dt;
          var life = 1 - d.age / d.life;
          if (life <= 0) { drops.splice(j, 1); continue; }
          ctx.fillStyle = "rgba(" + d.c + "," + (d.mist ? 0.06 : d.a * life) * fadeAll + ")";
          ctx.beginPath();
          ctx.arc(d.x, d.y, d.mist ? d.s * 9 : d.s, 0, 6.2832);
          ctx.fill();
        }
        if (fadeAll > 0) requestAnimationFrame(frame);
        else { canvas.remove(); el.classList.remove("is-armed"); el.style.removeProperty("--paint-clip"); }
      }
      requestAnimationFrame(frame);
    }

    // Empieza cuando termina de descubrirse la línea del título que contiene D&A
    var ink = el.closest(".title-ink");
    var started = false;
    function go() { if (!started) { started = true; start(); } }
    if (ink) ink.addEventListener("animationend", go, { once: true });
    setTimeout(go, 1700);
  }

  /* ---------- Cotización: escenas tipo Apple (mapa → revisión con lupa → notificación de WhatsApp) ---------- */
  function initScenes() {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    Array.prototype.forEach.call(document.querySelectorAll("[data-scenes]"), function (root) {
      var scenes = Array.prototype.slice.call(root.querySelectorAll(".scene"));
      var steps = Array.prototype.slice.call(root.querySelectorAll("[data-scene-to]"));
      var timers = [], raf = 0, current = -1;

      function ease(k) { return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; }
      function tween(ms, fn, done) {
        var t0 = performance.now();
        cancelAnimationFrame(raf);
        (function tick(now) {
          var k = Math.min((now - t0) / ms, 1);
          fn(ease(k));
          if (k < 1) raf = requestAnimationFrame(tick); else if (done) done();
        })(t0);
      }

      // Escena 1: el carrito recorre la ruta hasta el taller
      var map = root.querySelector('[data-scene="map"]');
      var route = map.querySelector("[data-route]"), car = map.querySelector("[data-car]");
      var L = route.getTotalLength();
      function carAt(k) {
        var p = route.getPointAtLength(L * k), q = route.getPointAtLength(Math.min(L, L * k + 1));
        var a = Math.atan2(q.y - p.y, q.x - p.x) * 180 / Math.PI + 90;
        if (k >= 1) { var b = route.getPointAtLength(L - 1); a = Math.atan2(p.y - b.y, p.x - b.x) * 180 / Math.PI + 90; }
        car.setAttribute("transform", "translate(" + p.x.toFixed(1) + " " + p.y.toFixed(1) + ") rotate(" + a.toFixed(1) + ")");
      }
      // Escena 2: la lupa recorre el carro y marca lo revisado
      var scan = root.querySelector('[data-scene="scan"]');
      var lens = scan.querySelector("[data-lens]"), clip = scan.querySelector("[data-lens-clip]");
      var zoom = scan.querySelector("[data-lens-zoom]"), ring = scan.querySelector(".scan-chip__ring");
      var checks = Array.prototype.slice.call(scan.querySelectorAll("[data-check]"));
      function lensAt(k) {
        var x = 70 + 270 * k, y = 118 + Math.sin(k * Math.PI * 2.5) * 22;
        lens.setAttribute("transform", "translate(" + x.toFixed(1) + " " + y.toFixed(1) + ")");
        lens.firstElementChild.setAttribute("transform", "translate(" + (-x).toFixed(1) + " " + (-y).toFixed(1) + ")");
        clip.setAttribute("cx", x.toFixed(1)); clip.setAttribute("cy", y.toFixed(1));
        zoom.setAttribute("transform", "translate(" + x.toFixed(1) + " " + y.toFixed(1) + ") scale(1.7) translate(" + (-x).toFixed(1) + " " + (-y).toFixed(1) + ")");
        ring.style.setProperty("--p", k.toFixed(3));
        checks.forEach(function (c) { c.classList.toggle("is-on", x >= +c.getAttribute("data-check")); });
      }
      var wa = root.querySelector('[data-scene="wa"]');

      var plays = [
        function (fast) {
          map.classList.remove("is-arrived");
          if (fast) { carAt(1); map.classList.add("is-arrived"); return; }
          carAt(0);
          tween(2600, carAt, function () { map.classList.add("is-arrived"); });
        },
        function (fast) {
          if (fast) { lensAt(1); return; }
          lensAt(0);
          tween(3300, lensAt);
        },
        function (fast) {
          wa.classList.remove("is-in");
          if (fast) { wa.classList.add("is-in"); return; }
          void wa.offsetWidth;
          wa.classList.add("is-in");
        }
      ];

      function stop() {
        timers.forEach(clearTimeout); timers = [];
        cancelAnimationFrame(raf);
      }
      function show(i, chain) {
        current = i;
        scenes.forEach(function (s, j) { s.classList.toggle("is-active", j === i); });
        steps.forEach(function (b, j) {
          b.setAttribute("aria-current", j === i ? "true" : "false");
          var bar = b.querySelector(".scenes__bar i");
          bar.style.transition = "none";
          bar.style.transform = "scaleX(" + (j < i ? 1 : 0) + ")";
        });
        plays[i](reduce);
        var ms = +scenes[i].getAttribute("data-ms");
        var bar = steps[i] && steps[i].querySelector(".scenes__bar i");
        if (bar && !reduce) {
          void bar.offsetWidth;
          bar.style.transition = "transform " + ms + "ms linear";
          bar.style.transform = "scaleX(1)";
        } else if (bar) { bar.style.transform = "scaleX(1)"; }
        if (chain && i < scenes.length - 1 && !reduce) timers.push(setTimeout(function () { show(i + 1, true); }, ms));
      }

      steps.forEach(function (b, i) {
        b.addEventListener("click", function () { stop(); show(i, false); });
      });
      // Estado de partida (sin JS se ve el carro ya en el taller)
      carAt(0); lensAt(0);
      watchShown(root, function () { stop(); show(0, true); }, function () { stop(); });
    });
  }

  /* ---------- Portafolios de trabajos reales en el panel del recorrido ---------- */
  function initFolios() {
    var dataEl = document.getElementById("gallery-data");
    var roots = document.querySelectorAll("[data-folio]");
    if (!dataEl || !roots.length) return;
    var data;
    try { data = JSON.parse(dataEl.textContent); } catch (err) { return; }
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Las fotos del panel viven en capas con opacidad 0: el navegador puede posponer su decodificación
    // hasta que se muestran y se ven tarde o borrosas. Se cargan y decodifican antes de llegar al recorrido.
    var panel = document.querySelector(".journey__panel");
    if (panel && "IntersectionObserver" in window) {
      var pre = new IntersectionObserver(function (entries) {
        if (!entries.some(function (e) { return e.isIntersecting; })) return;
        pre.disconnect();
        Array.prototype.forEach.call(panel.querySelectorAll("img"), function (im) {
          im.loading = "eager";
          if (im.decode) im.decode().catch(function () {});
        });
      }, { rootMargin: "800px 0px" });
      pre.observe(panel);
    }

    Array.prototype.forEach.call(roots, function (root) {
      var gal = data[root.getAttribute("data-folio")];
      if (!gal || !gal.fotos.length) return;
      var fotos = gal.fotos, n = fotos.length, index = 0, token = 0;
      var main = root.querySelector(".folio__main");
      var img = root.querySelector("[data-folio-img]");
      var num = root.querySelector("[data-folio-i]");
      var pie = root.querySelector("[data-folio-pie]");
      var strip = root.querySelector(".folio__strip");
      var thumbs = Array.prototype.slice.call(root.querySelectorAll("[data-folio-to]"));

      function pad(k) { return (k < 10 ? "0" : "") + k; }

      function show(i) {
        index = (i + n) % n;
        var f = fotos[index], mine = ++token;
        main.setAttribute("data-index", index);
        main.href = f.src;
        main.setAttribute("aria-label", "Ampliar foto " + (index + 1) + " de " + n + ": " + f.alt);
        num.textContent = pad(index + 1);
        pie.textContent = f.pie || "";
        thumbs.forEach(function (t, j) { t.setAttribute("aria-current", j === index ? "true" : "false"); });
        var t = thumbs[index];
        if (t && strip) {
          strip.scrollTo({ left: t.offsetLeft - (strip.clientWidth - t.offsetWidth) / 2, behavior: reduce ? "auto" : "smooth" });
        }
        // Precarga y cambia con un fundido corto para que no parpadee
        img.classList.add("is-swapping");
        var pre = new Image();
        pre.sizes = img.sizes;
        pre.srcset = f.srcset;
        pre.src = f.src;
        function swap() {
          if (mine !== token) return;
          img.srcset = f.srcset;
          img.src = f.src;
          img.width = f.w; img.height = f.h;
          img.alt = f.alt;
          img.classList.remove("is-swapping");
        }
        if (pre.decode) pre.decode().then(swap, swap); else pre.onload = pre.onerror = swap;
      }

      thumbs.forEach(function (t, j) { t.addEventListener("click", function () { show(j); }); });
      root.querySelector("[data-folio-prev]").addEventListener("click", function () { show(index - 1); });
      root.querySelector("[data-folio-next]").addEventListener("click", function () { show(index + 1); });
      root.addEventListener("keydown", function (e) {
        if (e.key === "ArrowLeft") { e.preventDefault(); show(index - 1); }
        else if (e.key === "ArrowRight") { e.preventDefault(); show(index + 1); }
      });
    });
  }

  /* ---------- Proceso: pestañas Qualitas / particular con línea de tiempo ---------- */
  function initFlows() {
    var root = document.querySelector("[data-flows]");
    if (!root) return;
    var tabs = Array.prototype.slice.call(root.querySelectorAll("[role=tab]"));
    var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute("aria-controls")); });
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    root.classList.add("is-enhanced");

    function play(panel) {
      var tl = panel.querySelector(".timeline");
      if (!tl || reduce) return;
      Array.prototype.forEach.call(tl.children, function (li, i) { li.style.setProperty("--i", i); });
      tl.classList.remove("is-in");
      tl.classList.add("will-reveal");
      void tl.offsetWidth; // reinicia la secuencia al cambiar de pestaña
      tl.classList.add("is-in");
    }
    function select(i, focus) {
      tabs.forEach(function (t, j) {
        var on = j === i;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        panels[j].hidden = !on;
      });
      if (focus) tabs[i].focus();
      play(panels[i]);
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(i, false); });
      t.addEventListener("keydown", function (e) {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          e.preventDefault();
          select((i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length, true);
        }
        if (e.key === "Home") { e.preventDefault(); select(0, true); }
        if (e.key === "End") { e.preventDefault(); select(tabs.length - 1, true); }
      });
    });

    // Primera vez: la línea se dibuja al llegar a la sección
    tabs.forEach(function (t, j) { panels[j].hidden = j !== 0; });
    if (reduce || !("IntersectionObserver" in window)) return;
    var first = panels[0].querySelector(".timeline");
    first.classList.add("will-reveal");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          var open = panels.filter(function (p) { return !p.hidden; })[0];
          play(open);
          io.disconnect();
        }
      });
    }, { threshold: 0.3 });
    io.observe(root);
  }

  /* ---------- Encuadre de fotos (data-foco = object-position) ---------- */
  function initFoco() {
    document.querySelectorAll("img[data-foco]").forEach(function (img) {
      img.style.objectPosition = img.getAttribute("data-foco");
    });
  }

  /* ---------- Galería por servicio ---------- */
  function initGallery() {
    var dataEl = document.getElementById("gallery-data");
    var dlg = document.getElementById("lightbox");
    if (!dataEl || !dlg || typeof dlg.showModal !== "function") return;
    var data;
    try { data = JSON.parse(dataEl.textContent); } catch (err) { return; }
    var img = dlg.querySelector("[data-lb-img]");
    var title = dlg.querySelector("[data-lb-title]");
    var count = dlg.querySelector("[data-lb-count]");
    var pie = dlg.querySelector("[data-lb-pie]");
    var strip = dlg.querySelector("[data-lb-strip]");
    var prevBtn = dlg.querySelector("[data-lb-prev]");
    var nextBtn = dlg.querySelector("[data-lb-next]");
    var gal = null, index = 0, opener = null;

    function smallest(srcset) { return (srcset.split(",")[0] || "").trim().split(" ")[0]; }

    function show(i) {
      var fotos = gal.fotos;
      index = (i + fotos.length) % fotos.length;
      var f = fotos[index];
      img.srcset = f.srcset;
      img.sizes = "(min-width: 1024px) 80vw, 100vw";
      img.src = f.src;
      img.width = f.w; img.height = f.h;
      img.alt = f.alt;
      var texto = [f.pie || "", f.ilu ? "Imagen ilustrativa, no es un trabajo del taller." : ""].filter(Boolean).join(" ");
      pie.textContent = texto;
      pie.hidden = !texto;
      count.textContent = "Foto " + (index + 1) + " de " + fotos.length;
      strip.querySelectorAll("button").forEach(function (b, j) {
        b.setAttribute("aria-current", j === index ? "true" : "false");
      });
      var single = fotos.length < 2;
      prevBtn.hidden = single; nextBtn.hidden = single;
    }

    function open(id, i, from) {
      gal = data[id];
      if (!gal || !gal.fotos.length) return;
      opener = from;
      title.textContent = gal.titulo;
      strip.textContent = "";
      gal.fotos.forEach(function (f, j) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "lightbox__thumb";
        b.setAttribute("aria-label", "Ver foto " + (j + 1));
        var t = document.createElement("img");
        t.src = smallest(f.srcset); t.alt = ""; t.loading = "lazy";
        b.appendChild(t);
        b.addEventListener("click", function () { show(j); });
        strip.appendChild(b);
      });
      strip.hidden = gal.fotos.length < 2;
      show(i);
      dlg.showModal();
    }

    document.addEventListener("click", function (e) {
      var a = e.target.closest("[data-gal]");
      if (!a) return;
      e.preventDefault();
      open(a.getAttribute("data-gal"), parseInt(a.getAttribute("data-index"), 10) || 0, a);
    });
    prevBtn.addEventListener("click", function () { show(index - 1); });
    nextBtn.addEventListener("click", function () { show(index + 1); });
    dlg.querySelector("[data-lb-close]").addEventListener("click", function () { dlg.close(); });
    dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener("keydown", function (e) {
      if (!gal) return;
      if (e.key === "ArrowLeft") show(index - 1);
      if (e.key === "ArrowRight") show(index + 1);
    });
    var touchX = null;
    img.addEventListener("pointerdown", function (e) { touchX = e.clientX; });
    img.addEventListener("pointerup", function (e) {
      if (touchX === null) return;
      var dx = e.clientX - touchX; touchX = null;
      if (Math.abs(dx) > 40) show(index + (dx < 0 ? 1 : -1));
    });
    dlg.addEventListener("close", function () {
      img.removeAttribute("srcset"); img.removeAttribute("src");
      if (opener && document.contains(opener)) opener.focus();
    });
  }

  /* ---------- Carrusel de reseñas ---------- */
  function initCarousel() {
    var root = document.getElementById("reviews-carousel");
    if (!root) return;
    var track = root.querySelector(".carousel__track");
    var slides = Array.prototype.slice.call(track.children);
    if (slides.length < 2) return;
    var current = root.querySelector("[data-carousel-current]");
    var toggle = root.querySelector("[data-carousel-toggle]");
    var bar = root.querySelector("[data-carousel-bar]");
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var DELAY = 7000;
    // Siempre avanza solo; con movimiento reducido cambia sin deslizar.
    var index = 0, timer = null, playing = true, hovered = false;

    root.classList.add("is-enhanced");
    if (reduce) root.classList.add("is-reduced");

    function go(i, user) {
      index = (i + slides.length) % slides.length;
      track.style.transform = "translateX(" + (-100 * index) + "%)";
      slides.forEach(function (s, j) {
        var on = j === index;
        s.setAttribute("aria-hidden", on ? "false" : "true");
        if ("inert" in s) s.inert = !on;
      });
      current.textContent = index + 1;
      track.setAttribute("aria-live", user ? "polite" : "off");
      restart();
    }
    function restart() {
      clearTimeout(timer);
      bar.classList.remove("is-running");
      void bar.offsetWidth; // reinicia la animación de la barra
      if (playing && !hovered && !document.hidden) {
        bar.style.animationDuration = DELAY + "ms";
        bar.classList.add("is-running");
        timer = setTimeout(function () { go(index + 1, false); }, DELAY);
      }
    }
    function setPlaying(p) {
      playing = p;
      toggle.textContent = p ? "Pausar" : "Reproducir";
      toggle.setAttribute("aria-label", p ? "Pausar el carrusel" : "Reproducir el carrusel");
      restart();
    }

    toggle.addEventListener("click", function () { setPlaying(!playing); });
    root.addEventListener("mouseenter", function () { hovered = true; restart(); });
    root.addEventListener("mouseleave", function () { hovered = false; restart(); });
    root.addEventListener("focusin", function () { hovered = true; restart(); });
    root.addEventListener("focusout", function (e) {
      if (!root.contains(e.relatedTarget)) { hovered = false; restart(); }
    });
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") go(index - 1, true);
      if (e.key === "ArrowRight") go(index + 1, true);
    });
    document.addEventListener("visibilitychange", restart);
    var startX = null;
    track.addEventListener("pointerdown", function (e) { startX = e.clientX; });
    track.addEventListener("pointerup", function (e) {
      if (startX === null) return;
      var dx = e.clientX - startX; startX = null;
      if (Math.abs(dx) > 40) go(index + (dx < 0 ? 1 : -1), true);
    });

    setPlaying(playing);
    go(0, false);
  }

  /* ---------- Mapa bajo demanda ---------- */
  function initMap() {
    var btn = document.getElementById("load-map");
    var box = document.getElementById("map");
    if (!btn || !box) return;
    btn.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = box.getAttribute("data-embed");
      f.title = box.getAttribute("data-title");
      f.loading = "lazy";
      f.referrerPolicy = "no-referrer-when-downgrade";
      f.setAttribute("allowfullscreen", "");
      box.appendChild(f);
      var ph = box.querySelector(".map__ph");
      if (ph) ph.hidden = true;
    });
  }

  /* ---------- Formulario: prepara un mensaje de WhatsApp ---------- */
  function initForm() {
    var form = document.getElementById("quote-form");
    if (!form) return;
    var waNumber = form.getAttribute("data-wa");
    var submitBtn = document.getElementById("form-submit");
    if (submitBtn) submitBtn.disabled = false; // la acción depende de JavaScript: se habilita al iniciar
    var $ = function (id) { return document.getElementById(id); };
    var status = $("form-status");
    var done = $("form-done");
    var mail = form.getAttribute("data-mail");
    var help = $("form-help");

    // Canal de envío: WhatsApp (por defecto) o correo; el botón y la ayuda dicen exactamente qué pasará
    function canal() {
      var c = form.querySelector('input[name="canal"]:checked');
      return c && c.value === "correo" && mail ? "correo" : "whatsapp";
    }
    function syncCanal() {
      var porCorreo = canal() === "correo";
      submitBtn.textContent = porCorreo ? "Continuar en correo" : "Continuar en WhatsApp";
      if (help) help.textContent = porCorreo
        ? "Se abre tu programa de correo con el mensaje listo para " + mail + "; revísalo y pulsa Enviar. Las fotos las adjuntas ahí."
        : "Se abre WhatsApp con tu mensaje listo; revísalo y pulsa Enviar. Las fotos las adjuntas ahí.";
      done.hidden = true;
    }
    form.querySelectorAll('input[name="canal"]').forEach(function (r) { r.addEventListener("change", syncCanal); });

    function setError(el, msg) {
      var err = $(el.id + "-err");
      err.textContent = msg;
      err.hidden = false;
      el.setAttribute("aria-invalid", "true");
      addDescribed(el, err.id);
    }
    function clearError(el) {
      var err = $(el.id + "-err");
      if (err) { err.textContent = ""; err.hidden = true; removeDescribed(el, err.id); }
      el.removeAttribute("aria-invalid");
    }
    function addDescribed(el, id) {
      var cur = (el.getAttribute("aria-describedby") || "").split(" ").filter(Boolean);
      if (cur.indexOf(id) < 0) cur.unshift(id);
      el.setAttribute("aria-describedby", cur.join(" "));
    }
    function removeDescribed(el, id) {
      var cur = (el.getAttribute("aria-describedby") || "").split(" ").filter(function (x) { return x && x !== id; });
      if (cur.length) el.setAttribute("aria-describedby", cur.join(" ")); else el.removeAttribute("aria-describedby");
    }

    var rules = {
      nombre: function (v) { return v.length < 2 ? "Escribe tu nombre." : ""; },
      servicio: function (v) { return v ? "" : "Elige el servicio que te interesa."; },
      descripcion: function (v) { return v.length < 10 ? "Describe en pocas palabras lo que necesita tu vehículo (mínimo 10 caracteres)." : ""; }
    };

    function validateField(id) {
      var el = $(id);
      var msg = rules[id](el.value.trim());
      if (msg) setError(el, msg); else clearError(el);
      return !msg;
    }
    Object.keys(rules).forEach(function (id) {
      var el = $(id);
      el.addEventListener("blur", function () { if (el.value.trim() || el.getAttribute("aria-invalid")) validateField(id); });
      el.addEventListener("input", function () { if (el.getAttribute("aria-invalid") === "true") validateField(id); });
      el.addEventListener("change", function () { if (el.getAttribute("aria-invalid") === "true") validateField(id); });
    });

    function buildMessage() {
      var lines = ["Hola, quiero agendar una evaluación para cotizar la reparación de mi vehículo."];
      lines.push("Nombre: " + $("nombre").value.trim());
      lines.push("Servicio: " + $("servicio").selectedOptions[0].text);
      var v = $("vehiculo").value.trim();
      if (v) lines.push("Vehículo: " + v);
      lines.push("Requerimiento: " + $("descripcion").value.trim());
      return lines.join("\n");
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var ids = ["nombre", "servicio", "descripcion"];
      var firstBad = null;
      ids.forEach(function (id) {
        if (!validateField(id) && !firstBad) firstBad = $(id);
      });
      if (firstBad) {
        status.textContent = "Revisa los campos marcados.";
        done.hidden = true;
        firstBad.focus();
        return;
      }
      status.textContent = "";
      var msg = buildMessage();
      var porCorreo = canal() === "correo";
      var url = porCorreo
        ? "mailto:" + mail + "?subject=" + encodeURIComponent("Solicitud de evaluación - " + $("servicio").selectedOptions[0].text) +
          "&body=" + encodeURIComponent(msg)
        : "https://wa.me/" + waNumber + "?text=" + encodeURIComponent(msg);
      var medio = porCorreo ? "tu correo" : "WhatsApp";
      // Abre el canal con un enlace real (no depende de window.open); WhatsApp en otra pestaña
      var a = document.createElement("a");
      a.href = url;
      if (!porCorreo) { a.target = "_blank"; a.rel = "noopener"; }
      document.body.appendChild(a); a.click(); a.remove();
      // Aviso breve: no afirma que el taller recibió nada; los datos del formulario se conservan
      done.textContent = "Abrimos " + medio + " con tu mensaje: revísalo y pulsa Enviar. ¿No se abrió? ";
      var again = document.createElement("a");
      again.href = url;
      if (!porCorreo) { again.target = "_blank"; again.rel = "noopener"; }
      again.textContent = porCorreo ? "Abrir correo" : "Abrir WhatsApp";
      done.appendChild(again);
      if (porCorreo) done.appendChild(document.createTextNode(" o escribe directo a " + mail + "."));
      done.hidden = false;
    });

    document.querySelectorAll("[data-service]").forEach(function (a) {
      a.addEventListener("click", function () {
        var want = a.getAttribute("data-service");
        var sel = $("servicio");
        for (var i = 0; i < sel.options.length; i++) {
          if (sel.options[i].value === want) { sel.selectedIndex = i; clearError(sel); break; }
        }
      });
    });

  }

  onReady(function () {
    initMenu();
    initHours();
    initHeroTilt();
    initJourney();
    initFolios();
    initChats();
    initScenes();
    initSpray();
    initFoco();
    initGallery();
    initCarousel();
    initFlows();
    initMap();
    initForm();
  });
})();
