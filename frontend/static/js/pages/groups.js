'use strict';
/* Study groups: create, my groups, discover/join, group detail */

const $ = id => document.getElementById(id);
let activeGroupId = null;
let discoverGroups = [];

async function loadMyGroups() {
  const { data } = await api('/api/groups');
  $('group-list').innerHTML = data.groups.length === 0
    ? emptyState('No groups yet')
    : data.groups.map(g => `
        <li>
          <button class="list-item list-item--button" type="button" data-action="open" data-id="${g.id}"
                  ${g.id === activeGroupId ? 'aria-current="true"' : ''}>${esc(g.name)}</button>
        </li>`).join('');
}

async function loadDiscover() {
  const { data } = await api('/api/groups/discover');
  discoverGroups = data.groups || [];
  renderDiscover();
}

function renderDiscover() {
  const list = $('discover-list');
  if (discoverGroups.length === 0) {
    list.innerHTML = emptyState('No other groups to discover yet.', 'p');
    return;
  }
  const q = $('discover-search').value.trim().toLowerCase();
  const found = discoverGroups.filter(g =>
    !q || `${g.name} ${g.description || ''} ${g.subjects.join(' ')}`.toLowerCase().includes(q));
  list.innerHTML = found.length === 0
    ? emptyState('No groups match your search.', 'p')
    : found.map(g => `
        <article class="group-card">
          <div class="group-card__top">
            <h3 class="group-card__name">${esc(g.name)}</h3>
            <span class="badge">${g.member_count} member${g.member_count === 1 ? '' : 's'}</span>
          </div>
          <p class="list-item__meta">${esc(g.description || 'No description')}</p>
          ${g.subjects.length
            ? `<ul class="tag-list">${g.subjects.map(s => `<li class="tag">${esc(s)}</li>`).join('')}</ul>`
            : emptyState('No subjects listed yet', 'p')}
          <p class="list-item__meta">Created by ${esc(g.creator)}${
            g.next_session ? ` · Next session ${esc(g.next_session)}` : ''}</p>
          <button class="btn btn--primary btn--sm" type="button" data-action="join" data-id="${g.id}">
            Join group
          </button>
        </article>`).join('');
}

async function openGroup(id, { scroll = false } = {}) {
  activeGroupId = id;
  const { data } = await api(`/api/groups/${id}`);
  $('detail-name').textContent = data.name;
  $('detail-desc').textContent = data.description || '';
  $('group-chat-link').href = `/chat?g=${id}`;
  $('member-list').innerHTML = data.members.map(m => `
    <li class="list-item">
      <span class="list-item__main">${esc(m.name)}</span>
      <span class="badge">${esc(m.role)}</span>
    </li>`).join('');
  $('session-list').innerHTML = data.sessions.length === 0
    ? emptyState('No sessions yet')
    : data.sessions.map(s => `
        <li class="list-item">
          <span class="list-item__main">${esc(s.start.replace('T', ' ').slice(0, 16))}</span>
          <span class="list-item__meta">${esc(s.location || '')}</span>
        </li>`).join('');
  ['invite-msg', 'session-msg'].forEach(msgId => { $(msgId).hidden = true; });
  loadInvitable(id);

  // Highlight the open group in "My groups"
  document.querySelectorAll('#group-list [data-action="open"]').forEach(b => {
    if (Number(b.dataset.id) === id) b.setAttribute('aria-current', 'true');
    else b.removeAttribute('aria-current');
  });

  const detail = $('group-detail');
  detail.hidden = false;
  // On phones the detail card is below the lists, so bring it into view
  if (scroll && window.matchMedia('(max-width: 767px)').matches) {
    detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

async function loadInvitable(id) {
  const select = $('invite-select');
  const { ok, data } = await api(`/api/groups/${id}/invitable`);
  select.innerHTML = !ok || data.partners.length === 0
    ? '<option value="">No accepted partners to invite</option>'
    : data.partners.map(p => `<option value="${p.user_id}">${esc(p.name)}</option>`).join('');
}

$('discover-search').addEventListener('input', renderDiscover);

$('create-form').addEventListener('submit', async event => {
  event.preventDefault();
  const res = await api('/api/groups', {
    method: 'POST',
    body: { name: $('group-name').value.trim(), description: $('group-desc').value },
  });
  if (res.ok) {
    event.target.reset();
    showMessage($('create-msg'), 'Group created', 'success', 2500);
    loadMyGroups();
  } else {
    showMessage($('create-msg'), res.data.error, 'error');
  }
});

$('invite-form').addEventListener('submit', async event => {
  event.preventDefault();
  const userId = parseInt($('invite-select').value, 10);
  if (!userId) {
    showMessage($('invite-msg'), 'Nobody to invite yet. Accept a match request first.', 'error');
    return;
  }
  const res = await api(`/api/groups/${activeGroupId}/invite`, { method: 'POST', body: { user_id: userId } });
  if (res.ok) {
    await openGroup(activeGroupId);
    showMessage($('invite-msg'), 'Added to the group', 'success', 2500);
  } else {
    showMessage($('invite-msg'), res.data.error, 'error');
  }
});

$('session-form').addEventListener('submit', async event => {
  event.preventDefault();
  const res = await api(`/api/groups/${activeGroupId}/sessions`, {
    method: 'POST',
    body: {
      start_datetime: $('session-start').value.replace('T', ' '),
      end_datetime: $('session-end').value.replace('T', ' '),
      location_or_link: $('session-location').value,
    },
  });
  if (res.ok) {
    event.target.reset();
    await openGroup(activeGroupId);
    showMessage($('session-msg'), 'Session added', 'success', 2500);
  } else {
    showMessage($('session-msg'), res.data.error, 'error');
  }
});

onAction({
  open(button) {
    openGroup(Number(button.dataset.id), { scroll: true });
  },
  async join(button) {
    button.disabled = true;
    const id = Number(button.dataset.id);
    const res = await api(`/api/groups/${id}/join`, { method: 'POST' });
    if (!res.ok) { button.disabled = false; alert(res.data.error); return; }
    await Promise.all([loadMyGroups(), loadDiscover()]);
    openGroup(id, { scroll: true });
  },
  async leave() {
    if (!confirm('Leave this group?')) return;
    await api(`/api/groups/${activeGroupId}/leave`, { method: 'POST' });
    activeGroupId = null;
    $('group-detail').hidden = true;
    loadMyGroups();
    loadDiscover();
  },
});

loadMyGroups();
loadDiscover();
