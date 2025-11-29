import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    ClockIcon,
    ArrowLeftIcon,
    HeartIcon,
    BeakerIcon,
    ExclamationCircleIcon
} from '@heroicons/react/24/outline';

interface TimelineEvent {
    id: string;
    date: string;
    type: 'symptom' | 'report' | 'prediction' | 'medication';
    title: string;
    description: string;
    severity?: 'low' | 'medium' | 'high';
}

export default function HealthTimeline() {
    const navigate = useNavigate();
    const [events, setEvents] = useState<TimelineEvent[]>([
        {
            id: '1',
            date: '2025-11-28',
            type: 'report',
            title: 'Blood Test Analyzed',
            description: 'Platelet count: 45,000 - CRITICAL',
            severity: 'high'
        },
        {
            id: '2',
            date: '2025-11-27',
            type: 'symptom',
            title: 'Symptoms Logged',
            description: 'Fever (102°F), Headache, Body Ache',
            severity: 'medium'
        },
        {
            id: '3',
            date: '2025-11-26',
            type: 'prediction',
            title: 'AI Risk Assessment',
            description: 'Dengue risk increased to 92%',
            severity: 'high'
        }
    ]);

    const getIcon = (type: string) => {
        switch (type) {
            case 'symptom': return <HeartIcon className="h-5 w-5" />;
            case 'report': return <BeakerIcon className="h-5 w-5" />;
            case 'prediction': return <ExclamationCircleIcon className="h-5 w-5" />;
            default: return <ClockIcon className="h-5 w-5" />;
        }
    };

    const getSeverityColor = (severity?: string) => {
        switch (severity) {
            case 'high': return 'border-red-500 bg-red-50';
            case 'medium': return 'border-yellow-500 bg-yellow-50';
            case 'low': return 'border-green-500 bg-green-50';
            default: return 'border-slate-300 bg-white';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center text-slate-600 hover:text-teal-600 mb-6 transition-colors"
                >
                    <ArrowLeftIcon className="h-5 w-5 mr-2" />
                    Back to Dashboard
                </button>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-panel rounded-2xl p-8"
                >
                    <div className="flex items-center gap-3 mb-8">
                        <ClockIcon className="h-8 w-8 text-teal-600" />
                        <div>
                            <h1 className="text-2xl font-bold text-slate-900">Health Timeline</h1>
                            <p className="text-slate-500">Your complete health journey</p>
                        </div>
                    </div>

                    <div className="relative">
                        {/* Timeline Line */}
                        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-teal-500 to-slate-300"></div>

                        {/* Events */}
                        <div className="space-y-6">
                            {events.map((event, index) => (
                                <motion.div
                                    key={event.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    className="relative flex gap-6"
                                >
                                    {/* Timeline Dot */}
                                    <div className="flex-shrink-0 w-16 flex justify-center">
                                        <div className="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center text-white shadow-lg">
                                            {getIcon(event.type)}
                                        </div>
                                    </div>

                                    {/* Event Card */}
                                    <div className={`flex-1 p-4 rounded-xl border-2 ${getSeverityColor(event.severity)} shadow-sm`}>
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="font-semibold text-slate-900">{event.title}</h3>
                                            <span className="text-xs text-slate-500">{event.date}</span>
                                        </div>
                                        <p className="text-sm text-slate-600">{event.description}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
