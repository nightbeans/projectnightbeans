(function () {
  if (sessionStorage.getItem('work_auth') === '1') return;
  if (localStorage.getItem('work_sso_auth') === '1') return;

  const CLIENT_ID = '709784373150-q5budplonk1uggjvr9kq2pqggf205mq4.apps.googleusercontent.com';
  const ALLOWED_DOMAIN = 'mobile-power.co.uk';

  function decodeJWT(token) {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
  }

  function showError(msg) {
    const err = document.getElementById('__we-err');
    if (err) { err.textContent = msg; err.style.display = 'block'; }
  }

  function handleCredential(response) {
    try {
      const c = decodeJWT(response.credential);
      const emailOk = typeof c.email === 'string' && c.email.toLowerCase().endsWith('@' + ALLOWED_DOMAIN);
      if (c.email_verified && c.hd === ALLOWED_DOMAIN && emailOk) {
        localStorage.setItem('work_sso_auth', '1');
        localStorage.setItem('work_email', c.email.toLowerCase());
        const gate = document.getElementById('__work-email-gate');
        if (gate) gate.remove();
      } else {
        showError("That account isn't a @" + ALLOWED_DOMAIN + " workspace user.");
      }
    } catch (e) {
      showError('Sign-in failed. Please try again.');
    }
  }

  function injectGate() {
    if (!document.body) { return setTimeout(injectGate, 10); }

    const gate = document.createElement('div');
    gate.id = '__work-email-gate';
    gate.setAttribute('style', 'position:fixed;inset:0;background:#1A4957;display:flex;align-items:center;justify-content:center;z-index:2147483647;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;');
    gate.innerHTML = '<div style="text-align:center;padding:2rem;max-width:380px;width:100%;box-sizing:border-box;">'
      + '<h2 style="color:#fff;font-size:1.6rem;font-weight:600;margin:0 0 0.4rem;">joeldelaney</h2>'
      + '<p style="color:#b0d4dd;margin:0 0 2rem;font-size:0.95rem;">Sign in with your MOPO Google account to continue</p>'
      + '<div id="__we-btn" style="display:flex;justify-content:center;min-height:44px;"></div>'
      + '<p id="__we-err" style="color:#e07070;margin:1rem 0 0;font-size:0.9rem;display:none;"></p>'
      + '</div>';
    document.body.appendChild(gate);

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = function () {
      google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: handleCredential,
        hd: ALLOWED_DOMAIN,
        auto_select: true,
        cancel_on_tap_outside: false,
        use_fedcm_for_prompt: true
      });
      google.accounts.id.renderButton(document.getElementById('__we-btn'), {
        theme: 'filled_white',
        size: 'large',
        text: 'signin_with',
        shape: 'pill'
      });
      google.accounts.id.prompt();
    };
    script.onerror = function () {
      showError('Could not load Google Sign-In. Check your connection and reload.');
    };
    document.head.appendChild(script);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectGate);
  } else {
    injectGate();
  }
})();
