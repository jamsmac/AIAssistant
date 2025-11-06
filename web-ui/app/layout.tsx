import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";
import { ToastProvider } from "@/components/ui/Toast";
import { PageErrorBoundary } from "@/components/ErrorBoundary";
import { ThemeProvider } from "@/components/ThemeProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Development System",
  description: "AI-powered development automation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-white dark:bg-gray-950 text-gray-900 dark:text-white transition-colors duration-200`}
      >
        <ThemeProvider>
          <PageErrorBoundary>
            <ToastProvider>
              <Navigation />
              <main className="md:pl-60 pt-16">
                <div className="min-h-screen">
                  {children}
                </div>
              </main>
            </ToastProvider>
          </PageErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  );
}
