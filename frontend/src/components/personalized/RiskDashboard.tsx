/**
 * Personalized Risk Dashboard Component
 * 
 * Individual risk assessment dashboard with real-time updates,
 * exposure tracking, and personalized recommendations.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { 
  Shield, TrendingUp, MapPin, AlertTriangle, 
  CheckCircle2, Clock, Heart, Activity, AlertCircle
} from 'lucide-react';
import { motion } from 'framer-motion';

interface RiskScore {
  risk_score: number;
  risk_level: string;
  factors: {
    location_risk: number;
    travel_risk: number;
    exposure_risk: number;
    vulnerability_risk: number;
    behavior_risk: number;
    occupation_risk: number;
    household_risk: number;
  };
  contributing_factors: Array<{
    name: string;
    value: number;
    contribution: number;
    percentage: number;
  }>;
  recommendations: string[];
  calculated_at: string;
}

interface RiskDashboardProps {
  userId: string;
  currentLocation?: { latitude: number; longitude: number };
}

export const RiskDashboard: React.FC<RiskDashboardProps> = ({ 
  userId, 
  currentLocation 
}) => {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRiskScore();
    // Refresh every 5 minutes
    const interval = setInterval(fetchRiskScore, 300000);
    return () => clearInterval(interval);
  }, [userId, currentLocation]);

  const fetchRiskScore = async () => {
    try {
      const params = new URLSearchParams({ user_id: userId });
      if (currentLocation) {
        params.append('latitude', currentLocation.latitude.toString());
        params.append('longitude', currentLocation.longitude.toString());
      }

      const response = await fetch(`/api/v1/personal/risk-score?${params}`);
      if (!response.ok) throw new Error('Failed to fetch risk score');
      const data = await response.json();
      setRiskScore(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MODERATE': return 'moderate';
      default: return 'minimal';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'CRITICAL': return AlertTriangle;
      case 'HIGH': return AlertCircle;
      case 'MODERATE': return Clock;
      default: return CheckCircle2;
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

  if (!riskScore) return null;

  const RiskIcon = getRiskIcon(riskScore.risk_level);
  const riskColor = getRiskColor(riskScore.risk_level);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2">Personal Risk Assessment</h1>
        <p className="text-text-secondary">
          Your personalized epidemic risk score and recommendations
        </p>
      </div>

      {/* Main Risk Score Card */}
      <Card variant="elevated" hover glow glowColor={riskColor as any} padding="lg">
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-4">
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <RiskIcon className="h-16 w-16" />
                </motion.div>
                <div>
                  <h2 className="text-3xl font-bold text-text mb-1">
                    {riskScore.risk_score.toFixed(1)}/100
                  </h2>
                  <Badge variant={riskColor as any} size="lg" pulse={riskScore.risk_level === 'CRITICAL'}>
                    {riskScore.risk_level} Risk
                  </Badge>
                </div>
              </div>
              
              <p className="text-text-secondary mb-4">
                Last updated: {new Date(riskScore.calculated_at).toLocaleString()}
              </p>

              {/* Risk Gauge Visualization */}
              <div className="relative w-full h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-4">
                <motion.div
                  className={`h-full ${
                    riskScore.risk_level === 'CRITICAL' ? 'bg-error-main' :
                    riskScore.risk_level === 'HIGH' ? 'bg-warning-main' :
                    riskScore.risk_level === 'MODERATE' ? 'bg-risk-moderate' :
                    'bg-success-main'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${riskScore.risk_score}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Factors Breakdown */}
      <Card variant="elevated" padding="lg">
        <CardHeader>
          <CardTitle>Risk Factors</CardTitle>
          <CardDescription>Contributing factors to your risk score</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {riskScore.contributing_factors.map((factor, index) => (
              <motion.div
                key={factor.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-text">{factor.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-text-secondary">
                      {factor.percentage.toFixed(1)}%
                    </span>
                    <Badge variant={factor.value > 70 ? 'high' : factor.value > 40 ? 'moderate' : 'low'}>
                      {factor.value.toFixed(0)}
                    </Badge>
                  </div>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-primary-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${factor.value}%` }}
                    transition={{ delay: index * 0.1 + 0.3, duration: 0.5 }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card variant="elevated" padding="lg">
        <CardHeader>
          <CardTitle>Personalized Recommendations</CardTitle>
          <CardDescription>Actions to reduce your risk</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {riskScore.recommendations.map((rec, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-3 p-3 rounded-lg bg-surface-hover dark:bg-surface-hover-dark"
              >
                <CheckCircle2 className="h-5 w-5 text-success-main flex-shrink-0 mt-0.5" />
                <p className="text-text">{rec}</p>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button variant="outline" fullWidth leftIcon={<MapPin className="h-4 w-4" />}>
          Check Location Risk
        </Button>
        <Button variant="outline" fullWidth leftIcon={<Heart className="h-4 w-4" />}>
          Report Symptoms
        </Button>
        <Button variant="outline" fullWidth leftIcon={<Activity className="h-4 w-4" />}>
          View Exposure History
        </Button>
      </div>
    </div>
  );
};

export default RiskDashboard;

