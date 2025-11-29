import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    ClipboardDocumentCheckIcon,
    ArrowLeftIcon,
    CheckCircleIcon
} from '@heroicons/react/24/outline';
import api from '../api/axios';

const SYMPTOMS_LIST = [
    'Fever', 'Cough', 'Headache', 'Fatigue', 'Body Ache',
    'Nausea', 'Diarrhea', 'Rash', 'Sore Throat', 'Shortness of Breath'
];

export default function SymptomLogger() {
    const navigate = useNavigate();
    const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
    const [severity, setSeverity] = useState(1);
    const [notes, setNotes] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const toggleSymptom = (symptom: string) => {
        if (selectedSymptoms.includes(symptom)) {
            setSelectedSymptoms(selectedSymptoms.filter(s => s !== symptom));
        } else {
            setSelectedSymptoms([...selectedSymptoms, symptom]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // Mock API call for now
            console.log({ selectedSymptoms, severity, notes });
            // await api.post('/symptoms/log', { ... });
            setSubmitted(true);
            setTimeout(() => {
                navigate('/dashboard');
            }, 2000);
        } catch (error) {
            console.error('Failed to log symptoms', error);
        }
    };

    if (submitted) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-teal-50">
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="glass-panel p-8 rounded-2xl text-center max-w-md mx-4"
                >
                    <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-emerald-100 mb-6">
                        <CheckCircleIcon className="h-10 w-10 text-emerald-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">Symptoms Logged</h2>
                    <p className="text-slate-600">Thank you for updating your health status. Redirecting to dashboard...</p>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto">
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
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center p-3 bg-teal-50 rounded-xl mb-4">
                            <ClipboardDocumentCheckIcon className="h-8 w-8 text-teal-600" />
                        </div>
                        <h1 className="text-2xl font-bold text-slate-900">Log Daily Symptoms</h1>
                        <p className="text-slate-500 mt-2">Help us track and predict health trends in your area</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-8">
                        {/* Symptoms Grid */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-4">Select Symptoms</label>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                {SYMPTOMS_LIST.map((symptom) => (
                                    <button
                                        key={symptom}
                                        type="button"
                                        onClick={() => toggleSymptom(symptom)}
                                        className={`p-3 rounded-xl text-sm font-medium transition-all duration-200 border ${selectedSymptoms.includes(symptom)
                                                ? 'bg-teal-600 text-white border-teal-600 shadow-md transform scale-[1.02]'
                                                : 'bg-white text-slate-600 border-slate-200 hover:border-teal-300 hover:bg-teal-50'
                                            }`}
                                    >
                                        {symptom}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Severity Slider */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-4">
                                Overall Severity (1-10)
                                <span className="float-right font-bold text-teal-600">{severity}</span>
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="10"
                                value={severity}
                                onChange={(e) => setSeverity(parseInt(e.target.value))}
                                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-teal-600"
                            />
                            <div className="flex justify-between text-xs text-slate-400 mt-2">
                                <span>Mild</span>
                                <span>Moderate</span>
                                <span>Severe</span>
                            </div>
                        </div>

                        {/* Notes */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Additional Notes</label>
                            <textarea
                                rows={4}
                                className="input-field resize-none"
                                placeholder="Describe any other symptoms or details..."
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={selectedSymptoms.length === 0}
                            className={`w-full btn-primary ${selectedSymptoms.length === 0 ? 'opacity-50 cursor-not-allowed' : ''
                                }`}
                        >
                            Submit Log
                        </button>
                    </form>
                </motion.div>
            </div>
        </div>
    );
}
