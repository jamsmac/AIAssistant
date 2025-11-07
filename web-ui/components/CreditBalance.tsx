'use client';

import { useCreditBalance } from '@/hooks/useCredits';
import { Coins, TrendingUp, TrendingDown, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function CreditBalance() {
  const { balance, loading, error } = useCreditBalance();

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-lg border border-gray-700">
        <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
        <span className="text-sm text-gray-400">Loading...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-red-900/20 rounded-lg border border-red-800">
        <Coins className="w-4 h-4 text-red-400" />
        <span className="text-sm text-red-400">Error</span>
      </div>
    );
  }

  if (!balance) {
    return null;
  }

  // Determine color based on balance
  const getBalanceColor = (bal: number) => {
    if (bal > 1000) return 'text-green-400';
    if (bal > 100) return 'text-yellow-400';
    return 'text-red-400';
  };

  const balanceColor = getBalanceColor(balance.balance);

  return (
    <Link
      href="/credits"
      className="flex items-center gap-3 px-4 py-2 bg-gray-800/50 hover:bg-gray-800 rounded-lg border border-gray-700 hover:border-gray-600 transition-all duration-200 group"
    >
      <div className="flex items-center gap-2">
        <Coins className={`w-5 h-5 ${balanceColor} group-hover:scale-110 transition-transform`} />
        <div className="flex flex-col">
          <span className={`text-sm font-bold ${balanceColor}`}>
            {balance.balance.toLocaleString()}
          </span>
          <span className="text-xs text-gray-500">credits</span>
        </div>
      </div>

      <div className="hidden md:flex items-center gap-3 pl-3 border-l border-gray-700">
        <div className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3 text-green-400" />
          <span className="text-xs text-gray-400">
            {balance.total_purchased.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <TrendingDown className="w-3 h-3 text-red-400" />
          <span className="text-xs text-gray-400">
            {balance.total_spent.toLocaleString()}
          </span>
        </div>
      </div>
    </Link>
  );
}
