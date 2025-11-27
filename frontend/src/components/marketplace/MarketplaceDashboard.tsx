/**
 * Marketplace Dashboard Component
 * 
 * Main dashboard for resource marketplace with real-time updates,
 * supply-demand visualization, and resource matching.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Alert, AlertContainer } from '@/components/ui/Alert';
import { TrendingUp, TrendingDown, Activity, AlertCircle, Package, Users } from 'lucide-react';
import { motion } from 'framer-motion';

interface MarketplaceStats {
  total_providers: number;
  total_inventory_items: number;
  total_requests: number;
  open_requests: number;
  active_matches: number;
  pending_transfers: number;
  total_volunteers: number;
  active_deployments: number;
}

export const MarketplaceDashboard: React.FC = () => {
  const [stats, setStats] = useState<MarketplaceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMarketplaceStats();
    // Refresh every 30 seconds
    const interval = setInterval(fetchMarketplaceStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchMarketplaceStats = async () => {
    try {
      const response = await fetch('/api/v1/marketplace/dashboard/overview');
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error}
      </Alert>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2">Resource Marketplace</h1>
        <p className="text-text-secondary">
          Real-time resource matching and allocation system
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card variant="elevated" hover glow glowColor="primary">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">Total Providers</p>
                <p className="text-3xl font-bold text-text">{stats.total_providers}</p>
              </div>
              <Users className="h-12 w-12 text-primary-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card variant="elevated" hover glow glowColor="success">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">Available Inventory</p>
                <p className="text-3xl font-bold text-text">{stats.total_inventory_items}</p>
              </div>
              <Package className="h-12 w-12 text-success-main opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card variant="elevated" hover glow glowColor="warning">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">Open Requests</p>
                <p className="text-3xl font-bold text-text">{stats.open_requests}</p>
                <div className="flex items-center gap-1 mt-2">
                  <AlertCircle className="h-4 w-4 text-warning-main" />
                  <span className="text-sm text-warning-main">Needs attention</span>
                </div>
              </div>
              <Activity className="h-12 w-12 text-warning-main opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card variant="elevated" hover glow glowColor="info">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">Active Matches</p>
                <p className="text-3xl font-bold text-text">{stats.active_matches}</p>
                <div className="flex items-center gap-1 mt-2">
                  <TrendingUp className="h-4 w-4 text-info-main" />
                  <span className="text-sm text-info-main">Matching</span>
                </div>
              </div>
              <Activity className="h-12 w-12 text-info-main opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card variant="elevated" padding="lg">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common marketplace operations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary" leftIcon={<Package className="h-4 w-4" />}>
              Add Inventory
            </Button>
            <Button variant="outline" leftIcon={<AlertCircle className="h-4 w-4" />}>
              Create Request
            </Button>
            <Button variant="outline" leftIcon={<Users className="h-4 w-4" />}>
              Register Volunteer
            </Button>
            <Button variant="ghost" leftIcon={<Activity className="h-4 w-4" />}>
              View Analytics
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Supply-Demand Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card variant="elevated" padding="lg">
          <CardHeader>
            <CardTitle>Supply Status</CardTitle>
            <CardDescription>Current inventory levels</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Total Items</span>
                <Badge variant="success">{stats.total_inventory_items}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Active Providers</span>
                <Badge variant="primary">{stats.total_providers}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card variant="elevated" padding="lg">
          <CardHeader>
            <CardTitle>Demand Status</CardTitle>
            <CardDescription>Current request levels</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Open Requests</span>
                <Badge variant={stats.open_requests > 10 ? "critical" : "moderate"}>
                  {stats.open_requests}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Active Matches</span>
                <Badge variant="success">{stats.active_matches}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Pending Transfers</span>
                <Badge variant="warning">{stats.pending_transfers}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Volunteer Section */}
      <Card variant="elevated" padding="lg">
        <CardHeader>
          <CardTitle>Volunteer Network</CardTitle>
          <CardDescription>Medical staff volunteers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-text-secondary mb-2">Total Volunteers</p>
              <p className="text-2xl font-bold text-text">{stats.total_volunteers}</p>
            </div>
            <div>
              <p className="text-sm text-text-secondary mb-2">Active Deployments</p>
              <p className="text-2xl font-bold text-text">{stats.active_deployments}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MarketplaceDashboard;

