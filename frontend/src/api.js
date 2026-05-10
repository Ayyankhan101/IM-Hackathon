const BASE = 'http://localhost:8001';

/**
 * POST /chat — send a question, get an answer.
 * Returns { answer: string } or throws with a user-readable message.
 */
export async function postChat(sessionId, question) {
  let res;
  try {
    res = await fetch(`${BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, question }),
      signal: AbortSignal.timeout(60_000),
    });
  } catch (err) {
    if (err.name === 'TimeoutError') {
      throw new Error('Request timed out — the backend took too long to respond.');
    }
    throw new Error('Cannot reach the backend. Make sure it is running on port 8001.');
  }

  if (!res.ok) {
    let msg = `Server error ${res.status}`;
    try { const j = await res.json(); msg = j.error || j.detail || msg; } catch {}
    throw new Error(msg);
  }

  const data = await res.json();
  if (data.error) throw new Error(data.error);
  if (typeof data.answer !== 'string') throw new Error('Unexpected response format from backend.');
  return data.answer;
}

export async function checkHealth() {
  try {
    const res = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(3_000) });
    return res.ok;
  } catch {
    return false;
  }
}
