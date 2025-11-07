'use client';

import { useState } from 'react';
import { useTransactionHistory } from '@/hooks/useCredits';
import { ArrowUpCircle, ArrowDownCircle, Gift, RotateCcw, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import Link from 'next/link';

export default function TransactionHistoryPage() {
  const [page, setPage] = useState(0);
  const limit = 20;
  const offset = page * limit;

  const { history, loading, error } = useTransactionHistory(limit, offset);

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'purchase':
        return <ArrowUpCircle className="w-5 h-5 text-green-400" />;
      case 'spend':
        return <ArrowDownCircle className="w-5 h-5 text-red-400" />;
      case 'refund':
        return <RotateCcw className="w-5 h-5 text-blue-400" />;
      case 'bonus':
        return <Gift className="w-5 h-5 text-purple-400" />;
      default:
        return <ArrowUpCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getTransactionColor = (type: string) => {
    switch (type) {
      case 'purchase':
        return 'text-green-400';
      case 'spend':
        return 'text-red-400';
      case 'refund':
        return 'text-blue-400';
      case 'bonus':
        return 'text-purple-400';
      default:
        return 'text-gray-400';
    }
  };

  const formatAmount = (amount: number, type: string) => {
    const sign = type === 'spend' ? '-' : '+';
    return `${sign}${Math.abs(amount).toLocaleString()}`;
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <Link
              href="/credits"
              className="text-sm text-gray-400 hover:text-gray-300 mb-2 inline-flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" />
              Back to Credits
            </Link>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Transaction History
            </h1>
            <p className="text-gray-400 mt-2">
              View all your credit transactions
            </p>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : error ? (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-6 text-center">
            <p className="text-red-400">{error}</p>
          </div>
        ) : !history || history.transactions.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
            <p className="text-gray-400 mb-4">No transactions yet</p>
            <Link
              href="/credits"
              className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
            >
              Purchase Credits
            </Link>
          </div>
        ) : (
          <>
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="text-sm text-gray-400 mb-1">Total Transactions</div>
                <div className="text-2xl font-bold">{history.total.toLocaleString()}</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="text-sm text-gray-400 mb-1">Showing</div>
                <div className="text-2xl font-bold">
                  {offset + 1}-{Math.min(offset + limit, history.total)}
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="text-sm text-gray-400 mb-1">Pages</div>
                <div className="text-2xl font-bold">
                  {page + 1} / {Math.ceil(history.total / limit)}
                </div>
              </div>
            </div>

            {/* Transactions Table */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-900 border-b border-gray-700">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Type</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Amount</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Balance</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Description</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {history.transactions.map((transaction) => (
                      <tr
                        key={transaction.id}
                        className="hover:bg-gray-750 transition-colors"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            {getTransactionIcon(transaction.type)}
                            <span className="capitalize font-medium">
                              {transaction.type}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`font-bold ${getTransactionColor(transaction.type)}`}>
                            {formatAmount(transaction.amount, transaction.type)}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-400">
                              {transaction.balance_before.toLocaleString()}
                            </span>
                            <span className="text-gray-600">→</span>
                            <span className="text-yellow-400 font-semibold">
                              {transaction.balance_after.toLocaleString()}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-gray-300">
                          {transaction.description || '-'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-400">
                          {new Date(transaction.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            {history.total > limit && (
              <div className="mt-6 flex items-center justify-between">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                  Previous
                </button>

                <span className="text-sm text-gray-400">
                  Page {page + 1} of {Math.ceil(history.total / limit)}
                </span>

                <button
                  onClick={() => setPage(page + 1)}
                  disabled={!history.has_more}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
