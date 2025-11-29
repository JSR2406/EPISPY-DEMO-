import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    VideoCameraIcon,
    ArrowLeftIcon,
    UserCircleIcon,
    CalendarIcon,
    ClockIcon
} from '@heroicons/react/24/outline';

interface Doctor {
    id: string;
    name: string;
    specialty: string;
    rating: number;
    available: boolean;
    nextSlot?: string;
}

export default function Telemedicine() {
    const navigate = useNavigate();
    const [doctors, setDoctors] = useState<Doctor[]>([
        {
            id: '1',
            name: 'Dr. Priya Sharma',
            specialty: 'Infectious Disease Specialist',
            rating: 4.9,
            available: true,
            nextSlot: 'Available Now'
        },
        {
            id: '2',
            name: 'Dr. Rajesh Kumar',
            specialty: 'General Physician',
            rating: 4.7,
            available: true,
            nextSlot: 'Available Now'
        },
        {
            id: '3',
            name: 'Dr. Anita Desai',
            specialty: 'Tropical Medicine Expert',
            rating: 4.8,
            available: false,
            nextSlot: 'Today 4:00 PM'
        }
    ]);

    const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);

    const handleBookConsultation = (doctor: Doctor) => {
        setSelectedDoctor(doctor);
        // In production, this would open a video call interface
        alert(`Booking consultation with ${doctor.name}. In production, this would start a video call.`);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-5xl mx-auto">
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
                        <div className="p-2 bg-teal-50 rounded-lg">
                            <VideoCameraIcon className="h-8 w-8 text-teal-600" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-slate-900">Telemedicine Consultation</h1>
                            <p className="text-slate-500">Connect with doctors instantly via video call</p>
                        </div>
                    </div>

                    {/* Your Health Summary */}
                    <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-xl p-6 mb-8">
                        <div className="flex items-start gap-4">
                            <div className="p-3 bg-red-100 rounded-lg">
                                <UserCircleIcon className="h-6 w-6 text-red-600" />
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-red-900 mb-2">Your Current Health Status</h3>
                                <div className="space-y-1 text-sm text-red-700">
                                    <p>• <strong>Risk Level:</strong> CRITICAL - Dengue Suspected</p>
                                    <p>• <strong>Platelet Count:</strong> 45,000 (Dangerously Low)</p>
                                    <p>• <strong>Symptoms:</strong> Fever, Headache, Body Ache</p>
                                </div>
                                <div className="mt-4 p-3 bg-white rounded-lg border border-red-200">
                                    <p className="text-xs text-red-600 font-medium">
                                        ⚠️ RECOMMENDATION: Immediate medical consultation required. Click below to connect with a specialist.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Available Doctors */}
                    <h2 className="text-xl font-bold text-slate-900 mb-6">Available Doctors</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {doctors.map((doctor, index) => (
                            <motion.div
                                key={doctor.id}
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: index * 0.1 }}
                                className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-start gap-4 mb-4">
                                    <div className="w-16 h-16 bg-gradient-to-br from-teal-400 to-teal-600 rounded-full flex items-center justify-center text-white text-xl font-bold">
                                        {doctor.name.split(' ').map(n => n[0]).join('')}
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-semibold text-slate-900">{doctor.name}</h3>
                                        <p className="text-sm text-slate-600">{doctor.specialty}</p>
                                        <div className="flex items-center gap-1 mt-1">
                                            <span className="text-yellow-500">★</span>
                                            <span className="text-sm font-medium text-slate-700">{doctor.rating}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 mb-4">
                                    {doctor.available ? (
                                        <>
                                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                            <span className="text-sm text-green-600 font-medium">{doctor.nextSlot}</span>
                                        </>
                                    ) : (
                                        <>
                                            <ClockIcon className="h-4 w-4 text-slate-400" />
                                            <span className="text-sm text-slate-500">{doctor.nextSlot}</span>
                                        </>
                                    )}
                                </div>

                                <button
                                    onClick={() => handleBookConsultation(doctor)}
                                    disabled={!doctor.available}
                                    className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all ${doctor.available
                                            ? 'bg-teal-600 text-white hover:bg-teal-700 shadow-md hover:shadow-lg'
                                            : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                                        }`}
                                >
                                    <VideoCameraIcon className="h-5 w-5" />
                                    {doctor.available ? 'Start Video Call' : 'Schedule Appointment'}
                                </button>
                            </motion.div>
                        ))}
                    </div>

                    {/* Features */}
                    <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 bg-teal-50 rounded-lg border border-teal-100">
                            <h4 className="font-semibold text-teal-900 mb-1">Instant Access</h4>
                            <p className="text-sm text-teal-700">Connect with doctors in under 60 seconds</p>
                        </div>
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <h4 className="font-semibold text-blue-900 mb-1">AI-Assisted Diagnosis</h4>
                            <p className="text-sm text-blue-700">Your health data is pre-shared with the doctor</p>
                        </div>
                        <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
                            <h4 className="font-semibold text-purple-900 mb-1">E-Prescription</h4>
                            <p className="text-sm text-purple-700">Get digital prescriptions instantly</p>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
