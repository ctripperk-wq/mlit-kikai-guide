(function () {
  // すべて開く／閉じる
  document.querySelectorAll('.tools button').forEach(function (b) {
    b.addEventListener('click', function () {
      var open = b.dataset.act === 'open';
      document.querySelectorAll('details.cl').forEach(function (d) { d.open = open; });
    });
  });

  // 目次・アンカーから条文を開く
  function openHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    var el = id && document.getElementById(id);
    if (el && el.tagName === 'DETAILS') el.open = true;
  }
  window.addEventListener('hashchange', openHash);
  openHash();

  // ページ内検索
  var q = document.getElementById('q'), qn = document.getElementById('qn');
  if (q) {
    var norm = function (s) { return (s || '').normalize('NFKC').toLowerCase(); };
    var items = Array.prototype.slice.call(document.querySelectorAll('tr.q, details.cl, figure.zu'));
    items.forEach(function (el) { el._t = norm(el.textContent); });
    var saved = new Map();
    var clearMarks = function () {
      saved.forEach(function (h, el) { var o = el.open; el.innerHTML = h; if (el.tagName === 'DETAILS') el.open = o; });
      saved.clear();
    };
    var markIn = function (root, term) {
      saved.set(root, root.innerHTML);
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), nodes = [], n;
      while ((n = walker.nextNode())) nodes.push(n);
      nodes.forEach(function (c) {
        var v = c.nodeValue, nv = v.normalize('NFKC').toLowerCase();
        if (v.length !== nv.length) return; // 正規化で文字数が変わる箇所は印を付けない
        var i = nv.indexOf(term); if (i < 0) return;
        var frag = document.createDocumentFragment(), last = 0;
        while (i >= 0) {
          frag.appendChild(document.createTextNode(v.slice(last, i)));
          var m = document.createElement('mark'); m.textContent = v.slice(i, i + term.length);
          frag.appendChild(m); last = i + term.length; i = nv.indexOf(term, last);
        }
        frag.appendChild(document.createTextNode(v.slice(last)));
        c.parentNode.replaceChild(frag, c);
      });
    };
    var run = function () {
      clearMarks();
      var term = norm(q.value.trim()), hit = 0;
      items.forEach(function (el) {
        var ok = !term || el._t.indexOf(term) >= 0;
        el.style.display = ok ? '' : 'none';
        if (term && ok) { hit++; if (el.tagName === 'DETAILS') el.open = true; markIn(el, term); }
      });
      qn.textContent = term ? hit + '件' : '';
    };
    var t;
    q.addEventListener('input', function () { clearTimeout(t); t = setTimeout(run, 200); });
  }

  // ライトボックス
  var lb = document.getElementById('lb');
  if (lb && lb.showModal) {
    var img = document.getElementById('lbimg'), cap = document.getElementById('lbcap'),
        box = lb.querySelector('.lbimg'), op = document.getElementById('lbopen');
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[data-full]');
      if (!a) return;
      e.preventDefault();
      img.src = a.dataset.full; img.alt = a.dataset.cap || '';
      cap.textContent = a.dataset.cap || ''; op.href = a.dataset.full;
      box.classList.remove('zoom'); box.scrollTop = 0;
      document.getElementById('lbzoom').textContent = '拡大';
      lb.showModal();
    });
    document.getElementById('lbclose').onclick = function () { lb.close(); };
    document.getElementById('lbzoom').onclick = function () {
      var z = box.classList.toggle('zoom');
      this.textContent = z ? '縮小' : '拡大';
    };
    img.addEventListener('dblclick', function () { document.getElementById('lbzoom').click(); });
    lb.addEventListener('click', function (e) { if (e.target === box) lb.close(); });
  }
})();
