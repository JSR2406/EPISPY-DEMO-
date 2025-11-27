/**
 * Resource Map Component
 * 
 * Interactive map showing supply and demand by location.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { MapPin, Package, AlertCircle } from 'lucide-react';

interface ResourceLocation {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  supply_count: number;
  demand_count: number;
  resource_type: string;
}

export const ResourceMap: React.FC = () => {
  const [locations, setLocations] = useState<ResourceLocation[]>([]);
  const [selectedResource, setSelectedResource] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch resource locations from API
    // For now, use placeholder data
    setLocations([]);
    setLoading(false);
  }, [selectedResource]);

  if (loading) {
    return (
      <Card variant="elevated" padding="lg">
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="elevated" padding="lg">
      <CardHeader>
        <CardTitle>Resource Map</CardTitle>
        <CardDescription>Supply and demand by location</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Map placeholder - would integrate with Mapbox GL */}
        <div className="w-full h-96 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <MapPin className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <p className="text-text-secondary">Map visualization</p>
            <p className="text-sm text-text-tertiary mt-2">
              Integrate with Mapbox GL for interactive map
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-success-main rounded-full"></div>
            <span className="text-sm text-text-secondary">Supply Available</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-error-main rounded-full"></div>
            <span className="text-sm text-text-secondary">High Demand</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-warning-main rounded-full"></div>
            <span className="text-sm text-text-secondary">Moderate Need</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ResourceMap;

