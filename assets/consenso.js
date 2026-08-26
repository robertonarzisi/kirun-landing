/* KiRun — banner cookie e caricamento condizionato del Meta Pixel «Cora».
   Il pixel parte SOLO dopo «Accetta». La scelta vive in localStorage per 365 giorni
   e si cambia dalla pagina /cookie/ (window.kirunConsenso.reset()). */
(function () {
  var PIXEL = '2838135509904960';
  var KEY = 'kirun_consenso_meta';
  var GIORNI = 365;
  var lang = (document.documentElement.lang || 'it').slice(0, 2);
  var T = lang === 'en' ? {
    testo: 'We use the Meta pixel to see whether our ads bring people here and to show you relevant ads on Facebook and Instagram. No other tracking.',
    info: 'Cookie policy', ok: 'Accept', no: 'Decline', infoUrl: '/cookie/#en'
  } : {
    testo: 'Usiamo il pixel Meta per capire se le nostre inserzioni portano fin qui e per mostrarti annunci pertinenti su Facebook e Instagram. Nessun altro tracciamento.',
    info: 'Informativa cookie', ok: 'Accetta', no: 'Rifiuta', infoUrl: '/cookie/'
  };

  function leggi() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (!v || !v.t || Date.now() - v.t > GIORNI * 864e5) return null;
      return v.scelta;
    } catch (e) { return null; }
  }
  function scrivi(scelta) {
    try { localStorage.setItem(KEY, JSON.stringify({ scelta: scelta, t: Date.now() })); } catch (e) {}
  }
  function slug() {
    var m = location.pathname.match(/\/eventi\/([^\/]+)/);
    return m ? m[1] : location.pathname;
  }
  function caricaPixel() {
    if (window.fbq) return;
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', PIXEL);
    fbq('track', 'PageView');
    var nome = slug();
    document.querySelectorAll('a.cta').forEach(function (a) {
      a.addEventListener('click', function () { fbq('track', 'Lead', { content_name: nome }); });
    });
  }
  function stile() {
    if (document.getElementById('kirun-cookie-css')) return;
    var s = document.createElement('style');
    s.id = 'kirun-cookie-css';
    s.textContent =
      '#kirun-cookie{position:fixed;left:0.75rem;right:0.75rem;bottom:4.25rem;z-index:50;max-width:36rem;margin:0 auto;' +
      'background:#fff;color:#22334A;border:1px solid #DDE5EC;border-radius:12px;box-shadow:0 8px 28px rgba(0,0,0,.18);' +
      'padding:0.9rem 1rem;font:400 0.875rem/1.45 "Poppins","Segoe UI",system-ui,sans-serif}' +
      '@media(min-width:940px){#kirun-cookie{bottom:1rem;left:1rem;right:auto}}' +
      '#kirun-cookie p{margin:0 0 0.7rem}' +
      '#kirun-cookie a{color:#203A5D}' +
      '#kirun-cookie .azioni{display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap}' +
      '#kirun-cookie button{font:inherit;font-weight:500;border-radius:8px;padding:0.5rem 1rem;cursor:pointer;border:1px solid #203A5D;background:#fff;color:#203A5D}' +
      '#kirun-cookie button.ok{background:#F76716;border-color:#F76716;color:#fff}' +
      '#kirun-cookie button:focus-visible{outline:3px solid #203A5D;outline-offset:2px}';
    document.head.appendChild(s);
  }
  function mostraBanner() {
    if (document.getElementById('kirun-cookie')) return;
    stile();
    var d = document.createElement('div');
    d.id = 'kirun-cookie';
    d.setAttribute('role', 'dialog');
    d.setAttribute('aria-label', T.info);
    d.innerHTML = '<p>' + T.testo + ' <a href="' + T.infoUrl + '">' + T.info + '</a></p>' +
      '<div class="azioni"><button type="button" class="ok">' + T.ok + '</button>' +
      '<button type="button" class="no">' + T.no + '</button></div>';
    d.querySelector('.ok').addEventListener('click', function () { scrivi('si'); d.remove(); caricaPixel(); });
    d.querySelector('.no').addEventListener('click', function () { scrivi('no'); d.remove(); });
    document.body.appendChild(d);
  }
  function avvia() {
    var scelta = leggi();
    if (scelta === 'si') caricaPixel();
    else if (scelta !== 'no') mostraBanner();
  }
  window.kirunConsenso = {
    stato: leggi,
    reset: function () { try { localStorage.removeItem(KEY); } catch (e) {} mostraBanner(); }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', avvia);
  else avvia();
})();
