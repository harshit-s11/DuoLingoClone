import type { Metadata } from 'next';
import { Nunito } from 'next/font/google';
import './globals.css';
import { QueryProvider } from '@/providers/query-provider';

const nunito = Nunito({
  subsets: ['latin'],
  weight: ['400', '600', '700', '800', '900'],
  variable: '--font-nunito',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Duolingo Clone',
  description: 'Duolingo web-app clone SDE Fullstack project',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={nunito.variable}>
      <body className="antialiased min-h-screen bg-white text-duo-gray-700">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
