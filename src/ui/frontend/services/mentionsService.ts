// Service for fetching mentions from the backend API
// Works in development with backend at http://localhost:8000

export type APIMention = {
  id: string;
  text: string;
  url: string | null;
  timestamp: string | null;
  platform: string;
  entity_mentioned: string[];
  author: string | null;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentiment_score: number; // -1..1
  rating?: number | null;
  topics?: string[];
  category?: string | null; // complaint, question, review, praise
  key_insight?: string | null;
  summary?: string | null;
  confidence?: number | null;
  actionable?: boolean;
  response_status?: string | null;
  response_draft?: string | null;
  assigned_to?: string | null;
};

export type MentionsQuery = {
  entity?: string; // Taboola | Realize
  days?: number; // default server-side
  sentiment?: 'positive' | 'neutral' | 'negative' | 'all';
  category?: 'complaint' | 'review' | 'question' | 'praise' | 'all';
  limit?: number;
};

const BASE_URL = 'http://localhost:8000';

export async function fetchMentions(query: MentionsQuery = {}): Promise<APIMention[]> {
  const params = new URLSearchParams();
  if (query.entity) params.set('entity', query.entity);
  if (query.days != null) params.set('days', String(query.days));
  if (query.limit != null) params.set('limit', String(query.limit));
  if (query.sentiment && query.sentiment !== 'all') params.set('sentiment', query.sentiment);
  if (query.category && query.category !== 'all') params.set('category', query.category);

  const url = `${BASE_URL}/api/mentions?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Failed to fetch mentions: ${res.status} ${text}`);
  }
  return res.json();
}

export async function postReply(itemId: string, by: string, content: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/mentions/${encodeURIComponent(itemId)}/reply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ by, content }),
  });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`Failed to post reply: ${res.status} ${t}`);
  }
}

export async function patchMentionStatus(itemId: string, payload: { response_status?: string; actionable?: boolean }): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/mentions/${encodeURIComponent(itemId)}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`Failed to update status: ${res.status} ${t}`);
  }
}

export async function listReplies(itemId: string): Promise<{ id: string; by: string; content: string; created_at: string; resolved: boolean }[]> {
  const res = await fetch(`${BASE_URL}/api/mentions/${encodeURIComponent(itemId)}/replies`);
  if (!res.ok) throw new Error(`Failed to list replies: ${res.status}`);
  const data = await res.json();
  return data.replies || [];
}
