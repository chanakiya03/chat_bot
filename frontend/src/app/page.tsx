'use client';

import { useWebSocket } from '../hooks/useWebSocket';
import ChatWindow from '../components/ChatWindow';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

// Emoji pool cycled per suggestion slot
const EMOJIS = ['🏫', '🎓', '💰', '📝', '🏆', '🚀', '🏥', '🔬', '📍', '💼', '🌟', '🤝', '👩‍🎓', '🏛️', '⏳', '📊', '💻', '🛠️', '🏢', '📸', '📚', '🏠'];

function pickEmoji(idx: number) {
    return EMOJIS[idx % EMOJIS.length];
}

export default function RootPage() {
    const { messages, sendMessage, isConnected, isTyping, connectionError } = useWebSocket();
    const { user, logout, isLoading } = useAuth();
    const router = useRouter();
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    // Redirect if not logged in
    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/login');
        }
    }, [user, isLoading, router]);

    // Circular pool from API — fetched once per session
    const poolRef = useRef<string[]>([]);
    const pointerRef = useRef<number>(0);          // tracks next question to show
    const [visible, setVisible] = useState<string[]>([]);  // 8 shown at a time
    const PAGE_SIZE = 8;

    // Fetch shuffled question pool from backend
    useEffect(() => {
        fetch('http://localhost:8000/api/suggestions/?n=80')
            .then(r => r.json())
            .then(data => {
                const questions: string[] = data.questions || [];
                poolRef.current = questions;
                pointerRef.current = PAGE_SIZE;
                setVisible(questions.slice(0, PAGE_SIZE));
            })
            .catch(() => {
                // Fallback if backend not ready
                const fallback = [
                    'Which colleges have NAAC A++ accreditation?',
                    'Compare HITS and SSN fees',
                    'Best placement college?',
                    'MBA available colleges',
                    'Tell me about MCC',
                    'BSc Computer Science fees',
                    'Does HITS have a hostel?',
                    'Top ranked colleges',
                ];
                poolRef.current = fallback;
                pointerRef.current = fallback.length;
                setVisible(fallback);
            });
    }, []);

    // On click: send the message and replace that slot with the next question in the circular pool
    const handleSuggestionClick = useCallback((q: string) => {
        sendMessage(q);
        setVisible(prev => {
            const pool = poolRef.current;
            if (!pool.length) return prev.filter(s => s !== q);
            const ptr = pointerRef.current % pool.length;
            const next = pool[ptr];
            pointerRef.current = ptr + 1;
            return prev.map(s => (s === q ? next : s));
        });
    }, [sendMessage]);

    // Shuffle visible list (keeps same pool position, just reorders display)
    const handleShuffle = useCallback(() => {
        const pool = poolRef.current;
        if (!pool.length) return;
        const ptr = pointerRef.current;
        const batch = [];
        for (let i = 0; i < PAGE_SIZE; i++) {
            batch.push(pool[(ptr + i) % pool.length]);
        }
        pointerRef.current = (ptr + PAGE_SIZE) % pool.length;
        setVisible(batch);
    }, []);

    return (
        <div style={{
            height: '100vh',
            display: 'flex',
            background: 'var(--bg-900)',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-sans)',
            overflow: 'hidden',
        }}>
            {/* Sidebar */}
            <aside style={{
                width: isSidebarOpen ? 260 : 0,
                transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                background: '#000',
                borderRight: '1px solid var(--border)',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                flexShrink: 0,
            }}>
                <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px' }}>
                        <span style={{ fontSize: '20px' }}>🎓</span>
                        <h1 style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
                            College<span style={{ color: 'var(--accent-blue)' }}>Bot</span>
                        </h1>
                    </div>

                    <button
                        onClick={() => window.location.reload()}
                        style={{
                            background: 'transparent',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-md)',
                            padding: '12px',
                            color: 'var(--text-primary)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            fontSize: '0.9rem',
                            transition: 'background 0.2s',
                            cursor: 'pointer',
                        }}
                        onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-800)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                        <span>➕</span> New Chat
                    </button>

                    <div style={{ flex: 1, overflowY: 'auto', marginTop: '10px' }}>
                        {/* Header row with Shuffle button */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', paddingLeft: '10px', paddingRight: '4px' }}>
                            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', margin: 0 }}>
                                Quick Access
                            </p>
                            <button
                                onClick={handleShuffle}
                                title="Shuffle suggestions"
                                style={{
                                    background: 'transparent',
                                    border: 'none',
                                    color: 'var(--text-muted)',
                                    fontSize: '0.75rem',
                                    cursor: 'pointer',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    transition: 'color 0.2s, background 0.2s',
                                }}
                                onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.background = 'var(--bg-800)'; }}
                                onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent'; }}
                            >
                                🔀 More
                            </button>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            {visible.map((q, idx) => (
                                <button
                                    key={`${q}-${idx}`}
                                    onClick={() => handleSuggestionClick(q)}
                                    style={{
                                        background: 'transparent',
                                        border: 'none',
                                        padding: '10px',
                                        borderRadius: 'var(--radius-sm)',
                                        textAlign: 'left',
                                        fontSize: '0.85rem',
                                        color: 'var(--text-secondary)',
                                        display: 'flex',
                                        gap: '10px',
                                        transition: 'background 0.2s, color 0.2s',
                                        cursor: 'pointer',
                                        width: '100%',
                                    }}
                                    onMouseEnter={e => {
                                        e.currentTarget.style.background = 'var(--bg-800)';
                                        e.currentTarget.style.color = 'var(--text-primary)';
                                    }}
                                    onMouseLeave={e => {
                                        e.currentTarget.style.background = 'transparent';
                                        e.currentTarget.style.color = 'var(--text-secondary)';
                                    }}
                                >
                                    <span>{pickEmoji(idx)}</span>
                                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{q}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                            <div style={{
                                width: 8, height: 8, borderRadius: '50%',
                                background: isConnected ? 'var(--accent-emerald)' : 'var(--accent-rose)'
                            }} />
                            {isConnected ? 'System Online' : 'Connecting...'}
                        </div>

                        {user && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{user.name}</div>
                                <button
                                    onClick={logout}
                                    style={{
                                        background: 'rgba(244, 63, 94, 0.1)',
                                        border: '1px solid rgba(244, 63, 94, 0.2)',
                                        borderRadius: 'var(--radius-sm)',
                                        padding: '8px',
                                        color: 'var(--accent-rose)',
                                        fontSize: '0.8rem',
                                        cursor: 'pointer',
                                    }}
                                >
                                    Logout
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Main Chat Area */}
            <main style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                background: 'var(--bg-900)',
            }}>
                <header style={{
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    borderBottom: '1px solid var(--border)',
                    height: '56px',
                    flexShrink: 0,
                }}>
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        style={{ background: 'transparent', border: 'none', fontSize: '1.2rem', color: 'var(--text-secondary)', cursor: 'pointer' }}
                    >
                        {isSidebarOpen ? '◀' : '▶'}
                    </button>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                        CollegeBot <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: '8px' }}>v2.0</span>
                    </div>
                </header>

                <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                    <ChatWindow
                        messages={messages}
                        isTyping={isTyping}
                        isConnected={isConnected}
                        connectionError={connectionError}
                        onSendMessage={sendMessage}
                    />
                </div>
            </main>
        </div>
    );
}
