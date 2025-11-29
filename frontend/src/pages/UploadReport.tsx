import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    CloudArrowUpIcon,
    DocumentTextIcon,
    ArrowLeftIcon,
    CheckCircleIcon
} from '@heroicons/react/24/outline';
import api from '../api/axios';

export default function UploadReport() {
    const navigate = useNavigate();
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('report_type', 'blood_test');

        try {
            const response = await api.post('/reports/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(response.data);
        } catch (error) {
            console.error('Upload failed', error);
        } finally {
            setLoading(false);
        }
    };

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
                            <DocumentTextIcon className="h-8 w-8 text-teal-600" />
                        </div>
                        <h1 className="text-2xl font-bold text-slate-900">Upload Medical Report</h1>
                        <p className="text-slate-500 mt-2">AI-powered analysis for instant health insights</p>
                    </div>

                    {!result ? (
                        <form onSubmit={handleSubmit} className="space-y-8">
                            <div className="flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-xl hover:border-teal-500 hover:bg-teal-50/30 transition-all duration-300">
                                <div className="space-y-1 text-center">
                                    <CloudArrowUpIcon className="mx-auto h-12 w-12 text-slate-400" />
                                    <div className="flex text-sm text-slate-600">
                                        <label className="relative cursor-pointer rounded-md font-medium text-teal-600 hover:text-teal-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-teal-500">
                                            <span>Upload a file</span>
                                            <input
                                                type="file"
                                                className="sr-only"
                                                onChange={handleFileChange}
                                                accept=".pdf,.jpg,.jpeg,.png"
                                            />
                                        </label>
                                        <p className="pl-1">or drag and drop</p>
                                    </div>
                                    <p className="text-xs text-slate-500">
                                        PDF, PNG, JPG up to 10MB
                                    </p>
                                    {file && (
                                        <div className="mt-4 p-2 bg-teal-50 text-teal-700 rounded-lg text-sm font-medium">
                                            Selected: {file.name}
                                        </div>
                                    )}
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={!file || loading}
                                className={`w-full btn-primary flex justify-center items-center ${(!file || loading) ? 'opacity-50 cursor-not-allowed' : ''
                                    }`}
                            >
                                {loading ? (
                                    <>
                                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Analyzing Report...
                                    </>
                                ) : (
                                    'Analyze Report'
                                )}
                            </button>
                        </form>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="space-y-6"
                        >
                            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 flex items-center gap-3">
                                <CheckCircleIcon className="h-6 w-6 text-emerald-600" />
                                <div>
                                    <h3 className="font-semibold text-emerald-900">Analysis Complete</h3>
                                    <p className="text-sm text-emerald-700">Report processed successfully</p>
                                </div>
                            </div>

                            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
                                <h3 className="font-semibold text-slate-900 mb-4">Extracted Data</h3>
                                <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                                    {Object.entries(result.extracted_data || {}).map(([key, value]: [string, any]) => (
                                        <div key={key} className="sm:col-span-1">
                                            <dt className="text-sm font-medium text-slate-500 capitalize">{key.replace(/_/g, ' ')}</dt>
                                            <dd className="mt-1 text-sm text-slate-900 font-semibold">{value}</dd>
                                        </div>
                                    ))}
                                </dl>
                            </div>

                            <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
                                <h3 className="font-semibold text-slate-900 mb-4">AI Assessment</h3>
                                <p className="text-slate-600 leading-relaxed">
                                    {result.risk_assessment?.summary || "No specific risks identified based on the provided data."}
                                </p>
                            </div>

                            <button
                                onClick={() => {
                                    setFile(null);
                                    setResult(null);
                                }}
                                className="w-full btn-secondary"
                            >
                                Upload Another Report
                            </button>
                        </motion.div>
                    )}
                </motion.div>
            </div>
        </div>
    );
}
