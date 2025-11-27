/**
 * Marketplace Page
 * 
 * Main page for resource marketplace with all components.
 */

import React from 'react';
import { MarketplaceDashboard } from '@/components/marketplace/MarketplaceDashboard';
import { ResourceMap } from '@/components/marketplace/ResourceMap';
import { RequestBoard } from '@/components/marketplace/RequestBoard';

export const MarketplacePage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <MarketplaceDashboard />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ResourceMap />
        <RequestBoard />
      </div>
    </div>
  );
};

export default MarketplacePage;

