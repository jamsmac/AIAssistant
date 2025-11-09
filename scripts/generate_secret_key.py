#!/usr/bin/env python3
"""
Генератор криптографически стойких SECRET_KEY для использования в environment variables.

Usage:
    python scripts/generate_secret_key.py [length]

    length: Длина ключа в байтах (по умолчанию 64, рекомендуется для production)
"""

import sys
import secrets
import argparse


def generate_secret_key(length: int = 64) -> str:
    """
    Генерирует криптографически стойкий SECRET_KEY.
    
    Args:
        length: Длина ключа в байтах
        
    Returns:
        Случайный URL-safe base64 ключ
    """
    return secrets.token_urlsafe(length)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a cryptographically secure SECRET_KEY"
    )
    parser.add_argument(
        "length",
        type=int,
        nargs="?",
        default=64,
        help="Key length in bytes (default: 64, recommended for production)"
    )
    
    args = parser.parse_args()
    
    if args.length < 32:
        print("Warning: Keys shorter than 32 bytes are not recommended.", file=sys.stderr)
        print("For production, use at least 64 bytes.", file=sys.stderr)
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    key = generate_secret_key(args.length)
    
    print("\n" + "=" * 70)
    print("Generated SECRET_KEY:")
    print("=" * 70)
    print(key)
    print("=" * 70)
    print(f"\nLength: {len(key)} characters")
    print(f"Entropy: {args.length * 8} bits")
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={key}")
    print("\nOr set as environment variable:")
    print(f"export SECRET_KEY='{key}'")
    print("\n⚠️  IMPORTANT: Keep this key secret! Never commit it to git!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

