'use strict';
/*
 * Light theme by default; the moon/sun button in the header switches to dark.
 * The choice is remembered in this browser (localStorage).
 * Loaded in <head> WITHOUT defer, so a saved dark theme is applied before the
 * page is drawn (no white flash).
 */
(function () {
  const STORAGE_KEY = 'studybuddy-theme';
  const BAR_COLORS = { light: '#FFFFFF', dark: '#162227' };   // phone browser bar
  const root = document.documentElement;

  function savedTheme() {
    try { return localStorage.getItem(STORAGE_KEY) === 'dark' ? 'dark' : 'light'; }
    catch { return 'light'; }   // storage blocked (e.g. private mode): stay light
  }

  function currentTheme() {
    return root.dataset.theme === 'dark' ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    root.dataset.theme = theme;
    const bar = document.querySelector('meta[name="theme-color"]');
    if (bar) bar.content = BAR_COLORS[theme];
    const button = document.querySelector('[data-theme-toggle]');
    if (button) button.setAttribute('aria-pressed', String(theme === 'dark'));
  }

  applyTheme(savedTheme());

  document.addEventListener('DOMContentLoaded', () => {
    applyTheme(currentTheme());   // the button exists now: sync its pressed state
    const button = document.querySelector('[data-theme-toggle]');
    if (!button) return;
    button.addEventListener('click', () => {
      const next = currentTheme() === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem(STORAGE_KEY, next); } catch { /* not remembered, still switches */ }
    });
  });
})();
