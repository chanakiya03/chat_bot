'use client';

import React from 'react';

interface TypingIndicatorProps {
    visible: boolean;
}

export default function TypingIndicator({ visible }: TypingIndicatorProps) {
    if (!visible) return null;
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '8px 0',
            animation: 'fadeIn 0.3s ease',
        }}>
            {/* Bot avatar */}
            <div style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #4f7cff, #8b5cf6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '16px',
                flexShrink: 0,
            }}>🤖</div>

            {/* Dots */}
            <div style={{
                background: 'rgba(20, 28, 53, 0.8)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(99, 137, 255, 0.15)',
                borderRadius: '18px 18px 18px 4px',
                padding: '14px 18px',
                display: 'flex',
                gap: '6px',
                alignItems: 'center',
            }}>
                {[0, 1, 2].map((i) => (
                    <span key={i} style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #4f7cff, #8b5cf6)',
                        display: 'block',
                        animation: `typing-dot 1.4s ease-in-out ${i * 0.2}s infinite`,
                    }} />
                ))}
            </div>
        </div>
    );
}
