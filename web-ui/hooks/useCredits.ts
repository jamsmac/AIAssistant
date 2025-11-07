'use client';

import { useState, useEffect } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface CreditBalance {
  balance: number;
  total_purchased: number;
  total_spent: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface CreditPackage {
  id: number;
  name: string;
  credits: number;
  price_usd: number;
  bonus_credits: number;
  total_credits: number;
  discount_percentage: number;
  price_per_credit: number;
  description: string | null;
  display_order: number;
}

export interface CreditTransaction {
  id: number;
  user_id: number;
  type: string;
  amount: number;
  balance_before: number;
  balance_after: number;
  description: string | null;
  request_id: number | null;
  payment_id: number | null;
  metadata: string | null;
  created_at: string;
}

export interface TransactionHistory {
  transactions: CreditTransaction[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface CostEstimate {
  estimated_cost_credits: number;
  estimated_tokens: number;
  selected_model: string;
  provider: string;
  quality_score: number;
  cost_tier: string;
  user_balance: number;
  sufficient_credits: boolean;
  task_analysis: {
    task_type: string;
    complexity: string;
    requires_reasoning: boolean;
    requires_code_generation: boolean;
    requires_creativity: boolean;
  };
  reasoning: string;
  credits_per_1k_tokens: number;
}

// Get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

// Fetch with auth
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Hook: Get credit balance
export function useCreditBalance() {
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBalance = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchWithAuth(`${API_URL}/api/credits/balance`);
      setBalance(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch balance');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBalance();
  }, []);

  return { balance, loading, error, refetch: fetchBalance };
}

// Hook: Get credit packages
export function useCreditPackages() {
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPackages = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchWithAuth(`${API_URL}/api/credits/packages`);
        setPackages(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch packages');
      } finally {
        setLoading(false);
      }
    };

    fetchPackages();
  }, []);

  return { packages, loading, error };
}

// Hook: Purchase credits
export function usePurchaseCredits() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const purchase = async (packageId: number, paymentMethod: string = 'stripe') => {
    try {
      setLoading(true);
      setError(null);

      const data = await fetchWithAuth(`${API_URL}/api/credits/purchase`, {
        method: 'POST',
        body: JSON.stringify({
          package_id: packageId,
          payment_method: paymentMethod,
        }),
      });

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Purchase failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { purchase, loading, error };
}

// Hook: Get transaction history
export function useTransactionHistory(limit: number = 50, offset: number = 0) {
  const [history, setHistory] = useState<TransactionHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchWithAuth(
        `${API_URL}/api/credits/history?limit=${limit}&offset=${offset}`
      );
      setHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [limit, offset]);

  return { history, loading, error, refetch: fetchHistory };
}

// Hook: Estimate cost
export function useEstimateCost() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const estimate = async (
    prompt: string,
    preferCheap: boolean = false,
    provider?: string
  ): Promise<CostEstimate | null> => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        prompt,
        prefer_cheap: preferCheap.toString(),
      });

      if (provider) {
        params.append('provider', provider);
      }

      const data = await fetchWithAuth(
        `${API_URL}/api/credits/estimate?${params.toString()}`
      );

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Estimation failed';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { estimate, loading, error };
}
