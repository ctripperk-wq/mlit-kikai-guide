(function () {
  // ---- 共通: 正規化と言い換え ----
  var norm = function (s) { return (s || '').normalize('NFKC').toLowerCase(); };
  var SYN = [
    ['間隔', 'ピッチ'], ['ステンレス', 'sus'], ['保温', '断熱'], ['吊り', '吊', 'つり', '支持'],
    ['振れ止め', '振止め', 'ふれ止め'], ['勾配', 'こう配', '傾き'], ['塩ビ', 'vp', 'vu', '塩化ビニル'],
    ['フレキシブル', 'フレキ'], ['気密試験', '気密'], ['真空', 'バキューム'], ['ろう付け', 'ロウ付け', 'ろう付', 'ブレージング'],
    ['トラップ', '封水'], ['満水試験', '満水'], ['水圧試験', '水圧', '耐圧'], ['厚さ', '厚み', '肉厚'],
    ['板厚', '鉄板の厚さ'], ['スリーブ', '貫通'], ['ドレン', 'ドレーン', '結露水'], ['冷媒', 'フロン'],
    ['フランジ', 'ﾌﾗﾝｼﾞ'], ['防火区画', '防火'], ['埋設', '埋戻し', '土被り']
  ].map(function (g) { return g.map(norm); });
  var expand = function (t) {
    var out = [t];
    SYN.forEach(function (g) { if (g.indexOf(t) >= 0) g.forEach(function (x) { if (out.indexOf(x) < 0) out.push(x); }); });
    return out;
  };
  // 語句 → [[同義語...], ...]（AND）
  var parseQuery = function (q) {
    return norm(q).split(/[\s　]+/).filter(Boolean).map(expand);
  };
  var matches = function (text, groups) {
    return groups.every(function (g) { return g.some(function (t) { return text.indexOf(t) >= 0; }); });
  };
  var allTerms = function (groups) { return [].concat.apply([], groups).sort(function (a, b) { return b.length - a.length; }); };

  // ハイライト（正規化で文字数が変わらないテキストのみ）
  var markIn = function (root, terms) {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (c) {
      var v = c.nodeValue, nv = norm(v);
      if (v.length !== nv.length) return;
      var hits = [];
      terms.forEach(function (t) {
        var i = nv.indexOf(t);
        while (i >= 0) { hits.push([i, i + t.length]); i = nv.indexOf(t, i + t.length); }
      });
      if (!hits.length) return;
      hits.sort(function (a, b) { return a[0] - b[0]; });
      var frag = document.createDocumentFragment(), last = 0;
      hits.forEach(function (h) {
        if (h[0] < last) return;
        frag.appendChild(document.createTextNode(v.slice(last, h[0])));
        var m = document.createElement('mark'); m.textContent = v.slice(h[0], h[1]);
        frag.appendChild(m); last = h[1];
      });
      frag.appendChild(document.createTextNode(v.slice(last)));
      c.parentNode.replaceChild(frag, c);
    });
  };

  // ---- すべて開く／閉じる ----
  document.querySelectorAll('.tools button').forEach(function (b) {
    b.addEventListener('click', function () {
      var open = b.dataset.act === 'open';
      document.querySelectorAll('details.cl').forEach(function (d) { d.open = open; });
    });
  });

  // ---- アンカーで開く・強調 ----
  function openHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    var el = id && document.getElementById(id);
    if (!el) return;
    if (el.tagName === 'DETAILS') el.open = true;
    if (el.tagName !== 'SECTION') { el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); }
    setTimeout(function () { el.scrollIntoView({ block: 'start' }); }, 30);
  }
  window.addEventListener('hashchange', openHash);
  openHash();

  // ---- ページ内検索 ----
  var q = document.getElementById('q'), qn = document.getElementById('qn');
  if (q) {
    var items = Array.prototype.slice.call(document.querySelectorAll('div.q, details.cl, figure.zu'));
    items.forEach(function (el) { el._t = norm(el.textContent); });
    var saved = new Map();
    var clearMarks = function () {
      saved.forEach(function (h, el) { var o = el.open; el.innerHTML = h; if (el.tagName === 'DETAILS') el.open = o; });
      saved.clear();
    };
    var first = null;
    var run = function () {
      clearMarks();
      var groups = parseQuery(q.value), terms = allTerms(groups), hit = 0;
      first = null;
      items.forEach(function (el) {
        var ok = !groups.length || matches(el._t, groups);
        el.style.display = ok ? '' : 'none';
        if (groups.length && ok) {
          hit++; if (!first) first = el;
          if (el.tagName === 'DETAILS') el.open = true;
          saved.set(el, el.innerHTML); markIn(el, terms);
        }
      });
      document.querySelectorAll('section').forEach(function (s) {
        var vis = s.querySelector('div.q:not([style*="none"]), details.cl:not([style*="none"]), figure.zu:not([style*="none"])');
        s.style.display = (!groups.length || vis) ? '' : 'none';
      });
      document.querySelectorAll('.qcat').forEach(function (c) {
        c.style.display = (!groups.length || c.querySelector('div.q:not([style*="none"])')) ? '' : 'none';
      });
      document.querySelectorAll('h3.hen').forEach(function (h) {
        var n = h.nextElementSibling, vis = false;
        while (n && n.tagName === 'DETAILS') { if (n.style.display !== 'none') vis = true; n = n.nextElementSibling; }
        h.style.display = vis ? '' : 'none';
      });
      qn.innerHTML = groups.length ? (hit ? '<a href="#" id="qfirst">' + hit + '件 ↓</a>' : '0件') : '';
      document.querySelectorAll('.chip').forEach(function (c) { c.classList.toggle('on', norm(c.dataset.q) === norm(q.value.trim())); });
    };
    var t;
    q.addEventListener('input', function () { clearTimeout(t); t = setTimeout(run, 200); });
    qn.addEventListener('click', function (e) {
      if (e.target.id === 'qfirst' && first) { e.preventDefault(); first.scrollIntoView({ block: 'start' }); }
    });
    document.querySelectorAll('.chip').forEach(function (c) {
      c.addEventListener('click', function () {
        q.value = c.classList.contains('on') ? '' : c.dataset.q; run();
        if (q.value && first) first.scrollIntoView({ block: 'start' });
      });
    });
  }

  // ---- 全ページ横断検索（トップ） ----
  var gq = document.getElementById('gq'), gres = document.getElementById('gres'), gqn = document.getElementById('gqn');
  if (gq && window.SIDX) {
    var data = window.SIDX, esc = function (s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; };
    data.items.forEach(function (it) { it._t = norm(it.t); it._x = norm(it.x); });
    var ORDER = { '早見表': 0, '条文': 1, '標準図': 2 };
    var snippet = function (it, terms) {
      var x = it.x, nx = norm(x);
      if (x.length !== nx.length) return esc(x.slice(0, 110)) + (x.length > 110 ? '…' : '');
      var pos = -1;
      terms.forEach(function (t) { var i = nx.indexOf(t); if (i >= 0 && (pos < 0 || i < pos)) pos = i; });
      var s = Math.max(0, pos - 40), e = Math.min(x.length, s + 120);
      var part = x.slice(s, e), np = nx.slice(s, e), out = '', last = 0, hits = [];
      terms.forEach(function (t) { var i = np.indexOf(t); while (i >= 0) { hits.push([i, i + t.length]); i = np.indexOf(t, i + t.length); } });
      hits.sort(function (a, b) { return a[0] - b[0]; });
      hits.forEach(function (h) { if (h[0] < last) return; out += esc(part.slice(last, h[0])) + '<mark>' + esc(part.slice(h[0], h[1])) + '</mark>'; last = h[1]; });
      out += esc(part.slice(last));
      return (s > 0 ? '…' : '') + out + (e < x.length ? '…' : '');
    };
    var grun = function () {
      var groups = parseQuery(gq.value), terms = allTerms(groups);
      if (!groups.length) { gres.innerHTML = ''; gqn.textContent = ''; return; }
      var res = data.items.filter(function (it) { return matches(it._t + ' ' + it._x, groups); });
      res.forEach(function (it) { it._s = ORDER[it.k] * 10 + (matches(it._t, groups) ? 0 : 5); });
      res.sort(function (a, b) { return a._s - b._s; });
      gqn.textContent = res.length + '件';
      var shown = res.slice(0, 80);
      gres.innerHTML = shown.length ? shown.map(function (it) {
        var tags = it.w.map(function (w) { return '<span class="wtag h-' + w + '">' + esc(data.names[w]) + '</span>'; }).join('');
        return '<a class="res" href="' + it.h + '"><span class="rk k' + ORDER[it.k] + '">' + it.k + '</span>' + tags +
          '<b>' + esc(it.t) + '</b><span class="snip">' + snippet(it, terms) + '</span></a>';
      }).join('') + (res.length > 80 ? '<p class="note">上位80件を表示しています。語を追加して絞り込んでください。</p>' : '')
        : '<p class="note">見つかりませんでした。別の言い方や、短い語で試してください。</p>';
    };
    var gt;
    gq.addEventListener('input', function () { clearTimeout(gt); gt = setTimeout(grun, 150); });
    document.querySelectorAll('.gchips .chip').forEach(function (c) {
      c.addEventListener('click', function () {
        var on = c.classList.contains('on');
        document.querySelectorAll('.gchips .chip').forEach(function (x) { x.classList.remove('on'); });
        gq.value = on ? '' : c.dataset.q; if (!on) c.classList.add('on'); grun();
      });
    });
  }

  // ---- ライトボックス（段階ズーム・ダブルタップ） ----
  var lb = document.getElementById('lb');
  if (lb && lb.showModal) {
    var img = document.getElementById('lbimg'), cap = document.getElementById('lbcap'),
        box = lb.querySelector('.lbimg'), op = document.getElementById('lbopen'),
        zl = document.getElementById('lbz'), LV = [1, 1.5, 2, 3, 4], zi = 0;
    var setZoom = function (i, cx, cy) {
      var oldW = img.clientWidth || 1;
      zi = Math.max(0, Math.min(LV.length - 1, i));
      img.style.width = (LV[zi] * 100) + '%';
      img.style.maxWidth = zi ? 'none' : '100%';
      zl.textContent = Math.round(LV[zi] * 100) + '%';
      if (cx != null) {
        var r = img.clientWidth / oldW, rect = box.getBoundingClientRect();
        var x = (box.scrollLeft + cx - rect.left) * r - (cx - rect.left);
        var y = (box.scrollTop + cy - rect.top) * r - (cy - rect.top);
        box.scrollLeft = x; box.scrollTop = y;
      }
    };
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[data-full]');
      if (!a) return;
      e.preventDefault();
      img.src = a.dataset.full; img.alt = a.dataset.cap || '';
      cap.textContent = a.dataset.cap || ''; op.href = a.dataset.full;
      setZoom(0); box.scrollTop = 0; box.scrollLeft = 0;
      lb.showModal();
    });
    document.getElementById('lbclose').onclick = function () { lb.close(); };
    document.getElementById('lbin').onclick = function () { var r = box.getBoundingClientRect(); setZoom(zi + 1, r.left + r.width / 2, r.top + r.height / 2); };
    document.getElementById('lbout').onclick = function () { var r = box.getBoundingClientRect(); setZoom(zi - 1, r.left + r.width / 2, r.top + r.height / 2); };
    var lastTap = 0;
    img.addEventListener('click', function (e) {
      var now = Date.now();
      if (now - lastTap < 320) { setZoom(zi ? 0 : 2, e.clientX, e.clientY); lastTap = 0; } else lastTap = now;
    });
    lb.addEventListener('click', function (e) { if (e.target === box && zi === 0) lb.close(); });
    document.addEventListener('keydown', function (e) {
      if (!lb.open) return;
      if (e.key === '+' || e.key === '=') document.getElementById('lbin').click();
      if (e.key === '-') document.getElementById('lbout').click();
    });
  }
})();
