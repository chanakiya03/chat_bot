import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/hooks/useAuth';

export const metadata: Metadata = {
    title: 'CollegeBot — AI-Powered College Enquiry Chatbot',
    description: 'Real-time AI chatbot for college enquiries — courses, fees, placements, and admissions for 8 top Chennai colleges.',
    keywords: 'college chatbot, AI, Chennai colleges, courses, fees, placements, admissions',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>
                <AuthProvider>
                    {children}
                </AuthProvider>
            </body>
        </html>
    );
}
