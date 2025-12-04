import React from 'react';

export const Progress = ({ value = 0, className = '' }: { value: number; className?: string }) => (
  <div className={`w-full bg-gray-200 rounded-full h-2 overflow-hidden ${className}`}>
    <div
      className="bg-blue-600 h-full transition-all duration-300"
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);
