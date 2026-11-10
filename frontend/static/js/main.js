// Show nav if logged in
(async function() {
  if (window.location.pathname === '/') return;
  const res = await fetch('/api/profile');
  if (res.ok) {
    document.getElementById('navLinks').style.display = 'flex';
    const data = await res.json();
    if (data.role === 'admin') {
      const link = document.getElementById('adminLink');
      if (link) { link.style.display = 'inline'; link.href = '/admin'; }
    }
  } else {
    window.location.href = '/';
  }
})();

async function logout() {
  await fetch('/api/auth/logout', {method: 'POST'});
  window.location.href = '/';
}
