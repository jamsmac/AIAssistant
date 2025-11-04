/**
 * React hook for API client with toast notifications
 */

import { useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { apiClient } from './api';

/**
 * Hook to initialize API client with toast handler
 */
export function useApi() {
  const { showToast } = useToast();

  useEffect(() => {
    // Inject toast handler into API client
    apiClient.setToastHandler(showToast);
  }, [showToast]);

  return apiClient;
}

export default useApi;
