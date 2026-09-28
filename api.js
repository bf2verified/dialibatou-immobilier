/**
 * Client API DIALIBATOU BTP IMMOBILIER
 * Charge AVANT le bloc React (index.html) : <script src="api.js"></script>
 *
 * Config : definir window.DIALIBATOU_API_URL avant ce script, sinon defaut local.
 *   <script>window.DIALIBATOU_API_URL='https://api.mon-domaine.com';</script>
 */
const API_URL = window.DIALIBATOU_API_URL || 'http://localhost:8001';

/** Prefixe les URL relatives de fichiers (/uploads/...) avec l'URL du backend */
const mediaUrl = (u) => (u && typeof u === 'string' && u.startsWith('/') ? API_URL + u : u);

/** Appel HTTP generique — THROW sur toute erreur HTTP/reseau (jamais silencieux) */
const request = async (path, opts = {}) => {
  const { method = 'GET', body, token, formData } = opts;
  const headers = {};
  if (token) headers['Authorization'] = 'Bearer ' + token;
  let payload;
  if (formData) {
    payload = formData; // multipart : le navigateur pose le header Content-Type
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(API_URL + path, { method, headers, body: payload });
  } catch (e) {
    const err = new Error('Backend injoignable (' + API_URL + ')');
    err.cause = e;
    throw err;
  }
  if (!res.ok) {
    let detail = 'Erreur HTTP ' + res.status;
    try {
      const j = await res.json();
      if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch (e) { /* reponse non-JSON */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.status === 204 ? null : res.json();
};

const api = {
  // --- Generiques ---
  get: (path, token) => request(path, { token }),
  post: (path, body, token) => request(path, { method: 'POST', body, token }),
  put: (path, body, token) => request(path, { method: 'PUT', body, token }),
  del: (path, token) => request(path, { method: 'DELETE', token }),

  // --- Proprietes ---
  getProperties: () => request('/api/properties'),
  getProperty: (id) => request('/api/properties/' + id),
  createProperty: (data, token) => request('/api/properties', { method: 'POST', body: data, token }),
  updateProperty: (id, data, token) => request('/api/properties/' + id, { method: 'PUT', body: data, token }),
  deleteProperty: (id, token) => request('/api/properties/' + id, { method: 'DELETE', token }),
  addView: (id) => request('/api/properties/' + id + '/view', { method: 'POST' }),

  // --- Lots (cooperative) ---
  getLots: () => request('/api/lots'),
  createLot: (data, token) => request('/api/lots', { method: 'POST', body: data, token }),
  updateLot: (id, data, token) => request('/api/lots/' + id, { method: 'PUT', body: data, token }),
  deleteLot: (id, token) => request('/api/lots/' + id, { method: 'DELETE', token }),

  // --- Messages de contact ---
  createMessage: (data) => request('/api/messages', { method: 'POST', body: data }),
  getMessages: (token) => request('/api/messages', { token }),
  updateMessage: (id, data, token) => request('/api/messages/' + id, { method: 'PUT', body: data, token }),
  deleteMessage: (id, token) => request('/api/messages/' + id, { method: 'DELETE', token }),

  // --- Auth admin (JWT) ---
  login: (username, password) =>
    request('/api/auth/login', { method: 'POST', body: { username, password } }),

  // --- Uploads multipart (fichiers physiques, jamais de base64) ---
  uploadImage: (token, file) => {
    const fd = new FormData();
    fd.append('file', file);
    return request('/api/upload/image', { method: 'POST', formData: fd, token });
  },
  uploadVideo: (token, file) => {
    const fd = new FormData();
    fd.append('file', file);
    return request('/api/upload/video', { method: 'POST', formData: fd, token });
  },
};
