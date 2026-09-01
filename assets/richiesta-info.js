/* KiRun — mini-form «Richiedi informazioni» sulle landing evento.
   Invia la richiesta al webhook n8n kirun-richiesta-info; la pratica nasce in Airtable e
   la persona riceve subito l'email di conferma. Nessun cookie: dati usati solo per rispondere. */
(function () {
  var form = document.querySelector('#richiedi-info form');
  if (!form) { return; }
  var lang = (document.documentElement.lang || 'it').slice(0, 2);
  var T = lang === 'en' ? {
    ok: 'Thank you! Check your inbox: we have sent you a confirmation and will reply as soon as possible.',
    err: 'Something went wrong. Please write to us directly at info@ki-run.it',
    wait: 'Sending…'
  } : {
    ok: 'Grazie! Controlla la posta: ti abbiamo inviato una conferma e ti rispondiamo al più presto.',
    err: 'Qualcosa non ha funzionato. Scrivici direttamente a info@ki-run.it',
    wait: 'Invio…'
  };
  function eventKey() {
    var a = document.querySelector('a.cta[href*="tally.so"]');
    if (a) {
      try { var u = new URL(a.getAttribute('href')); var k = u.searchParams.get('event_key'); if (k) { return k; } } catch (e) {}
    }
    var m = location.pathname.match(/\/eventi\/([^\/]+)/);
    return m ? m[1].split('-').join('_') : '';
  }
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var esito = form.querySelector('.esito');
    var bottone = form.querySelector('button[type="submit"]');
    if (form.querySelector('[name="azienda"]').value) { return; }
    var dati = {
      rid: 'ri-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8),
      nome: form.querySelector('[name="nome"]').value.trim(),
      email: form.querySelector('[name="email"]').value.trim(),
      domanda: form.querySelector('[name="domanda"]').value.trim(),
      consenso_marketing: form.querySelector('[name="consenso_marketing"]').checked,
      event_key: eventKey(),
      lang: lang.toUpperCase(),
      page_url: location.href.split('#')[0]
    };
    bottone.disabled = true;
    bottone.textContent = T.wait;
    fetch(form.getAttribute('data-endpoint'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dati)
    }).then(function (r) {
      if (!r.ok) { throw new Error('http ' + r.status); }
      form.querySelectorAll('label, button, .privacy-nota').forEach(function (el) { el.hidden = true; });
      esito.textContent = T.ok;
      esito.hidden = false;
      if (window.fbq) { fbq('trackCustom', 'RichiestaInfo', { content_name: dati.event_key }); }
    }).catch(function () {
      esito.textContent = T.err;
      esito.hidden = false;
      bottone.disabled = false;
      bottone.textContent = form.getAttribute('data-label-invia') || 'Invia';
    });
  });
})();
