'use client';

import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../hooks/useWebSocket';
import TypingIndicator from './TypingIndicator';

/* ── Formatting: convert simple markdown to HTML ── */
function formatMarkdown(text: string): string {
    return text
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/_(.*?)_/g, '<em>$1</em>')
        // Inline code
        .replace(/`(.*?)`/g, '<code>$1</code>')
        // Horizontal rule
        .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid rgba(99,137,255,0.15);margin:10px 0"/>')
        // Table header separator
        .replace(/^\|[-| :]+\|$/gm, '')
        // Table rows → keep as is for now, wrap in table later
        .replace(/\n/g, '<br/>');
}

function formatMessageText(text: string) {
    // Check if text contains markdown table
    if (text.includes('|---|') || text.includes('| --- |')) {
        const lines = text.split('\n');
        let html = '';
        let inTable = false;
        let tableHtml = '';
        let headerDone = false;

        for (const line of lines) {
            const isTableRow = line.trim().startsWith('|') && line.trim().endsWith('|');
            const isSeparator = /^\|[-| :]+\|$/.test(line.trim());

            if (isTableRow && !isSeparator) {
                if (!inTable) {
                    inTable = true;
                    tableHtml = '<table><thead><tr>';
                    headerDone = false;
                }
                const cells = line.trim().split('|').filter(Boolean).map(c => c.trim());
                if (!headerDone) {
                    tableHtml += cells.map(c => `<th>${formatMarkdown(c)}</th>`).join('') + '</tr></thead><tbody>';
                    headerDone = true;
                } else {
                    tableHtml += '<tr>' + cells.map(c => `<td>${formatMarkdown(c)}</td>`).join('') + '</tr>';
                }
            } else if (isSeparator) {
                continue;
            } else {
                if (inTable) {
                    tableHtml += '</tbody></table>';
                    html += tableHtml;
                    tableHtml = '';
                    inTable = false;
                    headerDone = false;
                }
                html += formatMarkdown(line) + '';
            }
        }
        if (inTable) html += tableHtml + '</tbody></table>';
        return html;
    }
    return formatMarkdown(text);
}

/* ── Individual Message Bubble ── */
/* ── Individual Message Bubble ── */
function MessageBubble({ message, onSendMessage }: { message: ChatMessage, onSendMessage: (t: string) => void }) {
    const isUser = message.role === 'user';
    const formattedHtml = formatMessageText(message.text);

    return (
        <div style={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            width: '100%',
            padding: '8px 16px',
            animation: 'fadeIn 0.4s ease',
        }}>
            <div style={{
                maxWidth: '80%',
                display: 'flex',
                flexDirection: isUser ? 'row-reverse' : 'row',
                gap: '12px',
                alignItems: 'flex-start',
            }}>
                {/* Avatar */}
                <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background: isUser ? '#5436DA' : '#10a37f',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '14px',
                    flexShrink: 0,
                    marginTop: '2px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                }}>
                    {isUser ? '👤' : '🤖'}
                </div>

                {/* Content Area */}
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isUser ? 'flex-end' : 'flex-start',
                }}>
                    <div style={{
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        color: 'var(--text-muted)',
                        marginBottom: '4px',
                        padding: '0 4px'
                    }}>
                        {isUser ? 'You' : 'CollegeBot'}
                    </div>

                    <div style={{
                        background: isUser ? 'var(--bg-700)' : 'var(--bg-800)',
                        border: '1px solid var(--border)',
                        borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                        padding: '12px 16px',
                        color: 'var(--text-primary)',
                        fontSize: '0.96rem',
                        lineHeight: '1.6',
                        boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                    }}>
                        <div
                            className="message-content"
                            dangerouslySetInnerHTML={{ __html: formattedHtml }}
                        />


                    </div>

                    {/* Suggestions Chips (Only for Bot Messages) - Moved Inside Flex Column */}
                    {!isUser && message.suggestions && message.suggestions.length > 0 && (
                        <div style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '6px',
                            marginTop: '8px',
                            paddingBottom: '8px',
                            animation: 'fadeInUp 0.5s ease',
                            width: '100%'
                        }}>
                            {message.suggestions.map((s, idx) => {
                                const isRefinement = idx === 0 && s.toLowerCase().includes('did you mean');
                                const displayToken = s.length > 80 ? s.substring(0, 77) + '...' : s;

                                return (
                                    <button
                                        key={s}
                                        onClick={() => onSendMessage(s.replace(/Did you mean\??\s*/i, ''))}
                                        title={s}
                                        style={{
                                            padding: '3px 10px',
                                            borderRadius: '20px',
                                            background: isRefinement ? 'rgba(59, 130, 246, 0.08)' : '#1a1a1a',
                                            border: `1px solid ${isRefinement ? 'rgba(59, 130, 246, 0.3)' : '#333'}`,
                                            color: isRefinement ? '#60a5fa' : '#8a8a8a',
                                            fontSize: '0.7rem',
                                            fontWeight: isRefinement ? 600 : 400,
                                            cursor: 'pointer',
                                            transition: 'all 0.2s ease',
                                            display: 'flex',
                                            alignItems: 'center',
                                            width: 'fit-content',
                                            maxWidth: '350px',
                                            whiteSpace: 'nowrap',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            lineHeight: '1.2'
                                        }}
                                        onMouseEnter={e => {
                                            e.currentTarget.style.background = isRefinement ? 'rgba(59, 130, 246, 0.15)' : '#222';
                                            e.currentTarget.style.borderColor = isRefinement ? '#3b82f6' : '#444';
                                        }}
                                        onMouseLeave={e => {
                                            e.currentTarget.style.background = isRefinement ? 'rgba(59, 130, 246, 0.08)' : '#1a1a1a';
                                            e.currentTarget.style.borderColor = isRefinement ? 'rgba(59, 130, 246, 0.3)' : '#333';
                                        }}
                                    >
                                        {displayToken}
                                    </button>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

/* ── Main Chat Window ── */
interface ChatWindowProps {
    messages: ChatMessage[];
    isTyping: boolean;
    isConnected: boolean;
    connectionError: string | null;
    onSendMessage: (text: string) => void;
}

export default function ChatWindow({
    messages, isTyping, isConnected, connectionError, onSendMessage
}: ChatWindowProps) {
    const [inputValue, setInputValue] = React.useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    const handleSend = () => {
        const text = inputValue.trim();
        if (!text || !isConnected) return;
        onSendMessage(text);
        setInputValue('');
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputValue(e.target.value);
        e.target.style.height = 'auto';
        e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            position: 'relative',
        }}>
            {/* ── Messages Area ── */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
            }}>
                {/* Empty state — show while INIT_CHAT response is loading */}
                {messages.length === 0 && (
                    <div style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '40px 20px',
                        gap: '16px',
                        opacity: 0.5,
                        animation: 'pulse 2s ease-in-out infinite',
                    }}>
                        <div style={{ fontSize: '2.5rem' }}>🎓</div>
                        <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                            CollegeBot is starting up…
                        </p>
                    </div>
                )}

                {/* Messages */}
                {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} onSendMessage={onSendMessage} />
                ))}

                {isTyping && (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 16px' }}>
                        <div style={{ maxWidth: '768px', width: '100%', display: 'flex', gap: '20px' }}>
                            <div style={{ width: 32, height: 32, borderRadius: '4px', background: '#10a37f', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px' }}>🤖</div>
                            <TypingIndicator visible={true} />
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* ── Fixed Input Container ── */}
            <div style={{
                padding: '0 20px 24px',
                background: 'linear-gradient(to top, var(--bg-900) 80%, transparent)',
                display: 'flex',
                justifyContent: 'center',
            }}>
                <div style={{
                    maxWidth: '768px',
                    width: '100%',
                    position: 'relative',
                }}>
                    {connectionError && (
                        <div style={{
                            position: 'absolute', top: '-40px', left: 0, right: 0,
                            textAlign: 'center', fontSize: '0.8rem', color: 'var(--accent-rose)'
                        }}>
                            ⚠️ {connectionError}
                        </div>
                    )}

                    <div style={{
                        background: 'var(--bg-800)',
                        border: '1px solid var(--border)',
                        borderRadius: 'var(--radius-lg)',
                        padding: '10px 14px',
                        display: 'flex',
                        alignItems: 'flex-end',
                        gap: '10px',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
                    }}>
                        <textarea
                            ref={inputRef}
                            rows={1}
                            value={inputValue}
                            onChange={handleInput}
                            onKeyDown={handleKeyDown}
                            placeholder="Message CollegeBot..."
                            disabled={!isConnected}
                            style={{
                                flex: 1,
                                background: 'transparent',
                                border: 'none',
                                outline: 'none',
                                color: 'var(--text-primary)',
                                fontSize: '1rem',
                                padding: '8px 0',
                                resize: 'none',
                                maxHeight: '200px',
                                fontFamily: 'inherit',
                            }}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!isConnected || !inputValue.trim()}
                            style={{
                                width: 32,
                                height: 32,
                                borderRadius: '8px',
                                background: (!isConnected || !inputValue.trim()) ? 'transparent' : '#fff',
                                color: '#000',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '16px',
                                marginBottom: '4px',
                                opacity: (!isConnected || !inputValue.trim()) ? 0.2 : 1,
                                transition: 'all 0.2s',
                            }}
                        >
                            ↑
                        </button>
                    </div>
                    <p style={{
                        textAlign: 'center',
                        fontSize: '0.7rem',
                        color: 'var(--text-muted)',
                        marginTop: '12px'
                    }}>
                        CollegeBot can make mistakes. Check important info.
                    </p>
                </div>
            </div>
        </div>
    );
}
