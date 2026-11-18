(function () {
  var chat = document.getElementById('chat');
  if (!chat) return;
  var el = {
    msgs: document.getElementById('chat-msgs'), form: document.getElementById('chat-form'),
    texto: document.getElementById('chat-texto'), enviar: document.getElementById('chat-enviar'),
    faixa: document.getElementById('faixa-estado'), sub: document.getElementById('chat-sub'),
    aval: document.getElementById('avaliacao'), estrelas: document.getElementById('estrelas'),
    obrig: document.getElementById('obrigado'), contador: document.getElementById('contador'),
  };
  var token = chat.querySelector('[name=csrfmiddlewaretoken]').value;
  var max = parseInt(chat.dataset.max, 10);
  var ultimo = 0, enviando = false, status = 'novo', csat = null, digitando = null, vistos = {};

  function json(id) { try { return JSON.parse(document.getElementById(id).textContent); } catch (e) { return null; } }
  function api(url, corpo) {
    var opt = corpo === undefined ? { credentials: 'same-origin' }
      : { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': token, 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) };
    return fetch(url, opt).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { j._status = r.status; return j; }); });
  }
  function negrito(pai, texto) {
    // seguro: só cria nós de texto e <strong>; nunca usa innerHTML
    texto.split(/(\*\*[^*]+\*\*)/).forEach(function (parte) {
      if (/^\*\*[^*]+\*\*$/.test(parte)) { var s = document.createElement('strong'); s.textContent = parte.slice(2, -2); pai.appendChild(s); }
      else pai.appendChild(document.createTextNode(parte));
    });
  }
  function linhas(pai, texto) {
    texto.split('\n').forEach(function (l, i) { if (i) pai.appendChild(document.createElement('br')); negrito(pai, l); });
  }
  function noPe() { return el.msgs.scrollHeight - el.msgs.scrollTop - el.msgs.clientHeight < 160; }
  function desenhar(m) {
    if (vistos[m.id]) return;
    vistos[m.id] = true; if (typeof m.id === 'number') ultimo = Math.max(ultimo, m.id);
    var w;
    if (m.tipo === 'sistema') {
      w = document.createElement('div'); w.className = 'msg-sis';
      var s = document.createElement('span'); linhas(s, m.texto); w.appendChild(s);
    } else if (m.tipo === 'acao') {
      w = document.createElement('div'); w.className = 'msg-acao' + (m.acao && !m.acao.ok ? ' falhou' : '');
      var sp = document.createElement('span'), b = document.createElement('b');
      b.textContent = 'IA usou uma ação · ' + (m.acao ? m.acao.rotulo : '');
      sp.appendChild(b); sp.appendChild(document.createTextNode(m.texto)); w.appendChild(sp);
    } else {
      var cls = m.tipo === 'cliente' ? 'cli' : (m.tipo === 'atendente' ? 'ate' : 'bot');
      w = document.createElement('div'); w.className = 'linha ' + cls;
      var bo = document.createElement('div'); bo.className = 'bolha';
      var meta = document.createElement('div'); meta.className = 'meta';
      meta.textContent = (m.tipo === 'cliente' ? 'Você' : (m.tipo === 'atendente' ? (m.autor || 'Atendente') + ' (humano)' : 'Aurora (IA)')) + ' · ' + m.hora;
      bo.appendChild(meta); linhas(bo, m.texto);
      if (m.fontes && m.fontes.length) {
        var f = document.createElement('div'); f.className = 'fontes';
        m.fontes.forEach(function (t) { var x = document.createElement('span'); x.className = 'fonte'; x.textContent = 'Fonte: ' + t; f.appendChild(x); });
        bo.appendChild(f);
      }
      w.appendChild(bo);
    }
    el.msgs.appendChild(w);
  }
  function mostrar(lista) {
    var pe = noPe(); tirarDigitando();
    lista.forEach(desenhar);
    if (pe || lista.length) el.msgs.scrollTop = el.msgs.scrollHeight;
  }
  function pôrDigitando() {
    if (digitando) return;
    digitando = document.createElement('div'); digitando.className = 'linha bot';
    digitando.innerHTML = '<div class="bolha digitando" aria-label="Aurora está digitando"><i></i><i></i><i></i></div>';
    el.msgs.appendChild(digitando); el.msgs.scrollTop = el.msgs.scrollHeight;
  }
  function tirarDigitando() { if (digitando) { digitando.remove(); digitando = null; } }
  function aviso(txt) {
    var w = document.createElement('div'); w.className = 'msg-sis'; var s = document.createElement('span'); s.textContent = txt; w.appendChild(s);
    el.msgs.appendChild(w); el.msgs.scrollTop = el.msgs.scrollHeight;
  }
  function estado(j) {
    if (!j || !j.status) return;
    status = j.status; csat = j.csat;
    var f = el.faixa;
    if (status === 'aguardando') { f.hidden = false; f.textContent = 'Você está na fila de atendimento humano. Pode continuar escrevendo.'; el.sub.textContent = 'aguardando atendente'; }
    else if (status === 'atendimento') { f.hidden = false; f.textContent = 'Você está falando com um atendente humano.'; el.sub.textContent = 'atendimento humano'; }
    else if (status === 'resolvida') { f.hidden = true; el.sub.textContent = 'atendimento encerrado'; }
    else { f.hidden = true; el.sub.innerHTML = '<span class="ponto on"></span>assistente virtual · responde na hora'; }
    var pedir = status === 'resolvida';
    el.aval.hidden = !pedir;
    if (pedir) {
      el.obrig.hidden = !csat;
      el.estrelas.querySelectorAll('button').forEach(function (b) { var on = csat && parseInt(b.dataset.nota, 10) <= csat; b.classList.toggle('on', !!on); b.setAttribute('aria-checked', String(csat === parseInt(b.dataset.nota, 10))); });
    }
  }
  function poll() {
    if (document.hidden || enviando) return;
    api(chat.dataset.msgs + '?depois=' + ultimo).then(function (j) { if (j.mensagens) { mostrar(j.mensagens); estado(j); } }).catch(function () {});
  }
  function enviar(texto) {
    if (enviando) return;
    texto = texto.trim();
    if (!texto) return;
    if (texto.length > max) { aviso('Mensagem muito longa (máximo ' + max + ' caracteres).'); return; }
    enviando = true; el.enviar.disabled = true; el.texto.value = ''; atualizarContador(); crescer();
    // eco imediato da mensagem do cliente (será substituída pelo id real do servidor)
    var eco = { id: 'eco' + Date.now(), tipo: 'cliente', texto: texto, hora: new Date().toTimeString().slice(0, 5) };
    var antes = Object.assign({}, vistos);
    desenhar(eco); el.msgs.scrollTop = el.msgs.scrollHeight;
    var ecoNo = el.msgs.lastElementChild;
    setTimeout(function () { if (enviando) pôrDigitando(); }, 350);
    api(chat.dataset.enviar, { texto: texto }).then(function (j) {
      tirarDigitando();
      if (j._status === 200) {
        ecoNo.remove();
        mostrar(j.mensagens); estado(j);
      } else {
        ecoNo.remove();
        aviso(j.erro || 'Não foi possível enviar agora. Tente novamente.');
        el.texto.value = texto;
      }
    }).catch(function () { tirarDigitando(); ecoNo.remove(); aviso('Sem conexão. Tente novamente.'); el.texto.value = texto; })
      .then(function () { enviando = false; el.enviar.disabled = false; el.texto.focus(); });
  }
  function atualizarContador() { el.contador.textContent = el.texto.value.length + '/' + max; }
  function crescer() { el.texto.style.height = 'auto'; el.texto.style.height = Math.min(el.texto.scrollHeight, 120) + 'px'; }

  el.form.addEventListener('submit', function (e) { e.preventDefault(); enviar(el.texto.value); });
  el.texto.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar(el.texto.value); } });
  el.texto.addEventListener('input', function () { atualizarContador(); crescer(); });
  document.querySelectorAll('[data-sug]').forEach(function (b) { b.addEventListener('click', function () { enviar(b.dataset.sug); }); });
  document.getElementById('btn-encerrar').addEventListener('click', function () {
    if (status === 'novo') { aviso('Envie uma mensagem primeiro para poder avaliar.'); return; }
    api(chat.dataset.encerrar, {}).then(function (j) { estado(j); poll(); });
  });
  el.estrelas.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-nota]'); if (!b) return;
    api(chat.dataset.avaliar, { nota: parseInt(b.dataset.nota, 10) }).then(function (j) { if (j._status === 200) estado(j); });
  });
  document.getElementById('btn-nova').addEventListener('click', function () {
    api(chat.dataset.nova, {}).then(function () { location.reload(); });
  });

  // início: histórico da sessão (se houver) ou boas-vindas
  var inicial = json('inicial') || [];
  if (inicial.length) { inicial.forEach(desenhar); } else {
    desenhar({ id: 'boas', tipo: 'bot', texto: 'Olá! Sou a Aurora, assistente virtual da Aurora Casa & Tech. Posso consultar pedido, tirar dúvidas, agendar retirada ou abrir um chamado. Como posso ajudar?', hora: new Date().toTimeString().slice(0, 5) });
  }
  estado(json('estado'));
  el.msgs.scrollTop = el.msgs.scrollHeight;
  setInterval(poll, 2500);
})();
