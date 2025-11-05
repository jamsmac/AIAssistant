'use client';

import React, { memo } from 'react';
import { X, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

interface Execution {
  id: number;
  workflow_id: number;
  status: string;
  result: any;
  error: string | null;
  executed_at: string;
}

interface WorkflowExecutionModalProps {
  execution: Execution | null;
  onClose: () => void;
}

const WorkflowExecutionModal = memo(function WorkflowExecutionModal({
  execution,
  onClose
}: WorkflowExecutionModalProps) {
  if (!execution) return null;

  const getStatusIcon = () => {
    switch (execution.status) {
      case 'success':
        return <CheckCircle2 className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Clock className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (execution.status) {
      case 'success':
        return 'text-green-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div className="bg-gray-900 rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
        <div className="p-6 border-b border-gray-700">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-3">
              {getStatusIcon()}
              <div>
                <h2 className="text-xl font-semibold text-white">Execution Details</h2>
                <p className={`text-sm mt-1 ${getStatusColor()}`}>
                  Status: {execution.status}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-800 rounded-lg transition"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
          {/* Metadata */}
          <div className="space-y-2">
            <div className="flex justify-between py-2 border-b border-gray-800">
              <span className="text-sm text-gray-400">Execution ID</span>
              <span className="text-sm text-white font-mono">#{execution.id}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-800">
              <span className="text-sm text-gray-400">Workflow ID</span>
              <span className="text-sm text-white font-mono">#{execution.workflow_id}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-800">
              <span className="text-sm text-gray-400">Executed At</span>
              <span className="text-sm text-white">{formatDate(execution.executed_at)}</span>
            </div>
          </div>

          {/* Error Message */}
          {execution.error && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <h3 className="text-sm font-medium text-red-400 mb-2">Error Message</h3>
              <pre className="text-sm text-red-300 whitespace-pre-wrap font-mono">
                {execution.error}
              </pre>
            </div>
          )}

          {/* Result */}
          {execution.result && (
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-300">Execution Result</h3>

              {/* Action Results */}
              {execution.result.action_results && execution.result.action_results.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Action Results
                  </h4>
                  {execution.result.action_results.map((result: any, index: number) => (
                    <div key={index} className="p-3 bg-gray-800 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-white">
                          Action {index + 1}: {result.action_type || 'Unknown'}
                        </span>
                        {result.success ? (
                          <CheckCircle2 className="w-4 h-4 text-green-500" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-red-500" />
                        )}
                      </div>
                      {result.message && (
                        <p className="text-xs text-gray-400 mb-2">{result.message}</p>
                      )}
                      {result.data && (
                        <pre className="text-xs text-gray-300 bg-gray-900 p-2 rounded overflow-x-auto">
                          {JSON.stringify(result.data, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Metadata */}
              {execution.result.metadata && (
                <div>
                  <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
                    Metadata
                  </h4>
                  <div className="p-3 bg-gray-800 rounded-lg">
                    <pre className="text-xs text-gray-300">
                      {JSON.stringify(execution.result.metadata, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Raw Result (if no structured data) */}
              {!execution.result.action_results && !execution.result.metadata && (
                <div className="p-3 bg-gray-800 rounded-lg">
                  <pre className="text-xs text-gray-300">
                    {typeof execution.result === 'string'
                      ? execution.result
                      : JSON.stringify(execution.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-700">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white font-medium transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
});

export default WorkflowExecutionModal;