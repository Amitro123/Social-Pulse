/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/

export type Platform = 'Reddit' | 'Google Search' | 'LinkedIn' | 'Twitter' | 'All';
export type Category = 'Complaint' | 'Question' | 'Review' | 'Praise' | 'All';
export type Entity = 'Taboola' | 'Realize' | 'All';
export type Sentiment = 'Positive' | 'Neutral' | 'Negative';
export type DateRange = '24h' | '7d' | '30d';

export interface Mention {
  id: string;
  entity: string;
  platform: Platform;
  category: Category;
  sentiment: Sentiment;
  sentimentScore: number; // 0 to 100
  text: string;
  author: string;
  date: string; // ISO timestamp from backend
  url: string;
  topic: string;
  // Demo-only extended fields for UI response tracking
  responseStatus?: 'pending' | 'sent' | 'ignored';
  actionable?: boolean;
  replies?: Reply[];
}

export interface TopicSummary {
  id: string;
  topic: string;
  count: number;
  avgSentiment: number; // 0 to 100
  sentimentLabel: Sentiment;
  platforms: Platform[];
  sampleQuote: string;
}

export interface CampaignDraft {
  topic: string;
  strategy: string;
  content: string;
  channels: string[];
}

export interface Reply {
  id: string;
  by: 'AI' | 'Taboola Employee';
  content: string;
  createdAt: string; // ISO
  resolved?: boolean;
}

export interface RecentCampaign {
  id: string;
  topic: string;
  createdAt: string; // ISO
  summary: string;
  sentiment: Sentiment;
  triggerCount?: number;
}

export interface FilterState {
  entity: Entity;
  platform: Platform;
  dateRange: DateRange;
  category: Category;
}

export interface GeneratedImage {
  id: string;
  prompt: string;
  data: string;
}

export interface SearchResultItem {
  title: string;
  url: string;
}

// Extend Window for AI Studio
declare global {
  interface AIStudio {
    hasSelectedApiKey: () => Promise<boolean>;
    openSelectKey: () => Promise<void>;
  }
  interface Window {
      aistudio?: AIStudio;
  }
}