/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React from 'react';

interface Props {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
  averageRating: number;
}

const SentimentOverview: React.FC<Props> = ({ positive, neutral, negative, total, averageRating }) => {
  // Calculate percentages for the chart
  const posPct = total > 0 ? (positive / total) * 100 : 0;
  const neuPct = total > 0 ? (neutral / total) * 100 : 0;
  const negPct = total > 0 ? (negative / total) * 100 : 0;

  // SVG Chart Calculations
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  
  // Dash offsets
  // The circle is drawn counter-clockwise usually or we rotate it.
  // We will stack segments using dasharray/dashoffset
  
  // Total circumference is ~377
  // Green (Pos) starts at 0
  // Blue (Neu) starts after Green
  // Red (Neg) starts after Blue
  
  const posLength = (posPct / 100) * circumference;
  const neuLength = (neuPct / 100) * circumference;
  const negLength = (negPct / 100) * circumference;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col h-full">
      <h2 className="text-lg font-bold text-gray-900 mb-6">Overall Sentiment</h2>
      
      <div className="flex items-center justify-center sm:justify-between gap-6 flex-wrap">
        {/* Donut Chart */}
        <div className="relative w-40 h-40 flex-shrink-0">
          <svg viewBox="0 0 160 160" className="transform -rotate-90 w-full h-full">
            {/* Background Circle */}
            <circle cx="80" cy="80" r={radius} fill="transparent" stroke="#f3f4f6" strokeWidth="20" />
            
            {/* Positive Segment (Green) */}
            <circle 
              cx="80" cy="80" r={radius} 
              fill="transparent" 
              stroke="#10b981" 
              strokeWidth="20" 
              strokeDasharray={`${posLength} ${circumference}`}
              className="transition-all duration-1000 ease-out"
            />
            
            {/* Neutral Segment (Blue) */}
            <circle 
              cx="80" cy="80" r={radius} 
              fill="transparent" 
              stroke="#3b82f6" 
              strokeWidth="20" 
              strokeDasharray={`${neuLength} ${circumference}`}
              strokeDashoffset={-posLength}
              className="transition-all duration-1000 ease-out"
            />
            
            {/* Negative Segment (Red) */}
            <circle 
              cx="80" cy="80" r={radius} 
              fill="transparent" 
              stroke="#ef4444" 
              strokeWidth="20" 
              strokeDasharray={`${negLength} ${circumference}`}
              strokeDashoffset={-(posLength + neuLength)}
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-bold text-gray-900">{total}</span>
            <span className="text-xs text-gray-500 uppercase tracking-wide">Mentions</span>
          </div>
        </div>

        {/* Legend & Rating */}
        <div className="flex-1 space-y-4 min-w-[160px]">
            <div className="flex items-center gap-2">
                <div className="flex gap-1 text-amber-400">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <svg key={star} className={`w-5 h-5 ${star <= Math.round(averageRating) ? 'fill-current' : 'text-gray-200'}`} viewBox="0 0 24 24">
                            <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                        </svg>
                    ))}
                </div>
                <span className="text-xl font-bold text-gray-900">{averageRating.toFixed(1)}/5</span>
            </div>
            
            <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                        <span className="text-gray-600">Positive</span>
                    </div>
                    <span className="font-bold text-gray-900">{Math.round(posPct)}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                        <span className="text-gray-600">Neutral</span>
                    </div>
                    <span className="font-bold text-gray-900">{Math.round(neuPct)}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-red-500"></span>
                        <span className="text-gray-600">Negative</span>
                    </div>
                    <span className="font-bold text-gray-900">{Math.round(negPct)}%</span>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default SentimentOverview;
