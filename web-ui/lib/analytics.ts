/**
 * Analytics Integration
 * Google Analytics 4 and Custom Events
 */

import React from 'react';

declare global {
  interface Window {
    gtag: (...args: any[]) => void;
    dataLayer: any[];
  }
}

interface AnalyticsEvent {
  action: string;
  category: string;
  label?: string;
  value?: number;
  custom_parameters?: Record<string, any>;
}

class Analytics {
  private initialized = false;
  private userId: string | null = null;
  private sessionId: string;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.initialize();
  }

  /**
   * Initialize Google Analytics
   */
  private initialize() {
    if (typeof window === 'undefined') return;

    const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

    if (!GA_MEASUREMENT_ID) {
      console.log('Analytics: GA Measurement ID not configured');
      return;
    }

    // Load Google Analytics script
    const script1 = document.createElement('script');
    script1.async = true;
    script1.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
    document.head.appendChild(script1);

    // Initialize gtag
    window.dataLayer = window.dataLayer || [];
    window.gtag = function() {
      window.dataLayer.push(arguments);
    };
    window.gtag('js', new Date());

    // Configure GA
    window.gtag('config', GA_MEASUREMENT_ID, {
      page_path: window.location.pathname,
      custom_map: {
        dimension1: 'user_type',
        dimension2: 'session_id',
      },
    });

    this.initialized = true;
    console.log('Analytics: Initialized');
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * Set user ID for tracking
   */
  setUserId(userId: string) {
    this.userId = userId;

    if (this.initialized && window.gtag) {
      window.gtag('config', process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID!, {
        user_id: userId,
      });
    }
  }

  /**
   * Track page view
   */
  trackPageView(path: string, title?: string) {
    if (!this.initialized || !window.gtag) return;

    window.gtag('event', 'page_view', {
      page_path: path,
      page_title: title || document.title,
      user_id: this.userId,
      session_id: this.sessionId,
    });
  }

  /**
   * Track custom events
   */
  trackEvent(event: AnalyticsEvent) {
    if (!this.initialized || !window.gtag) return;

    window.gtag('event', event.action, {
      event_category: event.category,
      event_label: event.label,
      value: event.value,
      user_id: this.userId,
      session_id: this.sessionId,
      ...event.custom_parameters,
    });
  }

  /**
   * Track user interactions
   */
  trackInteraction(element: string, action: string, label?: string) {
    this.trackEvent({
      action: 'interaction',
      category: 'UI',
      label: `${element}_${action}${label ? `_${label}` : ''}`,
    });
  }

  /**
   * Track API calls
   */
  trackApiCall(endpoint: string, method: string, status: number, duration: number) {
    this.trackEvent({
      action: 'api_call',
      category: 'API',
      label: `${method} ${endpoint}`,
      value: duration,
      custom_parameters: {
        status_code: status,
        success: status < 400,
      },
    });
  }

  /**
   * Track errors
   */
  trackError(error: Error, context?: string) {
    this.trackEvent({
      action: 'error',
      category: 'Error',
      label: context || error.message,
      custom_parameters: {
        error_message: error.message,
        error_stack: error.stack,
      },
    });
  }

  /**
   * Track performance metrics
   */
  trackPerformance(metric: string, value: number, unit: string = 'ms') {
    this.trackEvent({
      action: 'performance',
      category: 'Performance',
      label: metric,
      value,
      custom_parameters: {
        unit,
      },
    });
  }

  /**
   * Track user authentication
   */
  trackAuth(action: 'login' | 'logout' | 'register', method?: string) {
    this.trackEvent({
      action: `auth_${action}`,
      category: 'Authentication',
      label: method,
    });

    if (action === 'logout') {
      this.userId = null;
    }
  }

  /**
   * Track feature usage
   */
  trackFeature(feature: string, action: string, metadata?: Record<string, any>) {
    this.trackEvent({
      action: 'feature_usage',
      category: 'Features',
      label: `${feature}_${action}`,
      custom_parameters: metadata,
    });
  }

  /**
   * Track conversions
   */
  trackConversion(type: string, value?: number, currency: string = 'USD') {
    if (!this.initialized || !window.gtag) return;

    window.gtag('event', 'conversion', {
      value,
      currency,
      conversion_type: type,
      user_id: this.userId,
      session_id: this.sessionId,
    });
  }

  /**
   * Track search queries
   */
  trackSearch(query: string, results: number, category?: string) {
    this.trackEvent({
      action: 'search',
      category: 'Search',
      label: category,
      value: results,
      custom_parameters: {
        search_term: query,
        results_count: results,
      },
    });
  }

  /**
   * Track timing
   */
  trackTiming(category: string, variable: string, value: number, label?: string) {
    if (!this.initialized || !window.gtag) return;

    window.gtag('event', 'timing_complete', {
      event_category: category,
      name: variable,
      value,
      event_label: label,
    });
  }

  /**
   * Track social interactions
   */
  trackSocial(network: string, action: string, target: string) {
    this.trackEvent({
      action: 'social',
      category: 'Social',
      label: `${network}_${action}`,
      custom_parameters: {
        target,
      },
    });
  }

  /**
   * Track e-commerce events
   */
  trackEcommerce(action: string, data: Record<string, any>) {
    if (!this.initialized || !window.gtag) return;

    window.gtag('event', action, {
      ...data,
      user_id: this.userId,
      session_id: this.sessionId,
    });
  }

  /**
   * Get analytics instance
   */
  static getInstance(): Analytics {
    if (!(window as any).__analytics) {
      (window as any).__analytics = new Analytics();
    }
    return (window as any).__analytics;
  }
}

// Export singleton instance
export const analytics = typeof window !== 'undefined' ? Analytics.getInstance() : null;

// React Hook for analytics
export function useAnalytics() {
  return analytics;
}

// HOC for tracking page views
export function withAnalytics<P extends object>(
  Component: React.ComponentType<P>,
  pageName?: string
) {
  return (props: P) => {
    if (typeof window !== 'undefined' && analytics) {
      analytics.trackPageView(window.location.pathname, pageName);
    }
    return React.createElement(Component as any, props);
  };
}

// Utility functions
export const trackEvent = (event: AnalyticsEvent) => {
  analytics?.trackEvent(event);
};

export const trackPageView = (path: string, title?: string) => {
  analytics?.trackPageView(path, title);
};

export const trackError = (error: Error, context?: string) => {
  analytics?.trackError(error, context);
};

export const trackFeature = (feature: string, action: string, metadata?: Record<string, any>) => {
  analytics?.trackFeature(feature, action, metadata);
};

export const trackAuth = (action: 'login' | 'logout' | 'register', method?: string) => {
  analytics?.trackAuth(action, method);
};

export const trackSearch = (query: string, results: number, category?: string) => {
  analytics?.trackSearch(query, results, category);
};

export const trackTiming = (category: string, variable: string, value: number, label?: string) => {
  analytics?.trackTiming(category, variable, value, label);
};