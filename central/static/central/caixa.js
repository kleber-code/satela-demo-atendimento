(function () {
  var caixa = document.getElementById('caixa');
  if (!caixa) return;
  var painel = document.getElementById('painel');
  var lista = document.getElementById('lista');
  var tokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
  var token = tokenEl ? tokenEl.value : '';
  var timerMsgs = null;
  var conv = null;

  function post(url, dados) {
    var fd = dados instanceof FormData ? dados : new URLSearchParams(dados);
    return fetch(url, { method: 'POST', headers: { 'X-CSRFToken': token }, body: fd, credentials: 'same-origin' })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { j._status = r.status; return j; }); });
  }
  function selecionadaId() { return conv ? conv.dataset.id : (new URLSearchParams(location.search)).get('c'); }
  function queryLista() {
    var p = new URLSearchParams(location.search);
    var id = selecionadaId();
    if (id) p.set('c', id);
    return p.toString();
  }
  function atualizarLista() {
    if (document.hidden) return;
    fetch(caixa.dataset.lista + '?' + queryLista(), { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (h) { if (h !== null && h.trim() !== lista.innerHTML.trim()) { var y = lista.scrollTop; lista.innerHTML = h; lista.scrollTop = y; } })
      .catch(function () {});
  }
  function rolarFim(forcar) {
    var m = document.getElementById('mensagens');
    if (!m) return;
    if (forcar || m.scrollHeight - m.scrollTop - m.clientHeight < 140) m.scrollTop = m.scrollHeight;
  }
  function abrir(url, id, empurrar) {
    fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.text(); }).then(function (h) {
      painel.innerHTML = h;
      caixa.classList.add('com-conversa');
      if (empurrar) {
        var p = new URLSearchParams(location.search); p.set('c', id);
        history.pushState({ c: id }, '', '?' + p.toString());
      }
      iniciarConversa();
      atualizarLista();
    });
  }
  lista.addEventListener('click', function (e) {
    var a = e.target.closest('a.item');
    if (!a || e.metaKey || e.ctrlKey) return;
    e.preventDefault();
    abrir('/caixa/' + a.dataset.id + '/', a.dataset.id, true);
  });
  window.addEventListener('popstate', function () { location.reload(); });

  function recarregarPainel() {
    if (!conv) return;
    fetch(conv.dataset.urlPainel, { credentials: 'same-origin' }).then(function (r) { return r.text(); }).then(function (h) {
      painel.innerHTML = h; iniciarConversa(); atualizarLista();
    });
  }

  function iniciarConversa() {
    clearInterval(timerMsgs);
    conv = document.getElementById('conv');
    if (!conv) return;
    rolarFim(true);
    var msgs = document.getElementById('mensagens');
    var ultimo = parseInt(conv.dataset.ultimo || '0', 10);
    var estado = conv.dataset.estado;

    conv.querySelectorAll('[data-acao]').forEach(function (b) {
      b.addEventListener('click', function () {
        post(conv.dataset.urlAcao, { acao: b.dataset.acao }).then(recarregarPainel);
      });
    });
    var sel = conv.querySelector('[data-atribuir]');
    if (sel) sel.addEventListener('change', function () {
      if (sel.value) post(conv.dataset.urlAcao, { acao: 'atribuir', usuario: sel.value }).then(recarregarPainel);
    });
    conv.querySelectorAll('[data-etiqueta]').forEach(function (b) {
      b.addEventListener('click', function () {
        post(conv.dataset.urlAcao, { acao: 'etiqueta', etiqueta: b.dataset.etiqueta }).then(function () {
          var on = !b.classList.contains('ligada');
          b.classList.toggle('ligada', on); b.setAttribute('aria-pressed', on);
          estado = null; atualizarLista();
        });
      });
    });
    var voltar = conv.querySelector('[data-voltar]');
    if (voltar) voltar.addEventListener('click', function () {
      caixa.classList.remove('com-conversa');
      var p = new URLSearchParams(location.search); p.delete('c');
      history.pushState({}, '', '?' + p.toString());
    });

    function buscar() {
      if (document.hidden && !conv) return;
      fetch(conv.dataset.urlMsgs + '?depois=' + ultimo, { credentials: 'same-origin' })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) {
          if (!j || !document.body.contains(conv)) return;
          if (estado !== null && j.estado !== estado) { recarregarPainel(); return; }
          if (j.html && j.html.trim()) {
            var perto = msgs.scrollHeight - msgs.scrollTop - msgs.clientHeight < 140;
            msgs.insertAdjacentHTML('beforeend', j.html);
            if (perto) msgs.scrollTop = msgs.scrollHeight;
            atualizarLista();
          }
          ultimo = j.ultimo;
          if (estado === null) estado = j.estado;
        }).catch(function () {});
    }
    timerMsgs = setInterval(buscar, 2000);

    var form = document.getElementById('compor');
    if (!form) return;
    var ta = form.querySelector('textarea');
    var box = document.getElementById('rapidas');
    var rapidas = [];
    try { rapidas = JSON.parse(document.getElementById('rapidas-dados').textContent); } catch (e) {}
    var foco = 0, vis = [];
    function fecharRapidas() { box.hidden = true; vis = []; }
    function mostrarRapidas() {
      var v = ta.value;
      if (v.charAt(0) !== '/' || /\s/.test(v)) return fecharRapidas();
      vis = rapidas.filter(function (r) { return r.atalho.indexOf(v.toLowerCase()) === 0; });
      if (!vis.length) return fecharRapidas();
      foco = Math.min(foco, vis.length - 1);
      box.innerHTML = '';
      vis.forEach(function (r, i) {
        var b = document.createElement('button'); b.type = 'button'; b.className = i === foco ? 'foco' : '';
        var c = document.createElement('b'); c.textContent = r.atalho + ' · ' + r.titulo;
        var s = document.createElement('small'); s.textContent = r.texto.slice(0, 90);
        b.appendChild(c); b.appendChild(s);
        b.addEventListener('click', function () { inserir(r); });
        box.appendChild(b);
      });
      box.hidden = false;
    }
    function inserir(r) { ta.value = r.texto; fecharRapidas(); ta.focus(); }
    ta.addEventListener('input', function () { foco = 0; mostrarRapidas(); });
    ta.addEventListener('keydown', function (e) {
      if (!box.hidden && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        e.preventDefault(); foco = (foco + (e.key === 'ArrowDown' ? 1 : -1) + vis.length) % vis.length; mostrarRapidas(); return;
      }
      if (!box.hidden && (e.key === 'Enter' || e.key === 'Tab')) { e.preventDefault(); inserir(vis[foco]); return; }
      if (e.key === 'Escape') fecharRapidas();
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var texto = ta.value.trim();
      if (!texto) return;
      var tipo = form.querySelector('[name=tipo]:checked').value;
      post(conv.dataset.urlEnviar, { texto: texto, tipo: tipo }).then(function (j) {
        if (j.ok) {
          ta.value = '';
          if (tipo === 'resposta') { recarregarPainel(); } else { buscar(); }
        } else { alert(j.erro || 'Não foi possível enviar.'); }
      });
    });
  }

  iniciarConversa();
  setInterval(atualizarLista, 5000);
})();
