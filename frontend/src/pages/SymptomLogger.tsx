import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SymptomLogger() {
    const navigate = useNavigate();
    const [symptoms, setSymptoms] = useState<string[]>([]);
    const [severity, setSeverity] = useState(3);
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);

    const availableSymptoms = [
        "Fever", "Cough", "Headache", "Fatigue",
        "Body Ache", "Rash", "Nausea", "Chills",
        "Sore Throat", "Difficulty Breathing"
    ];

    const toggleSymptom = (symptom: string) => {
        if (symptoms.includes(symptom)) {
            setSymptoms(symptoms.filter(s => s !== symptom));
        } else {
            setSymptoms([...symptoms, symptom]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        // Mock API call since backend endpoint might not be fully wired yet
        setTimeout(() => {
            alert("Symptoms logged! AI Analysis: Monitor temperature closely.");
            setLoading(false);
            navigate('/dashboard');
        }, 1000);
    };

    return (
        <div className="min-h-screen bg-gray-100 p-6">
            <div className="max-w-2xl mx-auto">
                <button
                    onClick={() => navigate('/dashboard')}
                    className="mb-4 text-teal-600 hover:text-teal-800 font-medium"
                >
                    &larr; Back to Dashboard
                </button>

                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">Log Daily Symptoms</h2>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-3">Select Symptoms</label>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                {availableSymptoms.map(symptom => (
                                    <button
                                        key={symptom}
                                        type="button"
                                        onClick={() => toggleSymptom(symptom)}
                                        className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${symptoms.includes(symptom)
                                                ? 'bg-teal-100 border-teal-500 text-teal-800'
                                                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                                            }`}
                                    >
                                        {symptom}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Overall Severity (1-10)
                            </label>
                            <div className="flex items-center gap-4">
                                <input
                                    type="range"
                                    min="1"
                                    max="10"
                                    value={severity}
                                    onChange={(e) => setSeverity(parseInt(e.target.value))}
                                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                />
                                <span className="text-lg font-bold text-teal-600 w-8">{severity}</span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">1 = Mild, 10 = Severe/Emergency</p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Additional Notes</label>
                            <textarea
                                rows={3}
                                className="shadow-sm focus:ring-teal-500 focus:border-teal-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                placeholder="Describe how you feel..."
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading || symptoms.length === 0}
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50"
                        >
                            {loading ? 'Analyzing...' : 'Log Symptoms'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
