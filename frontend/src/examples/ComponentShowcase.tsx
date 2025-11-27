/**
 * Component Showcase - EpiSPY Design System
 * 
 * Demonstrates all core components with various states and variants.
 * Perfect for testing and demonstrating the design system.
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertContainer } from '@/components/ui/Alert';
import { Modal, ModalHeader, ModalTitle, ModalDescription, ModalContent, ModalFooter } from '@/components/ui/Modal';
import { AlertCircle, CheckCircle2, TrendingUp, Activity } from 'lucide-react';

export const ComponentShowcase: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [alertVisible, setAlertVisible] = useState(true);

  return (
    <div className="min-h-screen bg-background p-8 dark:bg-background-dark">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 gradient-text">
            EpiSPY Design System
          </h1>
          <p className="text-xl text-text-secondary">
            Healthcare-optimized UI components for epidemic surveillance
          </p>
        </div>

        {/* Buttons Section */}
        <Card variant="elevated" padding="lg">
          <CardHeader>
            <CardTitle>Buttons</CardTitle>
            <CardDescription>Various button variants and states</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="danger">Danger</Button>
              <Button variant="success">Success</Button>
              <Button variant="warning">Warning</Button>
              <Button size="sm">Small</Button>
              <Button size="lg">Large</Button>
              <Button loading>Loading</Button>
              <Button disabled>Disabled</Button>
              <Button leftIcon={<CheckCircle2 className="h-4 w-4" />}>
                With Icon
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Badges Section */}
        <Card variant="elevated" padding="lg">
          <CardHeader>
            <CardTitle>Badges</CardTitle>
            <CardDescription>Risk levels and status indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <Badge variant="minimal">Minimal Risk</Badge>
              <Badge variant="low">Low Risk</Badge>
              <Badge variant="moderate">Moderate</Badge>
              <Badge variant="high">High Risk</Badge>
              <Badge variant="critical" pulse>Critical</Badge>
              <Badge variant="healthy">Healthy</Badge>
              <Badge variant="infected">Infected</Badge>
              <Badge variant="recovered">Recovered</Badge>
              <Badge variant="vaccinated">Vaccinated</Badge>
              <Badge variant="success">Success</Badge>
              <Badge variant="warning">Warning</Badge>
              <Badge variant="error">Error</Badge>
              <Badge variant="info">Info</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Cards Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card variant="default" hover>
            <CardHeader>
              <CardTitle>Default Card</CardTitle>
              <CardDescription>Standard card with hover effect</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-secondary">
                This card has a subtle shadow and lifts on hover.
              </p>
            </CardContent>
          </Card>

          <Card variant="elevated" hover>
            <CardHeader>
              <CardTitle>Elevated Card</CardTitle>
              <CardDescription>More prominent shadow</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-secondary">
                This card has a stronger shadow for emphasis.
              </p>
            </CardContent>
          </Card>

          <Card variant="glass" hover glow>
            <CardHeader>
              <CardTitle>Glass Card</CardTitle>
              <CardDescription>Glassmorphism effect</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-secondary">
                Modern glassmorphism with backdrop blur.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Alerts Section */}
        <Card variant="elevated" padding="lg">
          <CardHeader>
            <CardTitle>Alerts</CardTitle>
            <CardDescription>System notifications and warnings</CardDescription>
          </CardHeader>
          <CardContent>
            <AlertContainer>
              {alertVisible && (
                <Alert
                  variant="warning"
                  title="Outbreak Detected"
                  dismissible
                  onDismiss={() => setAlertVisible(false)}
                >
                  New cases reported in Mumbai. Immediate action required.
                </Alert>
              )}
              <Alert variant="error" title="Critical Alert">
                Healthcare system capacity at 95%. Resource allocation needed.
              </Alert>
              <Alert variant="success" title="System Update">
                All monitoring agents are operational.
              </Alert>
              <Alert variant="info" title="Information">
                Weekly report generated successfully.
              </Alert>
            </AlertContainer>
          </CardContent>
        </Card>

        {/* Modal Trigger */}
        <Card variant="elevated" padding="lg">
          <CardHeader>
            <CardTitle>Modal</CardTitle>
            <CardDescription>Dialog modals with smooth animations</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => setModalOpen(true)}>
              Open Modal
            </Button>
          </CardContent>
        </Card>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card variant="elevated" hover glow glowColor="primary">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-secondary">Active Cases</p>
                  <p className="text-3xl font-bold text-text">1,234</p>
                  <div className="flex items-center gap-1 mt-2">
                    <TrendingUp className="h-4 w-4 text-success-main" />
                    <span className="text-sm text-success-main">+12.5%</span>
                  </div>
                </div>
                <Activity className="h-12 w-12 text-primary-500 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card variant="elevated" hover glow glowColor="success">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-secondary">Recovered</p>
                  <p className="text-3xl font-bold text-text">8,901</p>
                  <div className="flex items-center gap-1 mt-2">
                    <TrendingUp className="h-4 w-4 text-success-main" />
                    <span className="text-sm text-success-main">+5.2%</span>
                  </div>
                </div>
                <CheckCircle2 className="h-12 w-12 text-success-main opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card variant="elevated" hover glow glowColor="warning">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-secondary">At Risk</p>
                  <p className="text-3xl font-bold text-text">456</p>
                  <div className="flex items-center gap-1 mt-2">
                    <AlertCircle className="h-4 w-4 text-warning-main" />
                    <span className="text-sm text-warning-main">Monitor</span>
                  </div>
                </div>
                <AlertCircle className="h-12 w-12 text-warning-main opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card variant="elevated" hover glow glowColor="error">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-secondary">Critical</p>
                  <p className="text-3xl font-bold text-text">23</p>
                  <div className="flex items-center gap-1 mt-2">
                    <AlertCircle className="h-4 w-4 text-error-main" />
                    <span className="text-sm text-error-main">Urgent</span>
                  </div>
                </div>
                <AlertCircle className="h-12 w-12 text-error-main opacity-20" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Modal */}
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Confirm Action"
          description="This is a sample modal with smooth animations"
          size="md"
        >
          <ModalContent>
            <p className="text-text-secondary">
              This modal demonstrates the glassmorphism effect and smooth
              slide-up animation. It's fully accessible with keyboard navigation.
            </p>
          </ModalContent>
          <ModalFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => setModalOpen(false)}>
              Confirm
            </Button>
          </ModalFooter>
        </Modal>
      </div>
    </div>
  );
};

export default ComponentShowcase;

