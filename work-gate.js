(function () {
  if (sessionStorage.getItem('work_auth') === '1') return;
  if (localStorage.getItem('work_email_auth') === '1') return;

  const EMAIL_RE = /^[^\s@]+@mobile-power\.co\.uk$/i;

  function injectGate() {
    if (!document.body) { return setTimeout(injectGate, 10); }

    const gate = document.createElement('div');
    gate.id = '__work-email-gate';
    gate.setAttribute('style', 'position:fixed;inset:0;background:#1A4957;display:flex;align-items:center;justify-content:center;z-index:2147483647;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;');
    gate.innerHTML = '<div style="text-align:center;padding:2rem;max-width:380px;width:100%;box-sizing:border-box;">'
      + '<h2 style="color:#fff;font-size:1.6rem;font-weight:600;margin:0 0 0.4rem;">joeldelaney</h2>'
      + '<p style="color:#b0d4dd;margin:0 0 2rem;font-size:0.95rem;">Enter your MOPO email to continue</p>'
      + '<input type="email" id="__we-input" placeholder="name@mobile-power.co.uk" autocomplete="email" autocapitalize="off" autocorrect="off" spellcheck="false" style="width:100%;padding:12px 16px;background:#0f3340;border:1px solid #2d6575;border-radius:6px;color:#fff;font-size:1rem;margin-bottom:0.75rem;outline:none;box-sizing:border-box;font-family:inherit;">'
      + '<button id="__we-btn" type="button" style="width:100%;padding:12px;background:#fff;color:#1A4957;border:none;border-radius:6px;font-size:1rem;font-weight:600;cursor:pointer;font-family:inherit;">Continue</button>'
      + '<p id="__we-err" style="color:#e07070;margin:1rem 0 0;font-size:0.9rem;display:none;">Please use a @mobile-power.co.uk address</p>'
      + '</div>';
    document.body.appendChild(gate);

    const input = document.getElementById('__we-input');
    const btn = document.getElementById('__we-btn');
    const err = document.getElementById('__we-err');
    input.focus();

    function check() {
      const v = input.value.trim();
      if (EMAIL_RE.test(v)) {
        localStorage.setItem('work_email_auth', '1');
        localStorage.setItem('work_email', v.toLowerCase());
        gate.remove();
      } else {
        err.style.display = 'block';
        input.value = '';
        input.focus();
      }
    }

    btn.addEventListener('click', check);
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') check(); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectGate);
  } else {
    injectGate();
  }
})();
