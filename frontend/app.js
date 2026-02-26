const API = `${window.location.origin}/api`;
let token = localStorage.getItem('token');
let me = null;

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loginOrRegister(path) {
  const username = $('username').value.trim();
  const password = $('password').value;
  const data = await api(path, { method: 'POST', body: JSON.stringify({ username, password }) });
  token = data.access_token;
  localStorage.setItem('token', token);
  await loadApp();
}

function toIsoDate(value) {
  return value ? `${value}T00:00:00` : null;
}

async function createRecord() {
  const payload = {
    record_type: $('record-type').value,
    start_date: toIsoDate($('start-date').value),
    end_date: toIsoDate($('end-date').value),
    start_half: $('start-half').value,
    end_half: $('end-half').value,
    minutes: $('minutes').value ? Number($('minutes').value) : null,
    note: $('note').value || null,
  };
  await api('/leave', { method: 'POST', body: JSON.stringify(payload) });
  $('create-msg').textContent = 'Saved';
  await Promise.all([loadBalance(), loadMyRecords(), loadAllRecords()]);
}

async function loadBalance() {
  const data = await api('/leave/balance');
  $('balance').textContent = `Balance: ${data.leave_balance}`;
}

function renderRecords(target, items) {
  target.innerHTML = '';
  items.forEach((x) => {
    const li = document.createElement('li');
    li.innerHTML = `<b>${x.record_type}</b> - ${x.total_leave_days} day(s)
      <div class='small'>${x.start_datetime.slice(0, 10)} ${x.note || ''}</div>`;
    target.appendChild(li);
  });
}

async function loadMyRecords() {
  const data = await api('/leave/my?page=1&page_size=20');
  renderRecords($('my-list'), data.items);
}

async function loadUsers() {
  if (me.role !== 'admin') return;
  const users = await api('/admin/users');
  $('user-list').innerHTML = users.map((u) => `<li>${u.username} - ${u.role} - balance ${u.leave_balance}</li>`).join('');
}

async function loadAllRecords() {
  if (me.role !== 'admin') return;
  const data = await api('/admin/all-records?page=1&page_size=20');
  renderRecords($('all-records'), data.items);
}

async function createUser() {
  await api('/admin/users', {
    method: 'POST',
    body: JSON.stringify({ username: $('new-user-name').value, password: $('new-user-password').value, role: 'user', leave_balance: 0 }),
  });
  await loadUsers();
}

async function loadApp() {
  me = await api('/auth/me');
  $('auth-card').classList.add('hidden');
  $('app').classList.remove('hidden');
  $('me').textContent = `${me.username} (${me.role})`;
  if (me.role === 'admin') $('admin-panel').classList.remove('hidden');
  await Promise.all([loadBalance(), loadMyRecords(), loadUsers(), loadAllRecords()]);
}

$('login-btn').onclick = () => loginOrRegister('/auth/login').catch((e) => $('auth-msg').textContent = e.message);
$('register-btn').onclick = () => loginOrRegister('/auth/register').catch((e) => $('auth-msg').textContent = e.message);
$('create-btn').onclick = () => createRecord().catch((e) => $('create-msg').textContent = e.message);
$('create-user-btn').onclick = () => createUser().catch((e) => alert(e.message));
$('logout-btn').onclick = () => { localStorage.removeItem('token'); window.location.reload(); };

if (token) loadApp().catch(() => { localStorage.removeItem('token'); });
