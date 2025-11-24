/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState } from 'react';
import { TopicSummary } from '../types';
import { ChevronRight, ArrowUpRight, MessageSquare, Quote } from 'lucide-react';

interface Props {
  topics: TopicSummary[];
  onTopicClick: (topic: TopicSummary) => void;
}

const HotTopics: React.FC<Props> = ({ topics, onTopicClick }) => {
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  const toggleExpand = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedTopic(expandedTopic === id ? null : id);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-full">
      <div className="p-6 border-b border-gray-100 flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900">Trending Hot Topics</h2>
        <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-full">Live Analysis</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-600">
          <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-100">
            <tr>
              <th className="px-6 py-4">Topic / Keyword</th>
              <th className="px-6 py-4 text-center">Volume</th>
              <th className="px-6 py-4 text-center">Sentiment</th>
              <th className="px-6 py-4">Platforms</th>
              <th className="px-6 py-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {topics.map((topic) => (
              <React.Fragment key={topic.id}>
                <tr 
                    className="hover:bg-gray-50 transition-colors cursor-pointer group"
                    onClick={() => onTopicClick(topic)}
                >
                  <td className="px-6 py-4">
                    <span className="font-semibold text-gray-900 block mb-1">{topic.topic}</span>
                    {expandedTopic === topic.id && (
                        <div className="text-xs text-gray-500 flex items-center gap-1 mt-2">
                             <Quote className="w-3 h-3" /> "{topic.sampleQuote}"
                        </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {topic.count}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex flex-col items-center gap-1">
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                                className={`h-full rounded-full ${
                                    topic.avgSentiment >= 60 ? 'bg-emerald-500' :
                                    topic.avgSentiment >= 40 ? 'bg-blue-400' : 'bg-red-500'
                                }`}
                                style={{ width: `${topic.avgSentiment}%` }}
                            ></div>
                        </div>
                        <span className={`text-xs font-bold ${
                            topic.avgSentiment >= 60 ? 'text-emerald-600' :
                            topic.avgSentiment >= 40 ? 'text-blue-500' : 'text-red-500'
                        }`}>
                            {topic.avgSentiment}/100
                        </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex -space-x-2 overflow-hidden">
                        {topic.platforms.includes('Reddit') && (
                            <div className="inline-block h-6 w-6 rounded-full bg-orange-100 ring-2 ring-white flex items-center justify-center text-[10px] font-bold text-orange-600" title="Reddit">R</div>
                        )}
                         {topic.platforms.includes('Twitter') && (
                            <div className="inline-block h-6 w-6 rounded-full bg-blue-100 ring-2 ring-white flex items-center justify-center text-[10px] font-bold text-blue-600" title="Twitter">X</div>
                        )}
                        {topic.platforms.includes('LinkedIn') && (
                            <div className="inline-block h-6 w-6 rounded-full bg-blue-800 ring-2 ring-white flex items-center justify-center text-[10px] font-bold text-white" title="LinkedIn">in</div>
                        )}
                        {topic.platforms.includes('Google Search') && (
                            <div className="inline-block h-6 w-6 rounded-full bg-white border border-gray-200 ring-2 ring-white flex items-center justify-center text-[10px] font-bold text-gray-600" title="Google">G</div>
                        )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button 
                        onClick={(e) => toggleExpand(topic.id, e)}
                        className="p-2 hover:bg-gray-200 rounded-full text-gray-400 hover:text-gray-600 transition-colors"
                    >
                         {expandedTopic === topic.id ? <ArrowUpRight className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                  </td>
                </tr>
                {/* Detailed Expansion Row */}
                {expandedTopic === topic.id && (
                    <tr className="bg-gray-50/50">
                        <td colSpan={5} className="px-6 py-4">
                            <div className="flex justify-between items-start">
                                <div>
                                    <h4 className="text-xs font-bold uppercase text-gray-500 mb-2">Sample Feedback</h4>
                                    <p className="text-sm text-gray-700 italic border-l-2 border-gray-300 pl-3">
                                        "{topic.sampleQuote}"
                                    </p>
                                </div>
                                <button className="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 mt-1">
                                    Analyze <MessageSquare className="w-3 h-3" />
                                </button>
                            </div>
                        </td>
                    </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default HotTopics;
