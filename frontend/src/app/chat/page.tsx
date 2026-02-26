'use client';

import { useWebSocket } from '../../hooks/useWebSocket';
import ChatWindow from '../../components/ChatWindow';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function ChatPage() {
    const { messages, sendMessage, isConnected, isTyping, connectionError } = useWebSocket();
    const { user, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/login');
        }
    }, [user, isLoading, router]);

    if (isLoading || !user) return null;

    return (
        <div style={{
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            background: 'var(--bg-900)',
            position: 'relative',
            overflow: 'hidden',
        }}>
            {/* Background orbs */}
            <div className="orb orb-blue" style={{ width: 400, height: 400, top: -150, left: -100, opacity: 0.15 }} />
            <div className="orb orb-purple" style={{ width: 300, height: 300, bottom: -80, right: -80, opacity: 0.12, animationDelay: '3s' }} />

            {/* Header */}
            <header style={{
                height: 64,
                background: 'rgba(10,14,26,0.9)',
                backdropFilter: 'blur(20px)',
                borderBottom: '1px solid rgba(99,137,255,0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 24px',
                flexShrink: 0,
                zIndex: 10,
            }}>
                {/* Left: brand */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 24 }}>🎓</span>
                        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.1rem' }}>
                            College<span className="gradient-text">Bot</span>
                        </span>
                    </Link>
                </div>

                {/* Center: status */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{
                        width: 8, height: 8, borderRadius: '50%',
                        background: isConnected ? '#10b981' : '#f43f5e',
                        boxShadow: isConnected ? '0 0 8px #10b981' : '0 0 8px #f43f5e',
                        display: 'inline-block',
                    }} />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {isConnected ? 'Connected · AI Ready' : 'Connecting…'}
                    </span>
                </div>

                {/* Right: info */}
                <div style={{
                    fontSize: '0.75rem', color: 'rgba(148,163,184,0.5)',
                    display: 'flex', gap: 16,
                }}>
                    <span>8 Colleges</span>
                    <span>|</span>
                    <span>200+ Courses</span>
                </div>
            </header>

            {/* Main content: sidebar + chat */}
            <div style={{
                flex: 1,
                display: 'flex',
                overflow: 'hidden',
                position: 'relative',
                zIndex: 1,
            }}>
                {/* Sidebar */}
                <aside style={{
                    width: 220,
                    background: 'rgba(15,22,41,0.6)',
                    backdropFilter: 'blur(20px)',
                    borderRight: '1px solid rgba(99,137,255,0.08)',
                    padding: '20px 12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    overflowY: 'auto',
                    flexShrink: 0,
                }}>
                    <p style={{ fontSize: '0.7rem', color: 'rgba(148,163,184,0.4)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8, paddingLeft: 8 }}>
                        Try asking
                    </p>
                    {[
                        { emoji: '🎓', q: 'B.Tech CSE courses available?' },
                        { emoji: '💰', q: 'Cheapest MBA college?' },
                        { emoji: '📊', q: 'Compare HITS and BIHER' },
                        { emoji: '💼', q: 'Best placement college?' },
                        { emoji: '🏠', q: 'Hostel at Hindustan?' },
                        { emoji: '📋', q: 'Admission process at Ethiraj?' },
                        { emoji: '🏆', q: 'Top ranked colleges?' },
                        { emoji: '📚', q: 'BCA colleges in Chennai?' },
                        { emoji: '💊', q: 'Pharmacy courses available?' },
                        { emoji: '⚙️', q: 'Mechanical engineering fees?' },
                    ].map(({ emoji, q }) => (
                        <button
                            key={q}
                            onClick={() => sendMessage(q)}
                            style={{
                                background: 'transparent',
                                border: '1px solid transparent',
                                borderRadius: 8,
                                padding: '8px 10px',
                                textAlign: 'left',
                                fontSize: '0.78rem',
                                color: 'var(--text-secondary)',
                                cursor: 'pointer',
                                display: 'flex', gap: 6, alignItems: 'flex-start',
                                lineHeight: 1.4,
                                transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={e => {
                                (e.currentTarget as HTMLElement).style.background = 'rgba(79,124,255,0.08)';
                                (e.currentTarget as HTMLElement).style.borderColor = 'rgba(79,124,255,0.15)';
                                (e.currentTarget as HTMLElement).style.color = '#f0f4ff';
                            }}
                            onMouseLeave={e => {
                                (e.currentTarget as HTMLElement).style.background = 'transparent';
                                (e.currentTarget as HTMLElement).style.borderColor = 'transparent';
                                (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)';
                            }}
                        >
                            <span>{emoji}</span>
                            <span>{q}</span>
                        </button>
                    ))}
                </aside>

                {/* Chat area */}
                <div style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                }}>
                    <ChatWindow
                        messages={messages}
                        isTyping={isTyping}
                        isConnected={isConnected}
                        connectionError={connectionError}
                        onSendMessage={sendMessage}
                    />
                </div>
            </div>
        </div>
    );
}
