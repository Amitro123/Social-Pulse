
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState, useEffect } from 'react';
import { Mention, TopicSummary, FilterState, Entity, Platform, Category, Sentiment } from './types';
import SentimentOverview from './components/SentimentOverview';
import ActionPanel from './components/ActionPanel';
import HotTopics from './components/HotTopics';
import CampaignModal from './components/CampaignModal';
import { Filter, LayoutGrid, Bell, Search, Key, ExternalLink, ChevronDown, User } from 'lucide-react';
import { fetchMentions, APIMention, postReply } from './services/mentionsService';
import { listCampaigns, createCampaign } from './services/campaignsService';
import { Reply, RecentCampaign } from './types';

// Demo-only ManualReply component used in the Reply Modal
const ManualReply: React.FC<{ onSend: (text: string) => void }> = ({ onSend }) => {
    const [text, setText] = useState('');
    return (
        <div className="space-y-2">
            <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Write a manual reply..."
                className="w-full min-h-[100px] p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex justify-end">
                <button
                    onClick={() => text.trim() && onSend(text.trim())}
                    className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800 disabled:opacity-50"
                    disabled={!text.trim()}
                >
                    Send Manual Reply (Demo)
                </button>
            </div>
        </div>
    );
};

// Helper: map backend APIMention to frontend Mention type
function mapAPIMention(api: APIMention): Mention {
    const platformMap = (p: string): Platform => {
        const norm = p.toLowerCase();
        if (norm.includes('reddit')) return 'Reddit';
        if (norm.includes('linkedin')) return 'LinkedIn';
        if (norm.includes('twitter') || norm.includes('x')) return 'Twitter';
        if (norm.includes('google')) return 'Google Search';
        return 'Google Search';
    };
    const categoryMap = (c?: string | null): Category => {
        const v = (c || '').toLowerCase();
        if (v === 'complaint') return 'Complaint';
        if (v === 'question') return 'Question';
        if (v === 'review') return 'Review';
        if (v === 'praise') return 'Praise';
        return 'Review';
    };
    const sentimentMap = (s?: string | null): Sentiment => {
        const v = (s || '').toLowerCase();
        if (v === 'positive') return 'Positive';
        if (v === 'negative') return 'Negative';
        return 'Neutral';
    };
    return {
        id: api.id,
        entity: api.entity_mentioned?.[0] || 'Taboola',
        platform: platformMap(api.platform),
        category: categoryMap(api.category),
        sentiment: sentimentMap(api.sentiment),
        sentimentScore: Math.round(((api.sentiment_score ?? 0) + 1) * 50), // map -1..1 -> 0..100
        text: api.text || '',
        author: api.author || 'Unknown',
        date: api.timestamp || '',
        url: api.url || '#',
        topic: (api.topics && api.topics[0]) || 'General',
        responseStatus: (api as any).response_status || 'pending',
        actionable: (api as any).actionable ?? false,
        replies: [],
    };
}

const App: React.FC = () => {
    const [hasApiKey, setHasApiKey] = useState(false);
    const [mentions, setMentions] = useState<Mention[]>([]);
    const [topics, setTopics] = useState<TopicSummary[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [recentCampaigns, setRecentCampaigns] = useState<RecentCampaign[]>([]);
    const [replyingTo, setReplyingTo] = useState<string | null>(null);
    const [filters, setFilters] = useState<FilterState>({
        entity: 'All',
        platform: 'All',
        dateRange: '7d',
        category: 'All'
    });
    
    // Modal State
    const [isCampaignModalOpen, setIsCampaignModalOpen] = useState(false);
    const [selectedTopicForCampaign, setSelectedTopicForCampaign] = useState<TopicSummary | null>(null);

    // Initial API Key check (for AI studio features unrelated to mentions fetch)
    useEffect(() => {
        const checkKey = async () => {
             if (window.aistudio && window.aistudio.hasSelectedApiKey) {
                const hasKey = await window.aistudio.hasSelectedApiKey();
                setHasApiKey(hasKey);
             } else {
                 setHasApiKey(true);
             }
        };
        checkKey();
        // Load campaigns persisted in backend
        (async () => {
            try {
                const list = await listCampaigns(20);
                setRecentCampaigns(list.map(c => ({
                    id: c.id,
                    topic: c.topic,
                    createdAt: c.created_at,
                    summary: c.summary || '',
                    sentiment: 'Neutral',
                    triggerCount: c.trigger_count ?? undefined,
                })));
            } catch (e) {
                // ignore load errors silently for now
            }
        })();
    }, []);

    // Fetch mentions from backend when filters change
    useEffect(() => {
        const load = async () => {
            setLoading(true);
            setError(null);
            try {
                const q: any = {};
                if (filters.entity !== 'All') q.entity = filters.entity;
                if (filters.category !== 'All') q.category = filters.category.toLowerCase();
                // Backend API does not support platform filter directly; apply client-side below
                q.days = filters.dateRange === '24h' ? 1 : filters.dateRange === '7d' ? 7 : 30;
                q.limit = 100;
                const apiList = await fetchMentions(q);
                let mapped = apiList.map(mapAPIMention);
                if (filters.platform !== 'All') {
                    mapped = mapped.filter(m => m.platform === filters.platform);
                }
                setMentions(mapped);
                // Build simple topic summaries from mentions.topics
                const counts: Record<string, { count: number; scores: number; platforms: Set<Platform>; sample: string }>= {};
                for (const m of mapped) {
                    const t = m.topic || 'General';
                    if (!counts[t]) counts[t] = { count: 0, scores: 0, platforms: new Set<Platform>(), sample: m.text };
                    counts[t].count += 1;
                    counts[t].scores += m.sentimentScore;
                    counts[t].platforms.add(m.platform);
                }
                const topicsArr: TopicSummary[] = Object.entries(counts).map(([topic, v], i) => ({
                    id: `t-${i}`,
                    topic,
                    count: v.count,
                    avgSentiment: v.count ? Math.round(v.scores / v.count) : 0,
                    sentimentLabel: 'Neutral' as Sentiment,
                    platforms: Array.from(v.platforms),
                    sampleQuote: v.sample,
                })).sort((a, b) => b.count - a.count);
                setTopics(topicsArr);
            } catch (e: any) {
                setError(e?.message || 'Failed to load mentions.');
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [filters.entity, filters.platform, filters.category, filters.dateRange]);

    const handleSelectKey = async () => {
        if (window.aistudio && window.aistudio.openSelectKey) {
            await window.aistudio.openSelectKey();
            setHasApiKey(true);
        }
    };

    // Current filtered mentions already applied in fetch step
    const filteredMentions = mentions;
    
    const stats = {
        total: filteredMentions.length,
        positive: filteredMentions.filter(m => m.sentiment === 'Positive').length,
        neutral: filteredMentions.filter(m => m.sentiment === 'Neutral').length,
        negative: filteredMentions.filter(m => m.sentiment === 'Negative').length,
        avgRating: 3.8, // Placeholder until ratings are surfaced in UI
        complaints: filteredMentions.filter(m => m.category === 'Complaint').length,
        questions: filteredMentions.filter(m => m.category === 'Question').length,
        reviews: filteredMentions.filter(m => m.category === 'Review').length,
        praises: filteredMentions.filter(m => m.category === 'Praise').length,
    };

    // Dynamic response statistics
    const repliesSent = filteredMentions.filter(m => m.responseStatus === 'sent').length;
    const activeCampaigns = filteredMentions.filter(m => m.actionable).length;
    const pendingResponses = filteredMentions.filter(m => m.responseStatus === 'pending').length;

    const handleStartCampaign = (topic?: TopicSummary) => {
        setSelectedTopicForCampaign(topic || null);
        setIsCampaignModalOpen(true);
        if (topic) {
            // Persist campaign via backend
            (async () => {
                try {
                    await createCampaign({
                        topic: topic.topic,
                        summary: `AI proposal initiated for “${topic.topic}”`,
                        sentiment: topic.avgSentiment >= 60 ? 'positive' : topic.avgSentiment <= 40 ? 'negative' : 'neutral',
                        trigger_count: topic.count,
                    });
                    const list = await listCampaigns(20);
                    setRecentCampaigns(list.map(c => ({
                        id: c.id,
                        topic: c.topic,
                        createdAt: c.created_at,
                        summary: c.summary || '',
                        sentiment: 'Neutral',
                        triggerCount: c.trigger_count ?? undefined,
                    })));
                } catch (e) {
                    // fallback: keep ephemeral list
                    const entry: RecentCampaign = {
                        id: `c-${Date.now()}`,
                        topic: topic.topic,
                        createdAt: new Date().toISOString(),
                        summary: `AI proposal initiated for “${topic.topic}”`,
                        sentiment: topic.avgSentiment >= 60 ? 'Positive' : topic.avgSentiment <= 40 ? 'Negative' : 'Neutral',
                        triggerCount: topic.count,
                    };
                    setRecentCampaigns(prev => [entry, ...prev].slice(0, 10));
                }
            })();
        }
    };

    // Reply handlers (demo-only)
    const openReply = (id: string) => setReplyingTo(id);
    const closeReply = () => setReplyingTo(null);
    const sendReply = async (id: string, by: 'AI' | 'Taboola Employee', content: string) => {
        try {
            await postReply(id, by, content);
            // Refresh mentions from backend to ensure state is consistent/persistent
            const q: any = {};
            if (filters.entity !== 'All') q.entity = filters.entity;
            if (filters.category !== 'All') q.category = filters.category.toLowerCase();
            q.days = filters.dateRange === '24h' ? 1 : filters.dateRange === '7d' ? 7 : 30;
            q.limit = 100;
            const apiList = await fetchMentions(q);
            let mapped = apiList.map(mapAPIMention);
            if (filters.platform !== 'All') mapped = mapped.filter(m => m.platform === filters.platform);
            setMentions(mapped);
        } catch (e) {
            // fall back to local update if API fails
            const reply: Reply = { id: `r-${Date.now()}`, by, content, createdAt: new Date().toISOString(), resolved: true };
            setMentions(prev => prev.map(m => m.id === id ? { ...m, replies: [...(m.replies || []), reply], responseStatus: 'sent' } : m));
        } finally {
            setReplyingTo(null);
        }
    };

    if (!hasApiKey) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
                 <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md text-center space-y-6">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto text-blue-600">
                        <Key className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900">API Key Required</h2>
                    <p className="text-gray-500">To use the AI Campaign generation features, please select a Google Cloud Project with billing enabled.</p>
                    <button 
                        onClick={handleSelectKey}
                        className="w-full py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-colors"
                    >
                        Select Paid API Key
                    </button>
                    <a href="https://ai.google.dev/gemini-api/docs/billing" target="_blank" rel="noreferrer" className="text-xs text-blue-500 hover:underline inline-flex items-center gap-1">
                        Billing Documentation <ExternalLink className="w-3 h-3"/>
                    </a>
                 </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#f9fafb] text-[#1f2937] pb-10 font-sans">
            
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
                <div className="max-w-[1600px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                         <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white shadow-md">
                            <LayoutGrid className="w-5 h-5" />
                         </div>
                         <h1 className="text-xl font-bold tracking-tight text-gray-900">SentimentPulse</h1>
                    </div>
                    
                    <div className="flex items-center gap-4">
                        <div className="relative hidden md:block">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input 
                                type="text" 
                                placeholder="Search mentions..." 
                                className="pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
                            />
                        </div>
                        <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-full relative">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
                        </button>
                        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600">
                             <User className="w-5 h-5" />
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-[1600px] mx-auto px-4 sm:px-6 pt-6 space-y-6">
                
                {/* Filters */}
                <div className="flex flex-wrap items-center gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                    <div className="flex items-center gap-2 text-gray-500 mr-2">
                        <Filter className="w-4 h-4" />
                        <span className="text-sm font-semibold uppercase tracking-wide">Filters</span>
                    </div>
                    
                    {/* Entity Filter */}
                    <div className="relative">
                        <select 
                            value={filters.entity}
                            onChange={(e) => setFilters({...filters, entity: e.target.value as Entity})}
                            className="appearance-none pl-4 pr-10 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer hover:bg-gray-100 transition-colors"
                        >
                            <option value="All">All Entities</option>
                            <option value="Taboola">Taboola</option>
                            <option value="Realize">Realize</option>
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                    </div>

                    {/* Platform Filter */}
                    <div className="relative">
                        <select 
                            value={filters.platform}
                            onChange={(e) => setFilters({...filters, platform: e.target.value as Platform})}
                            className="appearance-none pl-4 pr-10 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer hover:bg-gray-100 transition-colors"
                        >
                            <option value="All">All Platforms</option>
                            <option value="Reddit">Reddit</option>
                            <option value="Twitter">Twitter</option>
                            <option value="LinkedIn">LinkedIn</option>
                            <option value="Google Search">Google Search</option>
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                    </div>

                     {/* Category Filter */}
                     <div className="relative">
                        <select 
                            value={filters.category}
                            onChange={(e) => setFilters({...filters, category: e.target.value as Category})}
                            className="appearance-none pl-4 pr-10 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer hover:bg-gray-100 transition-colors"
                        >
                            <option value="All">All Categories</option>
                            <option value="Complaint">Complaints</option>
                            <option value="Question">Questions</option>
                            <option value="Review">Reviews</option>
                            <option value="Praise">Praise</option>
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                    </div>
                </div>

                {/* Top Row: Overview & Actions */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Sentiment Overview (1/3) */}
                    <div className="lg:col-span-1 h-[340px]">
                        <SentimentOverview 
                            total={stats.total}
                            positive={stats.positive}
                            neutral={stats.neutral}
                            negative={stats.negative}
                            averageRating={stats.avgRating}
                        />
                    </div>
                    
                    {/* Action Panel (2/3) */}
                    <div className="lg:col-span-2 h-[340px]">
                        <ActionPanel 
                            complaints={stats.complaints}
                            questions={stats.questions}
                            reviews={stats.reviews}
                            praises={stats.praises}
                            campaignsCount={recentCampaigns.length || activeCampaigns}
                            repliesSent={repliesSent}
                            pendingResponses={pendingResponses}
                            onStartCampaign={() => handleStartCampaign()}
                        />
                    </div>
                </div>

            {/* Bottom Row: Hot Topics */}
            <div className="min-h-[400px]">
                <HotTopics 
                    topics={topics} 
                    onTopicClick={handleStartCampaign}
                />
            </div>

            {/* Mentions Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-bold text-gray-900">Latest Mentions</h2>
                    {loading && <span className="text-sm text-gray-500">Loading...</span>}
                </div>
                {error ? (
                    <div className="text-red-600 text-sm">{error}</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                            <thead>
                                <tr className="text-left text-gray-500 border-b">
                                    <th className="py-2 pr-4">Source</th>
                                    <th className="py-2 pr-4">Entity</th>
                                    <th className="py-2 pr-4">Text</th>
                                    <th className="py-2 pr-4">Author</th>
                                    <th className="py-2 pr-4">Date</th>
                                    <th className="py-2 pr-4">Respond</th>
                                    <th className="py-2 pr-4">Link</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredMentions.map(m => (
                                    <tr key={m.id} className="border-b last:border-0">
                                        <td className="py-2 pr-4 whitespace-nowrap">{m.platform}</td>
                                        <td className="py-2 pr-4 whitespace-nowrap">{m.entity}</td>
                                        <td className="py-2 pr-4 max-w-[520px] truncate" title={m.text}>{m.text.slice(0, 80)}</td>
                                        <td className="py-2 pr-4 whitespace-nowrap">{m.author}</td>
                                        <td className="py-2 pr-4 whitespace-nowrap">{m.date ? new Date(m.date).toLocaleString() : '—'}</td>
                                        <td className="py-2 pr-4 whitespace-nowrap">
                                            <button onClick={() => openReply(m.id)} className="px-3 py-1 bg-blue-600 text-white rounded-lg text-xs hover:bg-blue-700">Reply</button>
                                        </td>
                                        <td className="py-2 pr-4 whitespace-nowrap">
                                            {m.url && m.url !== '#' ? (
                                                <a href={m.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">Open</a>
                                            ) : (
                                                <span className="text-gray-400">N/A</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Recent AI Campaigns */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                <h2 className="text-lg font-bold text-gray-900 mb-3">Recent AI Campaigns (Demo)</h2>
                {recentCampaigns.length === 0 ? (
                    <p className="text-sm text-gray-500">No campaigns yet. Generate from Hot Topics or Start Campaign.</p>
                ) : (
                    <ul className="space-y-2">
                        {recentCampaigns.map(c => (
                            <li key={c.id} className="p-3 rounded-lg border border-gray-100 flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-semibold text-gray-900">{c.topic}</p>
                                    <p className="text-xs text-gray-500">{new Date(c.createdAt).toLocaleString()} • {c.summary}</p>
                                </div>
                                {typeof c.triggerCount === 'number' && (
                                    <span className="text-xs text-gray-500">{c.triggerCount} mentions</span>
                                )}
                            </li>
                        ))}
                    </ul>
                )}
                <p className="mt-2 text-xs text-gray-400">Demo only – proposals are not yet persisted.</p>
            </div>

        </main>

        {/* Modals */}
        <CampaignModal 
            isOpen={isCampaignModalOpen}
            onClose={() => setIsCampaignModalOpen(false)}
            selectedTopic={selectedTopicForCampaign}
        />
        {/* Reply Modal (Demo only) */}
        {replyingTo && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
                <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden">
                    <div className="p-4 border-b flex items-center justify-between">
                        <h3 className="text-lg font-bold">Respond to Mention</h3>
                        <button onClick={closeReply} className="text-gray-500 hover:text-gray-700">Close</button>
                    </div>
                    <div className="p-4 space-y-3">
                        <button onClick={() => sendReply(replyingTo, 'AI', 'Thank you for your feedback. Our team is reviewing this and will follow up with next steps.')} className="w-full py-2 bg-emerald-600 text-white rounded-lg text-sm">Send AI Reply (Demo)</button>
                        <ManualReply onSend={(text) => sendReply(replyingTo, 'Taboola Employee', text)} />
                        <p className="text-xs text-gray-400">Demo only – replies are stored in session state.</p>
                    </div>
                </div>
            </div>
        )}
    </div>
    );
};

export default App;
