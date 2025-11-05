'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    handleOAuthCallback();
  }, []);

  const handleOAuthCallback = async () => {
    try {
      // Get parameters from URL
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      // Check for OAuth errors
      if (error) {
        throw new Error(errorDescription || error);
      }

      if (!code || !state) {
        throw new Error('Missing authorization code or state');
      }

      // Get stored state and provider from sessionStorage
      const storedState = sessionStorage.getItem('oauth_state');
      const provider = sessionStorage.getItem('oauth_provider');

      if (!storedState || !provider) {
        throw new Error('OAuth session expired. Please try again.');
      }

      if (state !== storedState) {
        throw new Error('Invalid state parameter. Possible CSRF attack.');
      }

      // Send callback to backend
      const response = await fetch(`/api/auth/oauth/${provider}/callback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          code,
          state,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const data = await response.json();

      // Clean up sessionStorage
      sessionStorage.removeItem('oauth_state');
      sessionStorage.removeItem('oauth_provider');

      // Store auth data
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
      }

      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }

      setStatus('success');
      setMessage('Authentication successful! Redirecting...');

      // Redirect to dashboard after a short delay
      setTimeout(() => {
        router.push('/');
      }, 1500);

    } catch (error) {
      console.error('OAuth callback error:', error);
      setStatus('error');
      setMessage(error instanceof Error ? error.message : 'Authentication failed');

      // Clean up on error
      sessionStorage.removeItem('oauth_state');
      sessionStorage.removeItem('oauth_provider');

      // Redirect to login after showing error
      setTimeout(() => {
        router.push('/login?error=oauth_failed');
      }, 3000);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-2xl border border-gray-700 p-8 max-w-md w-full">
        <div className="flex flex-col items-center text-center">
          {/* Status Icon */}
          <div className="mb-6">
            {status === 'processing' && (
              <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              </div>
            )}
            {status === 'success' && (
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center animate-fadeIn">
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            )}
            {status === 'error' && (
              <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center animate-fadeIn">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
            )}
          </div>

          {/* Title */}
          <h1 className="text-2xl font-bold text-white mb-2">
            {status === 'processing' && 'Authenticating'}
            {status === 'success' && 'Welcome Back!'}
            {status === 'error' && 'Authentication Failed'}
          </h1>

          {/* Message */}
          <p className={`text-sm ${
            status === 'error' ? 'text-red-400' : 'text-gray-400'
          }`}>
            {message}
          </p>

          {/* Manual Navigation for Error */}
          {status === 'error' && (
            <div className="mt-6 space-y-3 w-full">
              <button
                onClick={() => router.push('/login')}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition"
              >
                Try Again
              </button>
              <button
                onClick={() => router.push('/')}
                className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white font-medium transition"
              >
                Go Home
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}