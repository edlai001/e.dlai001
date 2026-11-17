'use strict';
/* Login / register page */

const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const authError = document.getElementById('auth-error');

document.querySelectorAll('[data-auth-mode]').forEach(button => {
  button.addEventListener('click', () => {
    const mode = button.dataset.authMode;
    document.querySelectorAll('[data-auth-mode]').forEach(b =>
      b.setAttribute('aria-pressed', String(b === button)));
    loginForm.hidden = mode !== 'login';
    registerForm.hidden = mode !== 'register';
    authError.hidden = true;
    (mode === 'login' ? loginForm : registerForm).querySelector('input').focus();
  });
});

async function logIn(email, password) {
  return api('/api/auth/login', { method: 'POST', body: { email, password }, allow401: true });
}

/** Disable the submit button while the request runs, so it can't be sent twice. */
async function submitWith(form, action) {
  const button = form.querySelector('[type="submit"]');
  button.disabled = true;
  authError.hidden = true;
  try {
    const error = await action();
    if (error) showMessage(authError, error, 'error');
  } finally {
    button.disabled = false;
  }
}

loginForm.addEventListener('submit', event => {
  event.preventDefault();
  submitWith(loginForm, async () => {
    const res = await logIn(
      document.getElementById('login-email').value,
      document.getElementById('login-password').value);
    if (res.ok) { window.location.href = '/dashboard'; return null; }
    return res.data.error || 'Login failed';
  });
});

registerForm.addEventListener('submit', event => {
  event.preventDefault();
  submitWith(registerForm, async () => {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const res = await api('/api/auth/register', { method: 'POST', body: { email, password } });
    if (!res.ok) return res.data.error || 'Registration failed';
    await logIn(email, password);
    window.location.href = '/dashboard';
    return null;
  });
});
