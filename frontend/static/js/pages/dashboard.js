'use strict';
/* Dashboard: welcome, pending requests, top matches, my groups */

async function loadWelcome() {
  const { data } = await api('/api/profile');
  document.getElementById('welcome').textContent = `Welcome back, ${data.display_name || data.email}`;
}

async function loadRequests() {
  const { data } = await api('/api/matches/requests/incoming');
  document.getElementById('pending-requests').innerHTML = data.requests.length === 0
    ? emptyState('No pending requests')
    : data.requests.map(r => `
        <li class="list-item">
          <span class="list-item__main">${esc(r.from_name)}</span>
          <span class="list-item__actions">
            <button class="btn btn--success btn--sm" type="button"
                    data-action="respond" data-id="${r.id}" data-status="accepted">Accept</button>
            <button class="btn btn--danger btn--sm" type="button"
                    data-action="respond" data-id="${r.id}" data-status="declined">Decline</button>
          </span>
        </li>`).join('');
}

async function loadTopMatches() {
  const { data } = await api('/api/matches');
  document.getElementById('top-matches').innerHTML = data.matches.length === 0
    ? emptyState('Add subjects to your profile to get matches')
    : data.matches.slice(0, 3).map(m => `
        <li class="list-item">
          <span class="list-item__main">${esc(m.display_name)}</span>
          <span class="badge badge--accent">${Math.round(m.score * 100)}%</span>
        </li>`).join('');
}

async function loadGroups() {
  const { data } = await api('/api/groups');
  document.getElementById('my-groups').innerHTML = data.groups.length === 0
    ? emptyState('No groups yet')
    : data.groups.slice(0, 3).map(g => `
        <li class="list-item"><span class="list-item__main">${esc(g.name)}</span></li>`).join('');
}

onAction({
  async respond(button) {
    button.disabled = true;
    await api(`/api/matches/request/${button.dataset.id}`, {
      method: 'PUT', body: { status: button.dataset.status },
    });
    loadRequests();
  },
});

loadWelcome();
loadRequests();
loadTopMatches();
loadGroups();
