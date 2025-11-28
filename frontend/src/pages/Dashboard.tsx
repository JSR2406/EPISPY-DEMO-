import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
    const { user, logout } = useAuth();
    const [weather, setWeather] = useState<any>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchWeather = async () => {
            try {
                // Hardcoded city for demo
                const response = await api.get('/weather/Mumbai');
                setWeather(response.data);
            } catch (error) {
                console.error("Failed to fetch weather", error);
            }
        };
        fetchWeather();
    }, []);

    return (
        <div className="min-h-screen bg-gray-100">
            <nav className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <h1 className="text-xl font-bold text-teal-600">EpiSPY Patient Portal</h1>
                        </div>
                        <div className="flex items-center space-x-4">
                            <span className="text-gray-700">Welcome, {user?.full_name}</span>
                            <button
                                onClick={logout}
                                className="text-sm text-red-600 hover:text-red-800"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Weather Card */}
                        <div className="bg-white overflow-hidden shadow rounded-lg p-6">
                            <h3 className="text-lg font-medium text-gray-900">Local Weather</h3>
                            {weather ? (
                                <div className="mt-4">
                                    <div className="text-3xl font-bold">{weather.temperature_celsius}°C</div>
                                    <div className="text-gray-500 capitalize">{weather.condition}</div>
                                    <div className="mt-4 space-y-2">
                                        {Object.entries(weather.disease_multipliers || {}).map(([disease, risk]: [string, any]) => (
                                            <div key={disease} className="flex justify-between text-sm">
                                                <span className="capitalize">{disease} Risk</span>
                                                <span className={`font-bold ${risk > 1.5 ? 'text-red-600' : 'text-green-600'}`}>
                                                    {risk}x
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="mt-4 text-gray-400">Loading weather data...</div>
                            )}
                        </div>

                        {/* Risk Assessment Card */}
                        <div className="bg-white overflow-hidden shadow rounded-lg p-6">
                            <h3 className="text-lg font-medium text-gray-900">Your Health Risks</h3>
                            <div className="mt-4 space-y-4">
                                <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                                    <div className="flex justify-between">
                                        <span className="font-medium text-red-800">Dengue Fever</span>
                                        <span className="font-bold text-red-800">HIGH</span>
                                    </div>
                                    <p className="text-sm text-red-600 mt-1">Due to high humidity and local cases.</p>
                                </div>
                                <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                                    <div className="flex justify-between">
                                        <span className="font-medium text-green-800">Influenza</span>
                                        <span className="font-bold text-green-800">LOW</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Quick Actions */}
                        <div className="bg-white overflow-hidden shadow rounded-lg p-6">
                            <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
                            <div className="mt-4 space-y-3">
                                <button
                                    onClick={() => navigate('/upload-report')}
                                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700"
                                >
                                    Upload Report
                                </button>
                                <button
                                    onClick={() => navigate('/log-symptoms')}
                                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                                >
                                    Log Symptoms
                                </button>
                                <button className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700">
                                    Emergency SOS
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
