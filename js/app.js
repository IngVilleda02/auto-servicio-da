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

  /* ---------- Servicios: la vista previa sigue a la fila activa ---------- */
  function initServices() {
    var rows = document.querySelectorAll(".svc");
    var imgs = document.querySelectorAll(".svc-preview [data-for]");
    if (!rows.length || !imgs.length) return;
    function activate(row) {
      var id = row.getAttribute("data-svc");
      rows.forEach(function (r) { r.classList.toggle("is-active", r === row); });
      imgs.forEach(function (im) { im.classList.toggle("is-active", im.getAttribute("data-for") === id); });
    }
    rows.forEach(function (row) {
      row.addEventListener("mouseenter", function () { activate(row); });
      row.addEventListener("focusin", function () { activate(row); });
    });
  }

  /* ---------- Filtros y galería ---------- */
  function initProjects() {
    var grid = document.getElementById("projects");
    if (!grid) return;
    var chips = document.querySelectorAll("[data-filter]");
    var cards = Array.prototype.slice.call(grid.querySelectorAll(".project"));
    var live = document.getElementById("filter-live");
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var f = chip.getAttribute("data-filter");
        chips.forEach(function (c) { c.setAttribute("aria-pressed", c === chip ? "true" : "false"); });
        var n = 0;
        cards.forEach(function (card) {
          var show = f === "all" || card.getAttribute("data-cat") === f;
          card.hidden = !show;
          if (show) n++;
        });
        if (live) live.textContent = n + (n === 1 ? " trabajo mostrado" : " trabajos mostrados");
      });
    });

    var dlg = document.getElementById("lightbox");
    if (!dlg || typeof dlg.showModal !== "function") return;
    var img = dlg.querySelector("[data-lb-img]");
    var title = dlg.querySelector("[data-lb-title]");
    var cat = dlg.querySelector("[data-lb-cat]");
    var sit = dlg.querySelector("[data-lb-situacion]");
    var srv = dlg.querySelector("[data-lb-servicio]");
    var res = dlg.querySelector("[data-lb-resultado]");
    var current = null, opener = null;

    function visible() { return cards.filter(function (c) { return !c.hidden; }); }
    function render(card) {
      current = card;
      var t = card.querySelector(".project__open img");
      img.src = card.getAttribute("data-large");
      img.srcset = "";
      img.alt = t.alt;
      title.textContent = card.getAttribute("data-name");
      cat.textContent = card.getAttribute("data-cat");
      sit.textContent = card.getAttribute("data-situacion");
      srv.textContent = card.getAttribute("data-servicio");
      res.textContent = card.getAttribute("data-resultado");
    }
    function step(delta) {
      var list = visible();
      if (!list.length) return;
      var i = list.indexOf(current);
      render(list[(i + delta + list.length) % list.length]);
    }
    grid.addEventListener("click", function (e) {
      var btn = e.target.closest(".project__open");
      if (!btn) return;
      opener = btn;
      render(btn.closest(".project"));
      dlg.showModal();
    });
    dlg.querySelector("[data-lb-close]").addEventListener("click", function () { dlg.close(); });
    dlg.querySelector("[data-lb-prev]").addEventListener("click", function () { step(-1); });
    dlg.querySelector("[data-lb-next]").addEventListener("click", function () { step(1); });
    dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") step(-1);
      if (e.key === "ArrowRight") step(1);
    });
    dlg.addEventListener("close", function () {
      img.removeAttribute("src");
      if (opener && document.contains(opener)) opener.focus();
    });
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
    var $ = function (id) { return document.getElementById(id); };
    var status = $("form-status");
    var prepared = $("prepared");

    function medio() {
      var c = form.querySelector('input[name="medio"]:checked');
      return c ? c.value : "whatsapp";
    }

    function normalizePhone(v) {
      var d = String(v).replace(/\D/g, "");
      if (d.length === 12 && d.indexOf("52") === 0) d = d.slice(2);
      if (d.length === 13 && d.indexOf("521") === 0) d = d.slice(3);
      return d;
    }
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
      telefono: function (v) {
        return normalizePhone(v).length === 10 ? "" : "Escribe un teléfono de 10 dígitos, por ejemplo 427 123 4567.";
      },
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
      var m = medio();
      var lines = ["Hola, quiero solicitar una cotización."];
      lines.push("Nombre: " + $("nombre").value.trim());
      lines.push("Contacto preferido: " + (m === "whatsapp" ? "WhatsApp" : "llamada") + " al " + normalizePhone($("telefono").value));
      lines.push("Servicio: " + $("servicio").selectedOptions[0].text);
      var v = $("vehiculo").value.trim();
      if (v) lines.push("Vehículo: " + v);
      lines.push("Requerimiento: " + $("descripcion").value.trim());
      return lines.join("\n");
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var ids = ["nombre", "telefono", "servicio", "descripcion"];
      var firstBad = null;
      ids.forEach(function (id) {
        if (!validateField(id) && !firstBad) firstBad = $(id);
      });
      if (firstBad) {
        status.textContent = "Revisa los campos marcados.";
        prepared.hidden = true;
        firstBad.focus();
        return;
      }
      status.textContent = "";
      var msg = buildMessage();
      var url = "https://wa.me/" + waNumber + "?text=" + encodeURIComponent(msg);
      $("prepared-text").value = msg;
      var link = $("prepared-link");
      link.href = url;
      prepared.hidden = false;
      $("prepared-title").focus();
      try { window.open(url, "_blank", "noopener"); } catch (err) { /* el enlace explícito sigue disponible */ }
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

    var copy = $("prepared-copy");
    if (copy) copy.addEventListener("click", function () {
      var ta = $("prepared-text");
      function fallback() { ta.focus(); ta.select(); copy.textContent = "Texto seleccionado, cópialo"; }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(ta.value).then(function () { copy.textContent = "Mensaje copiado"; }, fallback);
      } else fallback();
    });
  }

  onReady(function () {
    initMenu();
    initHours();
    initServices();
    initProjects();
    initMap();
    initForm();
  });
})();
