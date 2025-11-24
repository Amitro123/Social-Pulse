/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState } from 'react';
import { CampaignDraft, TopicSummary } from '../types';
import { generateCampaignProposal } from '../services/geminiService';
import { X, Sparkles, Send, Copy, Loader2 } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  selectedTopic: TopicSummary | null;
}

const CampaignModal: React.FC<Props> = ({ isOpen, onClose, selectedTopic }) => {
  const [topic, setTopic] = useState(selectedTopic?.topic || '');
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState<CampaignDraft | null>(null);

  // Update internal state if selectedTopic changes
  React.useEffect(() => {
    if (selectedTopic) {
        setTopic(selectedTopic.topic);
        setDraft(null); // Reset draft on new topic
    }
  }, [selectedTopic]);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!topic) return;
    setLoading(true);
    setDraft(null);
    try {
        const sentiment = selectedTopic?.avgSentiment && selectedTopic.avgSentiment < 50 ? 'Negative' : 'Neutral';
        const result = await generateCampaignProposal(
            topic, 
            sentiment, 
            selectedTopic?.platforms[0] || 'Social Media'
        );
        setDraft(result);
    } catch (e) {
        console.error(e);
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50">
            <div>
                <h3 className="text-xl font-bold text-gray-900">New Campaign Strategy</h3>
                <p className="text-sm text-gray-500">AI-powered response & content generation</p>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full text-gray-500 transition-colors">
                <X className="w-5 h-5" />
            </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto flex-1">
            {!draft ? (
                <div className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Campaign Topic / Issue</label>
                        <input 
                            type="text" 
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                            placeholder="e.g., Login issues on mobile app"
                        />
                        {selectedTopic && (
                            <p className="mt-2 text-xs text-gray-500">
                                based on <span className="font-bold">{selectedTopic.count}</span> recent mentions with avg sentiment <span className="font-bold">{selectedTopic.avgSentiment}/100</span>
                            </p>
                        )}
                    </div>
                    
                    <button 
                        onClick={handleGenerate}
                        disabled={loading || !topic}
                        className="w-full py-4 bg-gray-900 text-white rounded-xl font-bold text-lg hover:bg-gray-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-gray-200"
                    >
                        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
                        {loading ? 'Analyzing & Generating...' : 'Generate Proposal'}
                    </button>
                </div>
            ) : (
                <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
                    <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                        <h4 className="text-sm font-bold text-emerald-800 uppercase tracking-wide mb-2">Strategic Approach</h4>
                        <p className="text-gray-800 text-sm leading-relaxed">{draft.strategy}</p>
                    </div>

                    <div>
                         <h4 className="text-sm font-bold text-gray-500 uppercase tracking-wide mb-2 flex items-center justify-between">
                            Draft Content
                            <button className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                <Copy className="w-3 h-3" /> Copy
                            </button>
                        </h4>
                        <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 text-gray-800 italic relative">
                            "{draft.content}"
                        </div>
                    </div>

                    <div>
                        <h4 className="text-sm font-bold text-gray-500 uppercase tracking-wide mb-2">Recommended Channels</h4>
                        <div className="flex gap-2">
                            {draft.channels.map((ch, i) => (
                                <span key={i} className="px-3 py-1 bg-gray-100 rounded-full text-xs font-semibold text-gray-700 border border-gray-200">
                                    {ch}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>

        {/* Footer */}
        {draft && (
            <div className="p-4 border-t border-gray-100 bg-gray-50 flex gap-3">
                 <button 
                    onClick={() => setDraft(null)}
                    className="flex-1 py-3 bg-white border border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-colors"
                >
                    Regenerate
                </button>
                <button 
                    onClick={onClose}
                    className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-blue-200"
                >
                    <Send className="w-4 h-4" />
                    Approve & Launch
                </button>
            </div>
        )}
      </div>
    </div>
  );
};

export default CampaignModal;
