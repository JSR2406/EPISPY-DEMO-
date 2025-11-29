import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    ChatBubbleLeftRightIcon,
    ArrowLeftIcon,
    PaperAirplaneIcon,
    SparklesIcon
} from '@heroicons/react/24/outline';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'ai';
    timestamp: Date;
}

export default function AIHealthAssistant() {
    const navigate = useNavigate();
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            text: "Hello! I'm your AI Health Assistant. I can help you understand your symptoms, interpret test results, and provide health guidance. How can I help you today?",
            sender: 'ai',
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);

    const quickQuestions = [
        "What are dengue symptoms?",
        "Explain my blood test results",
        "When should I see a doctor?",
        "How to prevent malaria?"
    ];

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            text: input,
            sender: 'user',
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        // Simulate AI response
        setTimeout(() => {
            const aiResponse: Message = {
                id: (Date.now() + 1).toString(),
                text: generateAIResponse(input),
                sender: 'ai',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, aiResponse]);
            setIsTyping(false);
        }, 1500);
    };

    const generateAIResponse = (question: string): string => {
        const lowerQ = question.toLowerCase();

        if (lowerQ.includes('dengue') && lowerQ.includes('symptom')) {
            return "Dengue fever symptoms typically include:\n\n• High fever (104°F/40°C)\n• Severe headache\n• Pain behind the eyes\n• Joint and muscle pain\n• Nausea and vomiting\n• Skin rash\n\n⚠️ WARNING SIGNS:\n• Severe abdominal pain\n• Persistent vomiting\n• Bleeding gums or nose\n• Blood in stool\n\nIf you experience warning signs, seek immediate medical attention!";
        }

        if (lowerQ.includes('blood test') || lowerQ.includes('result')) {
            return "Based on your recent blood test:\n\n🔴 CRITICAL: Platelet count is 45,000 (Normal: 150,000-400,000)\n\nThis indicates severe thrombocytopenia, commonly seen in dengue hemorrhagic fever.\n\n📋 IMMEDIATE ACTIONS:\n1. Hospitalization required\n2. Monitor for internal bleeding\n3. Avoid aspirin/ibuprofen\n4. Stay hydrated with ORS\n\nYour doctor should be contacted immediately.";
        }

        if (lowerQ.includes('doctor') || lowerQ.includes('hospital')) {
            return "You should see a doctor IMMEDIATELY if you have:\n\n🚨 EMERGENCY:\n• Difficulty breathing\n• Severe chest pain\n• Confusion or altered consciousness\n• Severe bleeding\n• Platelet count < 50,000\n\n⚠️ URGENT (within 24 hours):\n• Persistent high fever (>3 days)\n• Severe headache\n• Persistent vomiting\n• Abdominal pain\n\nBased on your current health data, I recommend immediate medical consultation.";
        }

        return "I understand your concern. Based on your health profile and current epidemic trends in your area, I recommend:\n\n1. Monitor your symptoms daily\n2. Stay hydrated\n3. Avoid mosquito exposure\n4. Get adequate rest\n\nWould you like me to schedule a telemedicine consultation?";
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
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
                    className="glass-panel rounded-2xl flex-1 flex flex-col overflow-hidden"
                >
                    {/* Header */}
                    <div className="p-6 border-b border-slate-200">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-teal-50 rounded-lg">
                                <SparklesIcon className="h-6 w-6 text-teal-600" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-slate-900">AI Health Assistant</h1>
                                <p className="text-sm text-slate-500">Powered by Medical AI • Always Available</p>
                            </div>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-4">
                        {messages.map((message) => (
                            <motion.div
                                key={message.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div className={`max-w-[80%] rounded-2xl p-4 ${message.sender === 'user'
                                        ? 'bg-teal-600 text-white'
                                        : 'bg-white border border-slate-200 text-slate-900'
                                    }`}>
                                    <p className="whitespace-pre-line">{message.text}</p>
                                    <span className={`text-xs mt-2 block ${message.sender === 'user' ? 'text-teal-100' : 'text-slate-400'
                                        }`}>
                                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                            </motion.div>
                        ))}

                        {isTyping && (
                            <div className="flex justify-start">
                                <div className="bg-white border border-slate-200 rounded-2xl p-4">
                                    <div className="flex gap-1">
                                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Quick Questions */}
                    <div className="px-6 py-3 border-t border-slate-200 bg-slate-50">
                        <p className="text-xs text-slate-500 mb-2">Quick questions:</p>
                        <div className="flex flex-wrap gap-2">
                            {quickQuestions.map((q, i) => (
                                <button
                                    key={i}
                                    onClick={() => setInput(q)}
                                    className="text-xs px-3 py-1.5 bg-white border border-slate-200 rounded-full hover:border-teal-500 hover:bg-teal-50 transition-colors"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Input */}
                    <div className="p-6 border-t border-slate-200">
                        <div className="flex gap-3">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                                placeholder="Ask me anything about your health..."
                                className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:border-teal-500 focus:ring-2 focus:ring-teal-200 outline-none"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim()}
                                className="btn-primary px-6 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <PaperAirplaneIcon className="h-5 w-5" />
                                Send
                            </button>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
