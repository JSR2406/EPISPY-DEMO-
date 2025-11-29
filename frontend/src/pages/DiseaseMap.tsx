import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    MapPinIcon,
    ArrowLeftIcon,
    ExclamationTriangleIcon,
    ShieldCheckIcon
} from '@heroicons/react/24/outline';

interface Hotspot {
    id: string;
    location: string;
    disease: string;
    cases: number;
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
    distance: string;
}

export default function DiseaseMap() {
    const navigate = useNavigate();
    const [hotspots, setHotspots] = useState<Hotspot[]>([
        {
            id: '1',
            location: 'Andheri West',
            disease: 'Dengue',
            cases: 45,
            riskLevel: 'critical',
            distance: '2.3 km'
        },
        {
            id: '2',
            location: 'Bandra East',
            disease: 'Malaria',
            cases: 12,
            riskLevel: 'high',
            distance: '5.1 km'
        },
        {
            id: '3',
            location: 'Powai',
            disease: 'Influenza',
            cases: 8,
            riskLevel: 'medium',
            distance: '7.8 km'
        }
    ]);

    const getRiskColor = (level: string) => {
        switch (level) {
            case 'critical': return 'bg-red-500';
            case 'high': return 'bg-orange-500';
            case 'medium': return 'bg-yellow-500';
            case 'low': return 'bg-green-500';
            default: return 'bg-slate-500';
        }
    };

    const getRiskBorder = (level: string) => {
        switch (level) {
            case 'critical': return 'border-red-500';
            case 'high': return 'border-orange-500';
            case 'medium': return 'border-yellow-500';
            case 'low': return 'border-green-500';
            default: return 'border-slate-500';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-6xl mx-auto">
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
                >
                    <div className="glass-panel rounded-2xl p-8 mb-6">
                        <div className="flex items-center gap-3 mb-6">
                            <MapPinIcon className="h-8 w-8 text-teal-600" />
                            <div>
                                <h1 className="text-2xl font-bold text-slate-900">Disease Hotspot Map</h1>
                                <p className="text-slate-500">Real-time outbreak tracking near you</p>
                            </div>
                        </div>

                        {/* Map Placeholder */}
                        <div className="relative h-96 bg-slate-100 rounded-xl overflow-hidden mb-6">
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="text-center">
                                    <MapPinIcon className="h-16 w-16 text-slate-300 mx-auto mb-4" />
                                    <p className="text-slate-400">Interactive map showing disease hotspots</p>
                                    <p className="text-xs text-slate-300 mt-2">Your location: Mumbai, Maharashtra</p>
                                </div>
                            </div>

                            {/* Simulated hotspot markers */}
                            <div className="absolute top-1/4 left-1/3 w-4 h-4 bg-red-500 rounded-full animate-ping"></div>
                            <div className="absolute top-1/2 right-1/3 w-4 h-4 bg-orange-500 rounded-full animate-ping" style={{ animationDelay: '0.5s' }}></div>
                            <div className="absolute bottom-1/3 left-1/2 w-4 h-4 bg-yellow-500 rounded-full animate-ping" style={{ animationDelay: '1s' }}></div>
                        </div>

                        {/* Legend */}
                        <div className="flex flex-wrap gap-4 justify-center">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                                <span className="text-sm text-slate-600">Critical</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                                <span className="text-sm text-slate-600">High</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                                <span className="text-sm text-slate-600">Medium</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                <span className="text-sm text-slate-600">Low</span>
                            </div>
                        </div>
                    </div>

                    {/* Hotspot List */}
                    <div className="glass-panel rounded-2xl p-8">
                        <h2 className="text-xl font-bold text-slate-900 mb-6">Nearby Outbreaks</h2>
                        <div className="space-y-4">
                            {hotspots.map((hotspot, index) => (
                                <motion.div
                                    key={hotspot.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    className={`p-4 rounded-xl border-2 ${getRiskBorder(hotspot.riskLevel)} bg-white shadow-sm hover:shadow-md transition-shadow`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <div className={`w-3 h-3 rounded-full ${getRiskColor(hotspot.riskLevel)}`}></div>
                                                <h3 className="font-semibold text-slate-900">{hotspot.location}</h3>
                                                <span className="text-xs px-2 py-1 bg-slate-100 text-slate-600 rounded-full">
                                                    {hotspot.distance} away
                                                </span>
                                            </div>
                                            <p className="text-sm text-slate-600 mb-2">
                                                <span className="font-medium">{hotspot.disease}</span> - {hotspot.cases} confirmed cases
                                            </p>
                                            <div className="flex items-center gap-2 text-xs text-slate-500">
                                                {hotspot.riskLevel === 'critical' || hotspot.riskLevel === 'high' ? (
                                                    <>
                                                        <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
                                                        <span>Avoid this area if possible</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <ShieldCheckIcon className="h-4 w-4 text-green-500" />
                                                        <span>Take standard precautions</span>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                        <button className="btn-secondary text-xs px-3 py-2">
                                            View Details
                                        </button>
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
