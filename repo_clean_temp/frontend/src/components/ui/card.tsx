import React from 'react';

export const Card = ({ className = '', children }: { className?: string; children: React.ReactNode }) => (
  <div className={`bg-white rounded-lg shadow-md border border-gray-200 ${className}`}>
    {children}
  </div>
);

export const CardHeader = ({ className = '', children }: { className?: string; children: React.ReactNode }) => (
  <div className={`px-6 py-4 border-b border-gray-200 ${className}`}>
    {children}
  </div>
);

export const CardTitle = ({ className = '', children }: { className?: string; children: React.ReactNode }) => (
  <h2 className={`text-lg font-semibold text-gray-900 ${className}`}>
    {children}
  </h2>
);

export const CardContent = ({ className = '', children }: { className?: string; children: React.ReactNode }) => (
  <div className={`px-6 py-4 ${className}`}>
    {children}
  </div>
);
