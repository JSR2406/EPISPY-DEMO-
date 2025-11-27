/**
 * Request Board Component
 * 
 * Kanban-style board showing resource requests by status.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { AlertCircle, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';

interface ResourceRequest {
  id: string;
  resource_type: string;
  quantity_needed: number;
  quantity_fulfilled: number;
  urgency: string;
  status: string;
  deadline?: string;
  created_at: string;
}

export const RequestBoard: React.FC = () => {
  const [requests, setRequests] = useState<ResourceRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch requests from API
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      // Placeholder - would fetch from API
      setRequests([]);
    } catch (error) {
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyBadge = (urgency: string) => {
    switch (urgency) {
      case 'EMERGENCY': return <Badge variant="critical" pulse>Emergency</Badge>;
      case 'CRITICAL': return <Badge variant="critical">Critical</Badge>;
      case 'URGENT': return <Badge variant="high">Urgent</Badge>;
      default: return <Badge variant="moderate">Routine</Badge>;
    }
  };

  const columns = [
    { id: 'OPEN', title: 'Open Requests', icon: Clock, color: 'warning' },
    { id: 'MATCHED', title: 'Matched', icon: CheckCircle2, color: 'info' },
    { id: 'FULFILLED', title: 'Fulfilled', icon: CheckCircle2, color: 'success' },
    { id: 'CANCELLED', title: 'Cancelled', icon: XCircle, color: 'error' },
  ];

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
        <CardTitle>Request Board</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {columns.map((column) => {
            const columnRequests = requests.filter(r => r.status === column.id);
            const Icon = column.icon;

            return (
              <div key={column.id} className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-surface-hover dark:bg-surface-hover-dark rounded-lg">
                  <div className="flex items-center gap-2">
                    <Icon className={`h-5 w-5 text-${column.color}-main`} />
                    <h3 className="font-semibold text-text">{column.title}</h3>
                  </div>
                  <Badge variant="default">{columnRequests.length}</Badge>
                </div>

                <div className="space-y-2 min-h-[200px]">
                  {columnRequests.map((request) => (
                    <motion.div
                      key={request.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-3 bg-surface dark:bg-surface-dark rounded-lg border border-border dark:border-border-dark hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="font-medium text-text">{request.resource_type}</span>
                        {getUrgencyBadge(request.urgency)}
                      </div>
                      <div className="text-sm text-text-secondary space-y-1">
                        <p>Needed: {request.quantity_needed}</p>
                        <p>Fulfilled: {request.quantity_fulfilled}</p>
                        {request.deadline && (
                          <p className="text-warning-main">
                            Deadline: {new Date(request.deadline).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      <Button variant="ghost" size="sm" className="w-full mt-2">
                        View Details
                      </Button>
                    </motion.div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default RequestBoard;

