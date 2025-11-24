const BASE_URL = 'http://localhost:8000';

export interface Campaign {
  id: string;
  topic: string;
  summary?: string;
  sentiment?: string;
  trigger_count?: number;
  created_at: string;
}

export async function listCampaigns(limit = 20): Promise<Campaign[]> {
  const res = await fetch(`${BASE_URL}/api/campaigns?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to list campaigns: ${res.status}`);
  return res.json();
}

export async function createCampaign(input: Partial<Campaign> & { topic: string }): Promise<Campaign> {
  const res = await fetch(`${BASE_URL}/api/campaigns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(`Failed to create campaign: ${res.status}`);
  return res.json();
}
