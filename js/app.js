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
    }, { rootMargin: "-48% 0px -48% 0px", threshold: 0 });
    stages.forEach(function (s) { io.observe(s); });
    // Hover o foco dentro de una etapa también la activa (teclado y ratón)
    stages.forEach(function (s, i) {
      s.addEventListener("focusin", function () { activate(i); });
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
      var url = "https://wa.me/" + waNumber + "?text=" + encodeURIComponent(msg);
      // Abre WhatsApp en otra pestaña con un enlace real (no depende de window.open)
      var a = document.createElement("a");
      a.href = url; a.target = "_blank"; a.rel = "noopener";
      document.body.appendChild(a); a.click(); a.remove();
      // Aviso breve: no afirma que el taller recibió nada; los datos del formulario se conservan
      done.textContent = "Abrimos WhatsApp con tu mensaje: revísalo y pulsa Enviar. ¿No se abrió? ";
      var again = document.createElement("a");
      again.href = url; again.target = "_blank"; again.rel = "noopener";
      again.textContent = "Abrir WhatsApp";
      done.appendChild(again);
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
    initFoco();
    initGallery();
    initCarousel();
    initFlows();
    initMap();
    initForm();
  });
})();
