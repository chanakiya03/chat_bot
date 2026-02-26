'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

export default function Login() {
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();
    const { login } = useAuth();

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const res = await fetch('http://127.0.0.1:8000/api/auth/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await res.json();

            if (res.ok) {
                login(data.access, data.refresh);
            } else {
                setError(data.detail || 'The email or password you entered is incorrect.');
            }
        } catch (err) {
            setError('Connection error. Please ensure the backend server is running.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            background: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
        }}>
            <div style={{ width: '100%', maxWidth: '400px', textAlign: 'center' }}>
                {/* Logo/Icon */}
                <div style={{ marginBottom: '40px' }}>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        background: '#000000',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 24px',
                        fontSize: '24px',
                        color: '#fff'
                    }}>
                        🎓
                    </div>
                    <h1 style={{
                        fontSize: '32px',
                        fontWeight: 700,
                        color: '#2d333a',
                        margin: 0,
                        letterSpacing: '-0.02em'
                    }}>
                        Welcome back
                    </h1>
                </div>

                {error && (
                    <div style={{
                        background: '#fae2e2',
                        border: '1px solid #e98a8a',
                        color: '#cd2d2d',
                        padding: '12px',
                        borderRadius: '6px',
                        marginBottom: '24px',
                        fontSize: '14px'
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <input
                        type="email"
                        name="email"
                        required
                        placeholder="Email address"
                        onChange={handleChange}
                        style={{
                            height: '52px',
                            padding: '0 16px',
                            borderRadius: '6px',
                            border: '1px solid #d1d5db',
                            fontSize: '16px',
                            outline: 'none'
                        }}
                    />
                    <input
                        type="password"
                        name="password"
                        required
                        placeholder="Password"
                        onChange={handleChange}
                        style={{
                            height: '52px',
                            padding: '0 16px',
                            borderRadius: '6px',
                            border: '1px solid #d1d5db',
                            fontSize: '16px',
                            outline: 'none'
                        }}
                    />

                    <button
                        type="submit"
                        disabled={isLoading}
                        style={{
                            height: '52px',
                            background: '#10a37f',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '16px',
                            fontWeight: 500,
                            cursor: 'pointer',
                            marginTop: '8px',
                            opacity: isLoading ? 0.7 : 1
                        }}
                    >
                        {isLoading ? 'Signing in...' : 'Continue'}
                    </button>
                </form>

                <div style={{ marginTop: '24px', fontSize: '14px', color: '#2d333a' }}>
                    Don't have an account?{' '}
                    <Link href="/signup" style={{ color: '#10a37f', textDecoration: 'none' }}>
                        Sign up
                    </Link>
                </div>

                {/* Footer links */}
                <div style={{ marginTop: '48px', fontSize: '12px', color: '#8e8ea0', display: 'flex', justifyContent: 'center', gap: '16px' }}>
                    <Link href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Terms of use</Link>
                    <span style={{ opacity: 0.5 }}>|</span>
                    <Link href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Privacy policy</Link>
                </div>
            </div>
        </div>
    );
}
