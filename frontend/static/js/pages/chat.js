'use strict';
/* Messages: direct chats with partners and group chats */

const $ = id => document.getElementById(id);
const POLL_MS = 4000;
let current = null;   // { type: 'direct' | 'group', id: number, name: string }
let pollTimer = null;

function conversationButton(type, id, name) {
  return `
    <li>
      <button class="list-item list-item--button" type="button" data-action="open-chat"
              data-type="${type}" data-id="${id}" data-name="${esc(name)}">${esc(name)}</button>
    </li>`;
}

async function loadSidebar() {
  const [partners, groups] = await Promise.all([api('/api/partners'), api('/api/groups')]);
  $('partner-list').innerHTML = partners.data.partners.length === 0
    ? emptyState('No partners yet. Send and accept a match request first.')
    : partners.data.partners.map(p => conversationButton('direct', p.user_id, p.name)).join('');
  $('chat-group-list').innerHTML = groups.data.groups.length === 0
    ? emptyState('No groups yet.')
    : groups.data.groups.map(g => conversationButton('group', g.id, g.name)).join('');

  // Links like /chat?g=5 (from the groups page) or /chat?u=7 open that conversation
  const params = new URLSearchParams(window.location.search);
  if (params.get('u')) openChat('direct', Number(params.get('u')));
  else if (params.get('g')) openChat('group', Number(params.get('g')));
}

function endpoint() {
  return current.type === 'direct'
    ? `/api/messages/direct/${current.id}`
    : `/api/groups/${current.id}/messages`;
}

async function openChat(type, id) {
  const button = document.querySelector(`[data-action="open-chat"][data-type="${type}"][data-id="${id}"]`);
  current = { type, id, name: button ? button.dataset.name : 'Conversation' };

  document.querySelectorAll('[data-action="open-chat"]').forEach(b => b.removeAttribute('aria-current'));
  if (button) button.setAttribute('aria-current', 'true');

  $('chat-title').textContent = current.name;
  $('chat-form').hidden = false;
  $('chat').classList.add('is-open');   // phones: switch from the list to the conversation

  await refreshMessages(true);
  clearInterval(pollTimer);
  pollTimer = setInterval(() => refreshMessages(false), POLL_MS);
  $('message-body').focus();
}

function closeChat() {
  clearInterval(pollTimer);
  current = null;
  $('chat').classList.remove('is-open');
}

function bubble(m) {
  const sender = current.type === 'group' && !m.mine
    ? `<span class="bubble__sender">${esc(m.sender)}</span>` : '';
  return `
    <div class="bubble ${m.mine ? 'bubble--mine' : 'bubble--theirs'}">${sender}${esc(m.body)}<span
      class="bubble__meta">${esc(m.sent_at)}</span></div>`;
}

async function refreshMessages(forceScroll) {
  if (!current) return;
  const box = $('chat-messages');
  const res = await api(endpoint());
  if (!res.ok) {
    box.innerHTML = `<p class="chat__empty">${esc(res.data.error)}</p>`;
    return;
  }
  const nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 80;
  box.innerHTML = res.data.messages.length === 0
    ? '<p class="chat__empty">No messages yet. Say hi!</p>'
    : res.data.messages.map(bubble).join('');
  if (forceScroll || nearBottom) box.scrollTop = box.scrollHeight;
}

$('chat-form').addEventListener('submit', async event => {
  event.preventDefault();
  const input = $('message-body');
  const body = input.value.trim();
  if (!body || !current) return;
  const res = await api(endpoint(), { method: 'POST', body: { body } });
  if (res.ok) { input.value = ''; refreshMessages(true); }
  else alert(res.data.error);
});

onAction({
  'open-chat'(button) { openChat(button.dataset.type, Number(button.dataset.id)); },
  back() { closeChat(); },
});

loadSidebar();
