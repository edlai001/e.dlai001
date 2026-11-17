'use strict';
/* Admin: statistics, subject management, user list */

const $ = id => document.getElementById(id);

async function loadStats() {
  const { data } = await api('/api/admin/stats');
  const stats = [['Users', data.total_users], ['Groups', data.total_groups], ['Accepted matches', data.accepted_matches]];
  $('stats').innerHTML = stats.map(([label, value]) => `
    <div class="stat">
      <dt class="stat__label">${label}</dt>
      <dd class="stat__value">${esc(value)}</dd>
    </div>`).join('');
}

async function loadSubjects() {
  const { data } = await api('/api/admin/subjects');
  $('subject-admin').innerHTML = data.subjects.length === 0
    ? emptyState('No subjects yet')
    : data.subjects.map(s => `
        <li class="list-item">
          <span class="list-item__main">${esc(s.name)}</span>
          <button class="btn btn--danger btn--icon" type="button" data-action="delete-subject"
                  data-id="${s.id}" data-name="${esc(s.name)}" aria-label="Delete ${esc(s.name)}">✕</button>
        </li>`).join('');
}

async function loadUsers() {
  const { data } = await api('/api/admin/users');
  // data-label is shown before each value when the table stacks on phones
  $('user-rows').innerHTML = data.users.map(u => `
    <tr>
      <td data-label="ID">${esc(u.id)}</td>
      <td data-label="Email">${esc(u.email)}</td>
      <td data-label="Name">${esc(u.display_name)}</td>
      <td data-label="Role">${esc(u.role)}</td>
    </tr>`).join('');
}

$('subject-form').addEventListener('submit', async event => {
  event.preventDefault();
  const res = await api('/api/admin/subjects', { method: 'POST', body: { name: $('new-subject').value.trim() } });
  if (res.ok) { event.target.reset(); $('subject-msg').hidden = true; loadSubjects(); }
  else showMessage($('subject-msg'), res.data.error || 'Could not add subject', 'error');
});

onAction({
  async 'delete-subject'(button) {
    if (!confirm(`Delete "${button.dataset.name}"? Students will lose it from their profiles.`)) return;
    await api(`/api/admin/subjects/${button.dataset.id}`, { method: 'DELETE' });
    loadSubjects();
  },
});

loadStats();
loadSubjects();
loadUsers();
