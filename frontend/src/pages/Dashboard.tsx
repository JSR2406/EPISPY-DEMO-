import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    CloudIcon,
    ExclamationTriangleIcon,
    DocumentArrowUpIcon,
    ClipboardDocumentCheckIcon,
    PhoneIcon,
    ArrowRightOnRectangleIcon,
    UserCircleIcon,
    SunIcon
} from '@heroicons/react/24/outline';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
    const { user, logout } = useAuth();
    const [weather, setWeather] = useState<any>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchWeather = async () => {
            try {
                const response = await api.get('/weather/Mumbai');
                setWeather(response.data);
            } catch (error) {
                console.error("Failed to fetch weather", error);
            }
        };
        fetchWeather();
    }, []);

    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    const item = {
        hidden: { y: 20, opacity: 0 },
        show: { y: 0, opacity: 1 }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50">
            {/* Navbar */}
            <nav className="glass-panel sticky top-0 z-50 border-b border-slate-200/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center gap-2">
                            <div className="bg-teal-600 p-2 rounded-lg">
                                <ExclamationTriangleIcon className="h-6 w-6 text-white" />
                            </div>
                            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-teal-600 to-emerald-600">
                                EpiSPY
                            </span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/50 border border-slate-200">
                                <UserCircleIcon className="h-5 w-5 text-slate-500" />
                                <span className="text-sm font-medium text-slate-700">
                                    {user?.full_name || 'Guest User'}
                                </span>
                            </div>
                            <button
                                onClick={logout}
                                className="p-2 rounded-full hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors"
                                title="Logout"
                            >
                                <ArrowRightOnRectangleIcon className="h-6 w-6" />
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                <motion.div
                    variants={container}
                    initial="hidden"
                    animate="show"
                    className="space-y-8"
                >
                    {/* Welcome Section */}
                    <motion.div variants={item} className="text-center sm:text-left">
                        <h1 className="text-3xl font-bold text-slate-900">
                            Health Dashboard
                        </h1>
                        <p className="mt-2 text-slate-600">
                            Real-time epidemic surveillance and personal health monitoring.
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Weather Card */}
                        <motion.div variants={item} className="glass-panel rounded-2xl p-6 card-hover relative overflow-hidden group">
                            <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-teal-100 rounded-full blur-2xl opacity-50 group-hover:opacity-75 transition-opacity"></div>

                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                                    <CloudIcon className="h-5 w-5 text-teal-500" />
                                    Environmental Risk
                                </h3>
                                <span className="text-xs font-medium px-2 py-1 bg-teal-50 text-teal-700 rounded-full border border-teal-100">
                                    Live Updates
                                </span>
                            </div>

                            {weather ? (
                                <div className="space-y-6">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-blue-50 rounded-xl">
                                            <SunIcon className="h-8 w-8 text-blue-500" />
                                        </div>
                                        <div>
                                            <div className="text-3xl font-bold text-slate-900">{weather.temperature_celsius}°C</div>
                                            <div className="text-sm text-slate-500 capitalize">{weather.condition}</div>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        {Object.entries(weather.disease_multipliers || {}).map(([disease, risk]: [string, any]) => (
                                            <div key={disease} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                                                <span className="capitalize text-sm font-medium text-slate-700">{disease}</span>
                                                <div className="flex items-center gap-2">
                                                    <div className={`h-2 w-16 rounded-full overflow-hidden bg-slate-200`}>
                                                        <div
                                                            className={`h-full ${risk > 1.5 ? 'bg-red-500' : 'bg-emerald-500'}`}
                                                            style={{ width: `${Math.min((risk / 3) * 100, 100)}%` }}
                                                        />
                                                    </div>
                                                    <span className={`text-sm font-bold ${risk > 1.5 ? 'text-red-600' : 'text-emerald-600'}`}>
                                                        {risk}x
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="animate-pulse space-y-4">
                                    <div className="h-12 bg-slate-100 rounded-lg w-1/2"></div>
                                    <div className="space-y-2">
                                        <div className="h-8 bg-slate-100 rounded-lg"></div>
                                        <div className="h-8 bg-slate-100 rounded-lg"></div>
                                    </div>
                                </div>
                            )}
                        </motion.div>

                        {/* Risk Assessment Card */}
                        <motion.div variants={item} className="glass-panel rounded-2xl p-6 card-hover relative overflow-hidden">
                            <div className="absolute top-0 left-0 -mt-4 -ml-4 w-24 h-24 bg-red-100 rounded-full blur-2xl opacity-50"></div>

                            <h3 className="text-lg font-semibold text-slate-800 mb-6 flex items-center gap-2">
                                <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
                                Personal Alerts
                            </h3>

                            <div className="space-y-4">
                                <div className="p-4 bg-gradient-to-r from-red-50 to-white border border-red-100 rounded-xl">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h4 className="font-semibold text-red-900">Dengue Fever Alert</h4>
                                            <p className="text-sm text-red-700 mt-1">High mosquito activity detected in your area.</p>
                                        </div>
                                        <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-bold rounded">HIGH</span>
                                    </div>
                                </div>

                                <div className="p-4 bg-gradient-to-r from-emerald-50 to-white border border-emerald-100 rounded-xl">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h4 className="font-semibold text-emerald-900">Influenza Status</h4>
                                            <p className="text-sm text-emerald-700 mt-1">Risk levels are currently low.</p>
                                        </div>
                                        <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded">LOW</span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Quick Actions */}
                        <motion.div variants={item} className="glass-panel rounded-2xl p-6 card-hover">
                            <h3 className="text-lg font-semibold text-slate-800 mb-6">Quick Actions</h3>
                            <div className="space-y-4">
                                <button
                                    onClick={() => navigate('/upload-report')}
                                    className="w-full group relative flex items-center p-4 rounded-xl border border-slate-200 bg-white hover:border-teal-500 hover:shadow-md transition-all duration-300"
                                >
                                    <div className="p-3 rounded-lg bg-teal-50 text-teal-600 group-hover:bg-teal-600 group-hover:text-white transition-colors">
                                        <DocumentArrowUpIcon className="h-6 w-6" />
                                    </div>
                                    <div className="ml-4 text-left">
                                        <h4 className="font-semibold text-slate-900">Analyze Report</h4>
                                        <p className="text-sm text-slate-500">Upload medical documents for AI analysis</p>
                                    </div>
                                </button>

                                <button
                                    onClick={() => navigate('/log-symptoms')}
                                    className="w-full group relative flex items-center p-4 rounded-xl border border-slate-200 bg-white hover:border-blue-500 hover:shadow-md transition-all duration-300"
                                >
                                    <div className="p-3 rounded-lg bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                        <ClipboardDocumentCheckIcon className="h-6 w-6" />
                                    </div>
                                    <div className="ml-4 text-left">
                                        <h4 className="font-semibold text-slate-900">Log Symptoms</h4>
                                        <p className="text-sm text-slate-500">Track daily health indicators</p>
                                    </div>
                                </button>

                                <button className="w-full group relative flex items-center p-4 rounded-xl border border-red-100 bg-red-50/50 hover:bg-red-50 hover:border-red-200 transition-all duration-300">
                                    <div className="p-3 rounded-lg bg-red-100 text-red-600 group-hover:bg-red-600 group-hover:text-white transition-colors">
                                        <PhoneIcon className="h-6 w-6" />
                                    </div>
                                    <div className="ml-4 text-left">
                                        <h4 className="font-semibold text-red-900">Emergency SOS</h4>
                                        <p className="text-sm text-red-600">Contact nearest emergency services</p>
                                    </div>
                                </button>
                            </div>
                        </motion.div>
                    </div>
                </motion.div>
            </main>
        </div>
    );
}
