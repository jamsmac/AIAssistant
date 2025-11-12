'use client'

import { useState } from 'react'
import { Loader2, TrendingUp, TrendingDown, DollarSign, BarChart3, Search } from 'lucide-react'

interface StockAnalysis {
  symbol: string
  price: number
  change: number
  change_percent: number
  analysis: string
  recommendation: string
  technical_indicators: {
    rsi: number
    macd: string
    moving_average_50: number
    moving_average_200: number
  }
}

export default function FinancialPage() {
  const [symbol, setSymbol] = useState('')
  const [analysis, setAnalysis] = useState<StockAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const analyzeStock = async () => {
    if (!symbol) return

    setLoading(true)
    try {
      // TODO: Implement actual API call when backend is ready
      // const response = await fetch(`${API_BASE}/api/financial/analyze/stock?symbol=${symbol}`)
      // const data = await response.json()

      // Mock data for now
      const mockAnalysis: StockAnalysis = {
        symbol: symbol.toUpperCase(),
        price: 150.25,
        change: 2.35,
        change_percent: 1.59,
        analysis: 'Strong buy signal based on technical indicators. RSI shows oversold conditions.',
        recommendation: 'BUY',
        technical_indicators: {
          rsi: 35.2,
          macd: 'Bullish',
          moving_average_50: 148.50,
          moving_average_200: 145.00
        }
      }

      setAnalysis(mockAnalysis)
    } catch (error) {
      console.error('Failed to analyze stock:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Financial Analytics
          </h1>
          <p className="text-gray-600 mt-2">
            AI-powered stock analysis with OpenBB integration
          </p>
        </div>

        {/* Search Box */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Stock Symbol
              </label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="Enter symbol (e.g., AAPL, TSLA)"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyPress={(e) => e.key === 'Enter' && analyzeStock()}
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={analyzeStock}
                disabled={loading || !symbol}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Search size={20} />
                    Analyze
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Analysis Results */}
        {analysis && (
          <div className="space-y-6">
            {/* Price Card */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold text-gray-800">{analysis.symbol}</h2>
                  <p className="text-gray-600 mt-1">Stock Analysis</p>
                </div>
                <div className="text-right">
                  <p className="text-4xl font-bold text-gray-800">${analysis.price.toFixed(2)}</p>
                  <div className={`flex items-center gap-2 justify-end mt-1 ${
                    analysis.change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {analysis.change >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                    <span className="font-semibold">
                      {analysis.change >= 0 ? '+' : ''}{analysis.change.toFixed(2)} ({analysis.change_percent.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className={`rounded-xl shadow-md p-6 ${
              analysis.recommendation === 'BUY' ? 'bg-gradient-to-r from-green-500 to-emerald-500' :
              analysis.recommendation === 'SELL' ? 'bg-gradient-to-r from-red-500 to-pink-500' :
              'bg-gradient-to-r from-yellow-500 to-orange-500'
            } text-white`}>
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                  <BarChart3 size={32} />
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold mb-1">Recommendation: {analysis.recommendation}</h3>
                  <p className="text-white/90">{analysis.analysis}</p>
                </div>
              </div>
            </div>

            {/* Technical Indicators */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <BarChart3 size={24} />
                Technical Indicators
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">RSI (14)</p>
                  <p className="text-2xl font-bold text-gray-800">{analysis.technical_indicators.rsi}</p>
                  <p className="text-xs text-gray-600 mt-1">
                    {analysis.technical_indicators.rsi < 30 ? 'Oversold' :
                     analysis.technical_indicators.rsi > 70 ? 'Overbought' : 'Neutral'}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">MACD</p>
                  <p className="text-2xl font-bold text-gray-800">{analysis.technical_indicators.macd}</p>
                  <p className="text-xs text-gray-600 mt-1">Signal</p>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">MA (50)</p>
                  <p className="text-2xl font-bold text-gray-800">${analysis.technical_indicators.moving_average_50}</p>
                  <p className="text-xs text-gray-600 mt-1">Moving Average</p>
                </div>

                <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">MA (200)</p>
                  <p className="text-2xl font-bold text-gray-800">${analysis.technical_indicators.moving_average_200}</p>
                  <p className="text-xs text-gray-600 mt-1">Moving Average</p>
                </div>
              </div>
            </div>

            {/* Features Coming Soon */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
              <h3 className="text-xl font-bold mb-4">Coming Soon</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <DollarSign className="mb-2" size={24} />
                  <h4 className="font-semibold mb-1">Fundamental Analysis</h4>
                  <p className="text-sm text-blue-100">P/E ratio, earnings, revenue analysis</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <BarChart3 className="mb-2" size={24} />
                  <h4 className="font-semibold mb-1">Advanced Charts</h4>
                  <p className="text-sm text-blue-100">Interactive price charts with indicators</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <TrendingUp className="mb-2" size={24} />
                  <h4 className="font-semibold mb-1">Portfolio Tracking</h4>
                  <p className="text-sm text-blue-100">Track your investments and performance</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!analysis && !loading && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <BarChart3 className="mx-auto text-gray-400 mb-4" size={64} />
            <h3 className="text-xl font-bold text-gray-800 mb-2">Start Your Analysis</h3>
            <p className="text-gray-600">
              Enter a stock symbol above to get AI-powered technical and fundamental analysis
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
