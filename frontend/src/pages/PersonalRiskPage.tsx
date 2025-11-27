/**
 * Personal Risk Page
 * 
 * Main page for personalized risk assessment.
 */

import React, { useState, useEffect } from 'react';
import { RiskDashboard } from '@/components/personalized/RiskDashboard';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { MapPin, Clock, AlertTriangle } from 'lucide-react';

export const PersonalRiskPage: React.FC = () => {
  const [userId, setUserId] = useState<string>('');
  const [currentLocation, setCurrentLocation] = useState<{ latitude: number; longitude: number } | undefined>();

  useEffect(() => {
    // Get user ID from auth context or localStorage
    const storedUserId = localStorage.getItem('userId');
    if (storedUserId) {
      setUserId(storedUserId);
    }

    // Get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        (error) => {
          console.error('Error getting location:', error);
        }
      );
    }
  }, []);

  if (!userId) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card variant="elevated" padding="lg">
          <CardContent className="text-center py-12">
            <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-warning-main" />
            <h2 className="text-2xl font-bold mb-2">Profile Required</h2>
            <p className="text-text-secondary mb-4">
              Please create a profile to view your personalized risk assessment.
            </p>
            <button className="btn btn-primary">Create Profile</button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <RiskDashboard userId={userId} currentLocation={currentLocation} />
    </div>
  );
};

export default PersonalRiskPage;

