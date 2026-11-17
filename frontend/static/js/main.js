'use strict';
/* Shared helpers for every page. Page-specific code lives in js/pages/. */

/** Make text safe to put inside HTML (stops names like "<script>" from running). */
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]
  ));
}

/**
 * Call the JSON API. Returns { ok, status, data }.
 * If the session has expired (401) the user is sent to the login page,
 * unless allow401 is set (used by the login form itself).
 */
async function api(url, { method = 'GET', body, allow401 = false } = {}) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  const res = await fetch(url, options);
  if (res.status === 401 && !allow401) {
    window.location.href = '/';
    return new Promise(() => {});   // never resolves: the page is navigating away
  }
  let data = {};
  try { data = await res.json(); } catch { /* response had no JSON body */ }
  return { ok: res.ok, status: res.status, data };
}

/** Show a success or error message in an .alert element; optionally hide it again. */
function showMessage(el, text, type = 'success', hideAfterMs = 0) {
  el.textContent = text;
  el.className = `alert alert--${type}`;
  el.hidden = false;
  clearTimeout(el._hideTimer);
  if (hideAfterMs) el._hideTimer = setTimeout(() => { el.hidden = true; }, hideAfterMs);
}

/** HTML for an empty list: an <li> inside <ul> lists, or pass tag 'p' elsewhere. */
function emptyState(text, tag = 'li') {
  return `<${tag} class="empty">${esc(text)}</${tag}>`;
}

/**
 * One click listener for all buttons with data-action="name" on the page.
 * handlers = { name(buttonElement) { ... } }
 */
function onAction(handlers) {
  document.addEventListener('click', event => {
    const el = event.target.closest('[data-action]');
    if (el && handlers[el.dataset.action]) handlers[el.dataset.action](el, event);
  });
}

/* ---------- Header: phone menu and logout ---------- */
(function initHeader() {
  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.getElementById('site-nav');
  if (toggle && nav) {
    const setOpen = open => {
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
    };
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) { setOpen(false); toggle.focus(); }
    });
  }

  const logout = document.querySelector('[data-logout]');
  if (logout) {
    logout.addEventListener('click', async () => {
      await api('/api/auth/logout', { method: 'POST' });
      window.location.href = '/';
    });
  }
})();
