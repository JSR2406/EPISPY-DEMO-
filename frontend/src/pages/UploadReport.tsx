import React, { useState } from 'react';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';

export default function UploadReport() {
    const [file, setFile] = useState<File | null>(null);
    const [reportType, setReportType] = useState('blood_test');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setLoading(true);
        setError('');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await api.post('/reports/upload', formData, {
                params: { report_type: reportType },
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(response.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Upload failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-6">
            <div className="max-w-3xl mx-auto">
                <button
                    onClick={() => navigate('/dashboard')}
                    className="mb-4 text-teal-600 hover:text-teal-800 font-medium"
                >
                    &larr; Back to Dashboard
                </button>

                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload Medical Report</h2>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Report Type</label>
                            <select
                                value={reportType}
                                onChange={(e) => setReportType(e.target.value)}
                                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm rounded-md"
                            >
                                <option value="blood_test">Blood Test</option>
                                <option value="urine_test">Urine Test</option>
                                <option value="xray">X-Ray</option>
                                <option value="prescription">Prescription</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700">File Upload</label>
                            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                                <div className="space-y-1 text-center">
                                    <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    <div className="flex text-sm text-gray-600">
                                        <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-teal-600 hover:text-teal-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-teal-500">
                                            <span>Upload a file</span>
                                            <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".pdf,.jpg,.jpeg,.png" />
                                        </label>
                                        <p className="pl-1">or drag and drop</p>
                                    </div>
                                    <p className="text-xs text-gray-500">PDF, PNG, JPG up to 10MB</p>
                                </div>
                            </div>
                            {file && <p className="mt-2 text-sm text-gray-500">Selected: {file.name}</p>}
                        </div>

                        {error && <div className="text-red-600 text-sm">{error}</div>}

                        <button
                            type="submit"
                            disabled={loading || !file}
                            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50"
                        >
                            {loading ? 'Analyzing...' : 'Upload & Analyze'}
                        </button>
                    </form>

                    {result && (
                        <div className="mt-8 border-t pt-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Analysis Results</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <h4 className="font-medium text-gray-700 mb-2">Extracted Data</h4>
                                    <pre className="text-xs overflow-auto max-h-60 bg-white p-2 rounded border">
                                        {JSON.stringify(result.extracted_data, null, 2)}
                                    </pre>
                                </div>
                                <div className="bg-blue-50 p-4 rounded-lg">
                                    <h4 className="font-medium text-blue-900 mb-2">AI Assessment</h4>
                                    <div className="space-y-2">
                                        {result.ai_analysis?.risk_assessment && Object.entries(result.ai_analysis.risk_assessment).map(([key, val]: [string, any]) => (
                                            <div key={key} className="flex justify-between text-sm">
                                                <span className="capitalize text-blue-800">{key.replace('_', ' ')}</span>
                                                <span className="font-bold">{val.level}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="mt-4">
                                        <h5 className="text-sm font-medium text-blue-900">Recommendations:</h5>
                                        <ul className="list-disc list-inside text-sm text-blue-800 mt-1">
                                            {result.ai_analysis?.recommendations?.map((rec: string, i: number) => (
                                                <li key={i}>{rec}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
