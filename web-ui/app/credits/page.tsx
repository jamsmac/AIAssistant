'use client';

import { useState } from 'react';
import { useCreditBalance, useCreditPackages, usePurchaseCredits } from '@/hooks/useCredits';
import { Coins, Check, Sparkles, TrendingUp, TrendingDown, Clock, Loader2, ChevronRight } from 'lucide-react';

export default function CreditsPage() {
  const { balance, loading: balanceLoading, refetch: refetchBalance } = useCreditBalance();
  const { packages, loading: packagesLoading } = useCreditPackages();
  const { purchase, loading: purchasing } = usePurchaseCredits();
  const [selectedPackage, setSelectedPackage] = useState<number | null>(null);
  const [purchaseSuccess, setPurchaseSuccess] = useState(false);

  const handlePurchase = async (packageId: number) => {
    try {
      setSelectedPackage(packageId);
      const result = await purchase(packageId, 'stripe');

      if (result.success) {
        setPurchaseSuccess(true);
        await refetchBalance();

        // Reset after 3 seconds
        setTimeout(() => {
          setPurchaseSuccess(false);
          setSelectedPackage(null);
        }, 3000);
      }
    } catch (error) {
      console.error('Purchase failed:', error);
      setSelectedPackage(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Credits
          </h1>
          <p className="text-gray-400">
            Purchase credits to use AI models. Credits never expire.
          </p>
        </div>

        {/* Current Balance */}
        <div className="mb-12 bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-8 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Coins className="w-6 h-6 text-yellow-400" />
                <h2 className="text-xl font-semibold">Current Balance</h2>
              </div>
              {balanceLoading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                  <span className="text-gray-400">Loading...</span>
                </div>
              ) : balance ? (
                <>
                  <div className="text-5xl font-bold text-yellow-400 mb-4">
                    {balance.balance.toLocaleString()}
                  </div>
                  <div className="flex items-center gap-6 text-sm text-gray-400">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-400" />
                      <span>Purchased: {balance.total_purchased.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendingDown className="w-4 h-4 text-red-400" />
                      <span>Spent: {balance.total_spent.toLocaleString()}</span>
                    </div>
                    {balance.updated_at && (
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>Updated: {new Date(balance.updated_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <p className="text-gray-400">No balance information available</p>
              )}
            </div>

            {purchaseSuccess && (
              <div className="bg-green-900/30 border border-green-700 rounded-lg px-6 py-4">
                <div className="flex items-center gap-2 text-green-400">
                  <Check className="w-6 h-6" />
                  <span className="font-semibold">Purchase Successful!</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Credit Packages */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-6">Credit Packages</h2>

          {packagesLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {packages.map((pkg) => {
                const isPopular = pkg.name === 'Basic' || pkg.name === 'Pro';
                const isPurchasing = purchasing && selectedPackage === pkg.id;

                return (
                  <div
                    key={pkg.id}
                    className={`relative bg-gray-800 rounded-xl p-6 border transition-all duration-200 hover:scale-105 ${
                      isPopular
                        ? 'border-blue-500 shadow-lg shadow-blue-500/20'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    {isPopular && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <div className="flex items-center gap-1 bg-gradient-to-r from-blue-500 to-purple-500 px-3 py-1 rounded-full text-xs font-bold">
                          <Sparkles className="w-3 h-3" />
                          POPULAR
                        </div>
                      </div>
                    )}

                    <div className="text-center mb-6">
                      <h3 className="text-2xl font-bold mb-2">{pkg.name}</h3>
                      {pkg.description && (
                        <p className="text-sm text-gray-400">{pkg.description}</p>
                      )}
                    </div>

                    <div className="text-center mb-6">
                      <div className="text-4xl font-bold text-yellow-400 mb-2">
                        {pkg.total_credits.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-400">credits</div>
                      {pkg.bonus_credits > 0 && (
                        <div className="mt-2 inline-block bg-green-900/30 border border-green-700 rounded-full px-3 py-1">
                          <span className="text-xs text-green-400 font-semibold">
                            +{pkg.bonus_credits.toLocaleString()} bonus
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="mb-6">
                      <div className="flex items-baseline justify-center gap-2 mb-2">
                        <span className="text-3xl font-bold">${pkg.price_usd}</span>
                        <span className="text-gray-400">USD</span>
                      </div>
                      <div className="text-center text-sm text-gray-400">
                        ${(pkg.price_per_credit * 1000).toFixed(2)} per 1000 credits
                      </div>
                      {pkg.discount_percentage > 0 && (
                        <div className="text-center text-xs text-green-400 mt-1">
                          Save {pkg.discount_percentage.toFixed(0)}%
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => handlePurchase(pkg.id)}
                      disabled={isPurchasing}
                      className={`w-full py-3 rounded-lg font-semibold transition-all duration-200 flex items-center justify-center gap-2 ${
                        isPopular
                          ? 'bg-gradient-to-r from-blue-500 to-purple-500 hover:shadow-lg hover:shadow-blue-500/50'
                          : 'bg-gray-700 hover:bg-gray-600'
                      } ${isPurchasing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {isPurchasing ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          Purchase
                          <ChevronRight className="w-5 h-5" />
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">How Credits Work</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-400">
            <div>
              <h4 className="font-semibold text-white mb-2">💰 Pay-as-you-go</h4>
              <p>Credits are charged based on AI model usage. Different models have different costs.</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">🤖 Smart Selection</h4>
              <p>Our system automatically selects the best model for your task to optimize cost and quality.</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">♾️ Never Expire</h4>
              <p>Your credits never expire. Buy once and use whenever you need.</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">📊 Full Transparency</h4>
              <p>See exactly how many credits each request will cost before you send it.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
