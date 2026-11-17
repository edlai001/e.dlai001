'use strict';
/* Profile: personal info, subjects, weekly availability */

const $ = id => document.getElementById(id);

async function loadProfile() {
  const { data } = await api('/api/profile');
  $('display-name').value = data.display_name || '';
  $('major').value = data.major || '';
  $('bio').value = data.bio || '';
  $('language').value = data.language || 'English';

  $('subject-list').innerHTML = data.subjects.length === 0
    ? emptyState('No subjects yet')
    : data.subjects.map(s => `
        <li class="list-item">
          <span class="list-item__main">
            <span class="tag">${esc(s.name)}</span>
            <span class="list-item__meta">${esc(s.level)} · ${esc(s.goal)}</span>
          </span>
          <button class="btn btn--danger btn--icon" type="button" data-action="remove-subject"
                  data-id="${s.id}" aria-label="Remove ${esc(s.name)}">✕</button>
        </li>`).join('');
}

async function loadSlots() {
  const { data } = await api('/api/availability');
  $('slot-list').innerHTML = data.slots.length === 0
    ? emptyState('No times yet')
    : data.slots.map(s => `
        <li class="list-item">
          <span class="list-item__main">${esc(s.day)} · ${esc(s.start)}–${esc(s.end)}</span>
          <button class="btn btn--danger btn--icon" type="button" data-action="remove-slot"
                  data-id="${s.id}" aria-label="Remove ${esc(s.day)} ${esc(s.start)}">✕</button>
        </li>`).join('');
}

async function loadSubjectOptions() {
  const { data } = await api('/api/profile/subjects');
  $('subject-select').innerHTML = data.subjects
    .map(s => `<option value="${esc(s.name)}">${esc(s.name)}</option>`).join('');
}

$('profile-form').addEventListener('submit', async event => {
  event.preventDefault();
  const res = await api('/api/profile', {
    method: 'PUT',
    body: {
      display_name: $('display-name').value,
      major: $('major').value,
      bio: $('bio').value,
      language: $('language').value,
    },
  });
  showMessage($('profile-msg'), res.ok ? 'Profile saved' : res.data.error,
              res.ok ? 'success' : 'error', 2500);
});

$('subject-form').addEventListener('submit', async event => {
  event.preventDefault();
  const res = await api('/api/profile/subjects', {
    method: 'POST',
    body: {
      subject_name: $('subject-select').value,
      level: $('subject-level').value,
      goal: $('subject-goal').value,
    },
  });
  if (res.ok) { $('subject-msg').hidden = true; loadProfile(); }
  else showMessage($('subject-msg'), res.data.error, 'error', 4000);
});

$('slot-form').addEventListener('submit', async event => {
  event.preventDefault();
  const res = await api('/api/availability', {
    method: 'POST',
    body: {
      day_of_week: parseInt($('slot-day').value, 10),
      start_time: $('slot-start').value,
      end_time: $('slot-end').value,
    },
  });
  if (res.ok) { $('slot-msg').hidden = true; loadSlots(); }
  else showMessage($('slot-msg'), res.data.error, 'error', 4000);
});

onAction({
  async 'remove-subject'(button) {
    await api(`/api/profile/subjects/${button.dataset.id}`, { method: 'DELETE' });
    loadProfile();
  },
  async 'remove-slot'(button) {
    await api(`/api/availability/${button.dataset.id}`, { method: 'DELETE' });
    loadSlots();
  },
});

loadProfile();
loadSlots();
loadSubjectOptions();
