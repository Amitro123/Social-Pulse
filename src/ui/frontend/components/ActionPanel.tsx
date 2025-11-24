/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React from 'react';
import { AlertCircle, MessageCircle, Star, ThumbsUp, Megaphone, Send, Clock, Layers } from 'lucide-react';

interface Props {
  complaints: number;
  questions: number;
  reviews: number;
  praises: number;
  campaignsCount: number;
  repliesSent: number;
  pendingResponses: number;
  onStartCampaign: () => void;
  onViewAll?: () => void;
}

const ActionPanel: React.FC<Props> = ({ 
  complaints, 
  questions, 
  reviews, 
  praises, 
  campaignsCount,
  repliesSent,
  pendingResponses,
  onStartCampaign, 
  onViewAll 
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
      {/* Left: Action Required */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                Action Required
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
            </h2>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="p-3 rounded-xl bg-red-50 border border-red-100 flex flex-col items-center justify-center text-center">
                <AlertCircle className="w-5 h-5 text-red-500 mb-1" />
                <span className="text-xl font-bold text-gray-900">{complaints}</span>
                <span className="text-[10px] font-medium text-red-600 uppercase tracking-wide">Complaints</span>
            </div>
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-100 flex flex-col items-center justify-center text-center">
                <MessageCircle className="w-5 h-5 text-blue-500 mb-1" />
                <span className="text-xl font-bold text-gray-900">{questions}</span>
                <span className="text-[10px] font-medium text-blue-600 uppercase tracking-wide">Questions</span>
            </div>
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-100 flex flex-col items-center justify-center text-center">
                <Star className="w-5 h-5 text-amber-500 mb-1" />
                <span className="text-xl font-bold text-gray-900">{reviews}</span>
                <span className="text-[10px] font-medium text-amber-600 uppercase tracking-wide">Reviews</span>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100 flex flex-col items-center justify-center text-center">
                <ThumbsUp className="w-5 h-5 text-emerald-500 mb-1" />
                <span className="text-xl font-bold text-gray-900">{praises}</span>
                <span className="text-[10px] font-medium text-emerald-600 uppercase tracking-wide">Praises</span>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
            {onViewAll && (
              <button 
                  onClick={onViewAll}
                  className="flex-1 py-2.5 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
              >
                  View All Mentions
              </button>
            )}
            <button 
                onClick={onStartCampaign}
                className="flex-1 py-2.5 px-4 bg-gray-900 hover:bg-gray-800 text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2 shadow-lg shadow-gray-200"
            >
                <Megaphone className="w-4 h-4" />
                Start Campaign
            </button>
        </div>
      </div>

      {/* Right: Response Statistics */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col">
        <h2 className="text-lg font-bold text-gray-900 mb-6">Response Statistics</h2>
        
        <div className="space-y-4 flex-1">
            <div className="flex items-center justify-between p-4 rounded-xl border border-gray-100 bg-gray-50/50">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg">
                        <Send className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-600">Replies Sent</p>
                        <p className="text-xs text-gray-400">Past 30 Days</p>
                    </div>
                </div>
                <span className="text-2xl font-bold text-gray-900">{repliesSent}</span>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl border border-gray-100 bg-gray-50/50">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                        <Layers className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-600">Active Campaigns</p>
                        <p className="text-xs text-gray-400">Current running</p>
                    </div>
                </div>
                <span className="text-2xl font-bold text-gray-900">{campaignsCount}</span>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl border border-gray-100 bg-gray-50/50">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-100 text-amber-600 rounded-lg">
                        <Clock className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-600">Pending</p>
                        <p className="text-xs text-gray-400">Needs attention</p>
                    </div>
                </div>
                <span className="text-2xl font-bold text-gray-900">{pendingResponses}</span>
            </div>
        </div>
      </div>
    </div>
  );
};

export default ActionPanel;
