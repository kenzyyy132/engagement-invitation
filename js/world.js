/*
 * The illustrated world around the invitation: petals and gold dust, swallows,
 * a butterfly, growing vines, parallax depth and small tap interactions.
 *
 * Everything here is decorative. It sleeps when its scene is off-screen or the
 * tab is hidden, and does nothing at all under prefers-reduced-motion.
 * main.js calls InvitationWorld.start() when the doors open.
 */
(function () {
  "use strict";

  var root = document.documentElement;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var started = false;
  var rand = function (a, b) { return a + Math.random() * (b - a); };
  var visible = !document.hidden;

  document.addEventListener("visibilitychange", function () {
    visible = !document.hidden;
    root.classList.toggle("is-page-hidden", !visible);
    if (visible) loops.forEach(function (l) { l.wake(); });
  });

  /* A tiny scheduler: each loop runs only while it wants to and the page is visible. */
  var loops = [];
  function makeLoop(step, isActive) {
    var frame = 0, last = 0;
    function tick(now) {
      frame = 0;
      if (!visible || !isActive()) return;
      var dt = Math.min(0.05, (now - (last || now)) / 1000);
      last = now;
      step(dt, now / 1000);
      frame = requestAnimationFrame(tick);
    }
    var loop = { wake: function () { if (!frame && visible && isActive()) { last = 0; frame = requestAnimationFrame(tick); } } };
    loops.push(loop);
    return loop;
  }

  function onScreen(el, cb) {
    if (!("IntersectionObserver" in window)) { cb(true); return; }
    new IntersectionObserver(function (e) { cb(e[0].isIntersecting); }, { rootMargin: "80px 0px" }).observe(el);
  }

  /* ── Petals & gold dust ───────────────────────────────────── */

  var ambient = (function () {
    var canvas = document.getElementById("ambient");
    if (!canvas || reduced) return { burst: function () {} };
    var ctx = canvas.getContext("2d");
    var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    var W = 0, H = 0;
    var petals = [], dust = [];
    var PETAL_COLORS = ["#f3b4c2", "#f6c9d2", "#e9a3b4", "#f8dde3", "#ead9c3"];
    var lastScroll = window.scrollY;

    function resize() {
      W = window.innerWidth; H = window.innerHeight;
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function petal(x, y, burst) {
      return {
        x: x, y: y,
        s: rand(4.5, 9),
        vy: burst ? rand(-60, -10) : rand(16, 34),
        vx: burst ? rand(-70, 70) : rand(-6, 10),
        sway: rand(14, 34), swayF: rand(.5, 1.1), ph: rand(0, 6.28),
        rot: rand(0, 6.28), spin: rand(-1.4, 1.4),
        flip: rand(0, 6.28), flipF: rand(1.2, 2.6),
        depth: rand(.5, 1.2),
        c: PETAL_COLORS[(Math.random() * PETAL_COLORS.length) | 0],
        life: burst ? rand(3.5, 5.5) : Infinity,
        a: burst ? 1 : rand(.55, .9),
      };
    }
    function speck() {
      return { x: rand(0, W), y: rand(0, H), r: rand(.6, 1.7), vy: rand(-9, -3), vx: rand(-4, 4), tw: rand(0, 6.28), twF: rand(.6, 1.8), glow: Math.random() < .18 };
    }
    function populate() {
      var n = W < 600 ? 9 : 16, m = W < 600 ? 14 : 26;
      petals = petals.filter(function (p) { return p.life !== Infinity; });
      for (var i = 0; i < n; i++) petals.push(petal(rand(0, W), rand(-H, H)));
      dust = [];
      for (var j = 0; j < m; j++) dust.push(speck());
    }

    function drawPetal(p) {
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.scale(Math.max(.18, Math.abs(Math.cos(p.flip))), 1);
      ctx.globalAlpha = p.a;
      ctx.fillStyle = p.c;
      var s = p.s;
      ctx.beginPath();
      ctx.moveTo(0, -s);
      ctx.bezierCurveTo(s * .9, -s * .55, s * .6, s * .9, 0, s);
      ctx.bezierCurveTo(-s * .6, s * .9, -s * .9, -s * .55, 0, -s);
      ctx.fill();
      ctx.globalAlpha = p.a * .35;
      ctx.strokeStyle = "#c97f93";
      ctx.lineWidth = .6;
      ctx.beginPath(); ctx.moveTo(0, -s * .7); ctx.lineTo(0, s * .7); ctx.stroke();
      ctx.restore();
    }

    function step(dt, t) {
      var scrolled = window.scrollY - lastScroll;
      lastScroll = window.scrollY;
      ctx.clearRect(0, 0, W, H);

      for (var i = petals.length - 1; i >= 0; i--) {
        var p = petals[i];
        p.vx *= p.life === Infinity ? 1 : .985;
        p.y += (p.vy * p.depth) * dt - scrolled * .25 * p.depth;   // drift against the scroll a little
        p.x += (p.vx + Math.sin(t * p.swayF + p.ph) * p.sway) * dt;
        p.rot += p.spin * dt;
        p.flip += p.flipF * dt;
        if (p.life !== Infinity) {
          p.vy += 40 * dt;           // burst petals arc, then fall
          p.life -= dt;
          if (p.life < 1) p.a = Math.max(0, p.life);
          if (p.life <= 0) { petals.splice(i, 1); continue; }
        } else if (p.y > H + 20 || p.y < -H * 1.2 || p.x < -40 || p.x > W + 40) {
          var fresh = petal(rand(-20, W + 20), rand(-60, -20));
          petals[i] = fresh;
        }
        drawPetal(p);
      }

      for (var j = 0; j < dust.length; j++) {
        var d = dust[j];
        d.y += d.vy * dt - scrolled * .1;
        d.x += (d.vx + Math.sin(t * .7 + d.tw) * 3) * dt;
        if (d.y < -10) { d.y = H + 10; d.x = rand(0, W); }
        if (d.y > H + 10) d.y = -10;
        var a = .25 + .55 * (0.5 + 0.5 * Math.sin(t * d.twF + d.tw));
        if (d.glow) {
          ctx.globalAlpha = a * .25;
          ctx.fillStyle = "#f3d58f";
          ctx.beginPath(); ctx.arc(d.x, d.y, d.r * 4, 0, 6.283); ctx.fill();
        }
        ctx.globalAlpha = a;
        ctx.fillStyle = "#d6b46a";
        ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, 6.283); ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    resize(); populate();
    var resizeTimer;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () { resize(); populate(); }, 200);
    });
    var loop = makeLoop(step, function () { return true; });
    loop.wake();

    return {
      burst: function (x, y, n) {
        for (var k = 0; k < (n || 8); k++) petals.push(petal(x + rand(-10, 10), y + rand(-10, 10), true));
        if (petals.length > 80) petals.splice(0, petals.length - 80);
        loop.wake();
      },
    };
  })();

  /* ── Swallows ─────────────────────────────────────────────── */

  var BIRD = '<svg class="bird" viewBox="0 0 60 42" aria-hidden="true">' +
    '<g class="bird__wing bird__wing--far"><path d="M30 21C26 10 18 4 6 3C14 9 20 15 25 22Z" fill="#9aaa9b"/></g>' +
    '<path d="M24 21C32 19 42 18 48 20C52 21 54 23 54 24C50 26 44 28 36 28C28 28 20 29 14 30L1 37L10 29L2 27L14 26C18 24 21 22 24 21Z" fill="#37443b"/>' +
    '<path d="M27 25.5C34 27.5 44 27 50 24.5C46 28 38 29.5 30 29Z" fill="#efe6d6"/>' +
    '<path d="M47.5 22.5C50.5 22 53 23 54 24.2C52 25.2 49.5 25 47.5 24Z" fill="#d98e8e"/>' +
    '<circle cx="49" cy="21" r="4.6" fill="#37443b"/><circle cx="50.7" cy="20.2" r=".9" fill="#f6efe0"/>' +
    '<path d="M53.3 20.4L58 21.3L53.3 22.6Z" fill="#b8955a"/>' +
    '<g class="bird__wing bird__wing--near"><path d="M30 21C24 8 14 1 0 1C10 8 18 16 24 24Z" fill="#5f7363"/>' +
    '<path d="M30 21C24 8 14 1 0 1" fill="none" stroke="#c9a764" stroke-width=".8" opacity=".75"/></g></svg>';

  function flock(container, plans) {
    var birds = plans.map(function (plan) {
      var wrap = document.createElement("div");
      wrap.innerHTML = BIRD;
      var el = wrap.firstChild;
      el.style.opacity = "0";
      el.style.width = "calc(" + plan.size + " * clamp(36px, 8.5vw, 60px))";
      container.appendChild(el);
      var b = { el: el, plan: plan, t: plan.offset, boost: 1, px: null, py: null, glide: false, fade: 0 };
      el.addEventListener("click", function () {
        b.boost = 2.8;
        el.classList.add("is-startled");
        setTimeout(function () { el.classList.remove("is-startled"); }, 1400);
      });
      return b;
    });
    var box = { w: 0, h: 0 };
    function measure() { box.w = container.clientWidth; box.h = container.clientHeight; }
    measure();
    window.addEventListener("resize", measure);

    var inView = false;
    onScreen(container, function (on) { inView = on; loop.wake(); });

    var loop = makeLoop(function (dt) {
      birds.forEach(function (b) {
        var p = b.plan;
        b.boost += (1 - b.boost) * Math.min(1, dt * .9);
        b.t += dt * p.speed * b.boost;
        var pos = p.path(b.t);
        var x = pos[0] * box.w, y = pos[1] * box.h;
        if (b.px !== null) {
          var vx = x - b.px, vy = y - b.py;
          var face = vx < 0 ? -1 : 1;
          var ang = Math.atan2(vy, Math.abs(vx) + 0.0001) * 180 / Math.PI;
          ang = Math.max(-32, Math.min(32, ang));
          var glide = vy > 0.25 * Math.abs(vx) + 0.05;
          if (glide !== b.glide) { b.glide = glide; b.el.classList.toggle("is-gliding", glide); }
          b.fade = Math.min(1, b.fade + dt * .6);
          b.el.style.opacity = String(b.fade * p.alpha);
          b.el.style.transform = "translate(" + x.toFixed(1) + "px," + y.toFixed(1) + "px) scale(" + face + ",1) rotate(" + ang.toFixed(1) + "deg)";
        }
        b.px = x; b.py = y;
      });
    }, function () { return inView && started; });

    return { start: function () { loop.wake(); } };
  }

  // Flight paths in container fractions (0–1). Lissajous curves give gentle, never-repeating-looking loops.
  var stagePlans = [
    { size: 1,   speed: .32, offset: 0,   alpha: .95, path: function (t) { return [.5 + .36 * Math.sin(t), .42 + .16 * Math.sin(2 * t + .6)]; } },
    { size: .8,  speed: .26, offset: 2.1, alpha: .9,  path: function (t) { return [.5 + .42 * Math.sin(t + 1.4), .3 + .12 * Math.sin(2 * t)]; } },
    { size: .65, speed: .38, offset: 4.4, alpha: .8,  path: function (t) { return [.48 + .3 * Math.cos(t), .5 + .14 * Math.sin(3 * t + 1)]; } },
    { size: .9,  speed: .22, offset: 1.2, alpha: .92, path: function (t) { return [.52 + .44 * Math.sin(t + 3), .24 + .1 * Math.cos(2 * t + .3)]; } },
    { size: .55, speed: .3,  offset: 5.6, alpha: .75, path: function (t) { return [.5 + .25 * Math.sin(t + 2.2), .62 + .08 * Math.sin(2 * t + 2)]; } },
  ];
  // closing: swallows lifting away across the sky, then circling back
  var closingPlans = [
    { size: .9,  speed: .09, offset: 0,   alpha: .9,  path: function (t) { var u = (t % 1); return [-.1 + 1.2 * u, .55 - .45 * u + .05 * Math.sin(u * 12)]; } },
    { size: .7,  speed: .08, offset: .35, alpha: .85, path: function (t) { var u = (t % 1); return [1.1 - 1.2 * u, .45 - .35 * u + .04 * Math.sin(u * 10 + 1)]; } },
    { size: .6,  speed: .1,  offset: .7,  alpha: .8,  path: function (t) { var u = (t % 1); return [-.1 + 1.2 * u, .3 - .2 * u + .05 * Math.sin(u * 14 + 2)]; } },
  ];

  var flocks = [];
  if (!reduced) {
    document.querySelectorAll("[data-birds]").forEach(function (el) {
      flocks.push(flock(el, el.dataset.birds === "closing" ? closingPlans : stagePlans));
    });
  }

  /* ── Butterfly over the venue card ────────────────────────── */

  function butterfly(zone) {
    var card = zone.parentElement.querySelector(".venue-card");
    if (!card) return null;
    var el = document.createElement("div");
    el.innerHTML = '<svg class="butterfly" viewBox="0 0 40 36" aria-hidden="true"><g class="butterfly__wing">' +
      '<path d="M20 18C14 6 4 2 2 8C0 14 8 18 20 19Z" fill="#f3b4c2"/><path d="M20 18C26 6 36 2 38 8C40 14 32 18 20 19Z" fill="#f3b4c2"/>' +
      '<path d="M20 19C12 22 6 30 10 32C14 34 18 26 20 20Z" fill="#e39aac"/><path d="M20 19C28 22 34 30 30 32C26 34 22 26 20 20Z" fill="#e39aac"/>' +
      '<path d="M20 18C14 10 8 7 5 9M20 18C26 10 32 7 35 9" fill="none" stroke="#c9a764" stroke-width=".7"/></g>' +
      '<path d="M20 11V28" stroke="#5a4a3a" stroke-width="1.8" stroke-linecap="round"/>' +
      '<path d="M20 11C19 7 17 5 15 4M20 11C21 7 23 5 25 4" fill="none" stroke="#5a4a3a" stroke-width=".7"/></svg>';
    var b = el.firstChild;
    zone.appendChild(b);
    var active = false, t = rand(0, 10);
    onScreen(zone, function (on) { active = on; if (on) loop.wake(); });
    var loop = makeLoop(function (dt) {
      t += dt;
      var zr = zone.getBoundingClientRect(), cr = card.getBoundingClientRect();
      var cx = cr.left - zr.left + cr.width * .72, cy = cr.top - zr.top + cr.height * .12;
      var x = cx + Math.sin(t * .45) * cr.width * .3 + Math.sin(t * 1.7) * 8;
      var y = cy + Math.sin(t * .9) * cr.height * .05 + Math.sin(t * 3.3) * 6;
      var tilt = Math.cos(t * .45) * 14;
      b.style.transform = "translate(" + x.toFixed(1) + "px," + y.toFixed(1) + "px) rotate(" + tilt.toFixed(1) + "deg)";
    }, function () { return active; });
    return loop;
  }
  if (!reduced) document.querySelectorAll("[data-butterfly]").forEach(butterfly);

  /* ── Vines growing beside the invitation card ─────────────── */

  function growVine(holder) {
    var NS = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 110 700");
    svg.setAttribute("preserveAspectRatio", "none");
    svg.innerHTML = '<defs><linearGradient id="vl-' + Math.random().toString(36).slice(2, 7) + '" x1="0" x2="1"><stop offset="0" stop-color="#5f765f"/><stop offset="1" stop-color="#b9c8b2"/></linearGradient></defs>';
    var gradId = svg.querySelector("linearGradient").id;
    var stem = document.createElementNS(NS, "path");
    stem.setAttribute("class", "vine__stem");
    stem.setAttribute("pathLength", "1");
    stem.setAttribute("d", "M60 700C20 620 100 560 60 480C20 400 100 340 60 260C26 190 92 122 64 40C60 26 54 16 46 8");
    svg.appendChild(stem);
    holder.appendChild(svg);
    var len = stem.getTotalLength();
    var n = 16;
    for (var i = 1; i < n; i++) {
      var at = (i / n) * len;
      var p = stem.getPointAtLength(at), q = stem.getPointAtLength(Math.min(len, at + 1));
      var tangent = Math.atan2(q.y - p.y, q.x - p.x) * 180 / Math.PI;
      var side = i % 2 ? 1 : -1;
      var g = document.createElementNS(NS, "g");
      g.setAttribute("transform", "translate(" + p.x.toFixed(1) + " " + p.y.toFixed(1) + ") rotate(" + (tangent + side * rand(45, 70)).toFixed(1) + ")");
      var leaf = document.createElementNS(NS, "path");
      leaf.setAttribute("class", "vine__leaf");
      if (i % 5 === 3) {
        leaf.setAttribute("d", "M0 0m-5 0a5 5 0 1 0 10 0a5 5 0 1 0-10 0");
        leaf.setAttribute("fill", "#f3b4c2");
      } else {
        var s = rand(.75, 1.15);
        leaf.setAttribute("d", "M0 0C" + 8 * s + " " + -7 * s + " " + 20 * s + " " + -7 * s + " " + 28 * s + " 0C" + 20 * s + " " + 7 * s + " " + 8 * s + " " + 7 * s + " 0 0Z");
        leaf.setAttribute("fill", "url(#" + gradId + ")");
      }
      leaf.style.transitionDelay = (0.3 + (i / n) * 2.8).toFixed(2) + "s";
      g.appendChild(leaf);
      svg.appendChild(g);
    }
    onScreen(holder, function (on) { if (on) holder.classList.add("is-grown"); });
  }
  document.querySelectorAll("[data-vine]").forEach(growVine);

  /* ── Parallax depth ───────────────────────────────────────── */

  var layers = reduced ? [] : Array.prototype.slice.call(document.querySelectorAll("[data-parallax]"));
  var parallaxQueued = false;
  function parallax() {
    parallaxQueued = false;
    var vh = window.innerHeight;
    layers.forEach(function (el) {
      var host = el.closest("section") || el.parentElement;
      var r = host.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) return;
      var offset = (r.top + r.height / 2 - vh / 2) * Number(el.dataset.parallax);
      el.style.translate = "0 " + offset.toFixed(1) + "px";
    });
  }
  if (layers.length) {
    window.addEventListener("scroll", function () {
      if (!parallaxQueued) { parallaxQueued = true; requestAnimationFrame(parallax); }
    }, { passive: true });
    parallax();
  }

  /* ── Small interactions ───────────────────────────────────── */

  function restart(el, cls, ms) {
    el.classList.remove(cls);
    void el.offsetWidth; // restart the CSS animation
    el.classList.add(cls);
    clearTimeout(el._t);
    el._t = setTimeout(function () { el.classList.remove(cls); }, ms);
  }
  document.querySelectorAll(".branch").forEach(function (b) {
    b.addEventListener("click", function (e) {
      restart(b, "is-rustling", 950);
      ambient.burst(e.clientX, e.clientY, 9);
    });
  });
  document.querySelectorAll("[data-swing]").forEach(function (l) {
    var swing = function () { restart(l, "is-swinging", 1850); };
    l.addEventListener("click", swing);
    l.addEventListener("mouseenter", swing);
  });

  /* ── Start (after the doors open) ─────────────────────────── */

  function start() {
    if (started) return;
    started = true;
    flocks.forEach(function (f) { f.start(); });
  }
  // If the animated mode never starts (main.js failed), let the world run anyway.
  setTimeout(function () { if (!root.classList.contains("js-ready")) start(); }, 4300);

  window.InvitationWorld = { start: start, burst: ambient.burst };
})();
