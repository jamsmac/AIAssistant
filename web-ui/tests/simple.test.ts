/**
 * Simple test to verify testing setup
 */

import { describe, it, expect } from 'vitest';

describe('Simple Test Suite', () => {
  it('should pass basic arithmetic test', () => {
    expect(2 + 2).toBe(4);
  });

  it('should handle string concatenation', () => {
    const result = 'Hello' + ' ' + 'World';
    expect(result).toBe('Hello World');
  });

  it('should compare objects', () => {
    const obj = { name: 'Test', value: 42 };
    expect(obj).toEqual({ name: 'Test', value: 42 });
  });

  it('should handle arrays', () => {
    const arr = [1, 2, 3, 4, 5];
    expect(arr).toHaveLength(5);
    expect(arr).toContain(3);
  });

  it('should handle boolean logic', () => {
    expect(true).toBeTruthy();
    expect(false).toBeFalsy();
    expect(null).toBeNull();
    expect(undefined).toBeUndefined();
  });
});