'use strict';
/* Find partners: ranked match list and match requests */

const percent = value => Math.round(value * 100);

function scoreRow(label, value) {
  return `
    <div class="score-row">
      <span class="score-row__label">${label}</span>
      <progress class="meter" max="100" value="${percent(value)}"
                aria-label="${label} match ${percent(value)}%"></progress>
      <span class="score-row__value">${percent(value)}%</span>
    </div>`;
}

function matchCard(m) {
  const name = m.display_name || '?';
  const shared = m.shared_subjects.length
    ? `<ul class="tag-list">${m.shared_subjects.map(s => `<li class="tag">${esc(s)}</li>`).join('')}</ul>`
    : emptyState('None', 'p');
  return `
    <article class="card card--interactive">
      <div class="match-card__header">
        <div class="avatar" aria-hidden="true">${esc(name[0].toUpperCase())}</div>
        <div>
          <h2 class="match-card__name">${esc(name)}</h2>
          <span class="badge badge--accent">${percent(m.score)}% match</span>
        </div>
      </div>
      <div class="match-card__details">
        <div>
          <h3 class="card__subtitle">Shared subjects</h3>
          ${shared}
        </div>
        <div>
          <h3 class="card__subtitle">Scores</h3>
          ${scoreRow('Subjects', m.subject_score)}
          ${scoreRow('Schedule', m.availability_score)}
        </div>
      </div>
      <div class="match-card__footer">
        <button class="btn btn--primary" type="button" data-action="request" data-user-id="${m.user_id}">
          Send request
        </button>
        <span class="empty" role="status"></span>
      </div>
    </article>`;
}

async function loadMatches() {
  const { data } = await api('/api/matches');
  const list = document.getElementById('match-list');
  list.innerHTML = data.matches.length === 0
    ? `<div class="card span-full">${emptyState(
        'No matches yet. Add subjects and availability on your profile first.', 'p')}</div>`
    : data.matches.map(matchCard).join('');
}

onAction({
  async request(button) {
    button.disabled = true;
    const res = await api('/api/matches/request', {
      method: 'POST', body: { to_user_id: Number(button.dataset.userId) },
    });
    if (res.ok) button.textContent = 'Request sent ✓';
    else button.nextElementSibling.textContent = res.data.error;
  },
});

loadMatches();
