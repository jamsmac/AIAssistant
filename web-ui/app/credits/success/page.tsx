'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, Loader2, XCircle } from 'lucide-react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Auth token now comes from httpOnly cookies automatically
async function fetchWithAuth(url: string) {
  const response = await fetch(url, {
    credentials: 'include', // Include httpOnly cookies
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export default function PaymentSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    if (!sessionId) {
      setError('No session ID provided');
      setLoading(false);
      return;
    }

    // Verify payment session
    const verifyPayment = async () => {
      try {
        setLoading(true);
        const data = await fetchWithAuth(`${API_URL}/api/credits/session/${sessionId}`);

        if (data.success) {
          setSession(data.session);
        } else {
          setError('Failed to verify payment');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to verify payment');
      } finally {
        setLoading(false);
      }
    };

    verifyPayment();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-400 mx-auto mb-4" />
          <p className="text-gray-400">Verifying your payment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-900/20 border border-red-800 rounded-xl p-8 text-center">
            <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-red-400 mb-2">Payment Verification Failed</h1>
            <p className="text-gray-400 mb-6">{error}</p>
            <Link
              href="/credits"
              className="inline-block px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              Back to Credits
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isPaid = session?.payment_status === 'paid';
  const creditsAmount = session?.metadata?.credits || '0';
  const amountPaid = session?.amount_total || 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-2xl mx-auto">
        {isPaid ? (
          <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-700 rounded-xl p-8 text-center">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-green-400 mb-2">Payment Successful!</h1>
            <p className="text-gray-400 mb-6">
              Your payment has been processed successfully.
            </p>

            <div className="bg-gray-800 rounded-lg p-6 mb-6">
              <div className="grid grid-cols-2 gap-4 text-left">
                <div>
                  <div className="text-sm text-gray-400">Credits Added</div>
                  <div className="text-2xl font-bold text-green-400">
                    {parseInt(creditsAmount).toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">Amount Paid</div>
                  <div className="text-2xl font-bold text-white">
                    ${(amountPaid / 100).toFixed(2)}
                  </div>
                </div>
              </div>

              {session?.customer_email && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="text-sm text-gray-400">Receipt sent to</div>
                  <div className="text-white">{session.customer_email}</div>
                </div>
              )}

              {session?.payment_intent && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="text-sm text-gray-400">Payment ID</div>
                  <div className="text-xs text-gray-500 font-mono">
                    {session.payment_intent}
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/credits/history"
                className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                View Transaction History
              </Link>
              <Link
                href="/chat"
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg transition-colors"
              >
                Start Using Credits
              </Link>
            </div>
          </div>
        ) : (
          <div className="bg-yellow-900/20 border border-yellow-700 rounded-xl p-8 text-center">
            <div className="w-16 h-16 bg-yellow-900/50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Loader2 className="w-8 h-8 text-yellow-400 animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-yellow-400 mb-2">Payment Processing</h1>
            <p className="text-gray-400 mb-6">
              Your payment is being processed. This usually takes a few seconds.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              Status: {session?.payment_status || 'unknown'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-yellow-600 hover:bg-yellow-700 rounded-lg transition-colors"
            >
              Refresh Status
            </button>
          </div>
        )}

        <div className="mt-6 text-center">
          <Link href="/credits" className="text-blue-400 hover:text-blue-300 text-sm">
            ← Back to Credits
          </Link>
        </div>
      </div>
    </div>
  );
}
