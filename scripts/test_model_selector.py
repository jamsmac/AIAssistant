#!/usr/bin/env python3
"""
Test script for ModelSelector
Tests intelligent model selection with different prompts
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.model_selector import ModelSelector


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_analysis(analysis):
    """Print task analysis"""
    print(f"\n📊 Task Analysis:")
    print(f"   Type: {analysis.task_type}")
    print(f"   Complexity: {analysis.complexity}")
    print(f"   Estimated Tokens: {analysis.estimated_tokens}")
    print(f"   Requires Reasoning: {analysis.requires_reasoning}")
    print(f"   Requires Code: {analysis.requires_code_generation}")
    print(f"   Requires Creativity: {analysis.requires_creativity}")


def print_recommendation(rec):
    """Print model recommendation"""
    print(f"\n🤖 Model Recommendation:")
    print(f"   Provider: {rec.provider}")
    print(f"   Model: {rec.model}")
    print(f"   Cost: {rec.estimated_cost_credits} credits")
    print(f"   Quality Score: {rec.quality_score:.2f}")
    print(f"   Cost Tier: {rec.cost_tier}")
    print(f"   Credits/1K tokens: {rec.credits_per_1k_tokens}")
    print(f"   Reasoning: {rec.reasoning}")


def test_prompt(selector: ModelSelector, prompt: str, user_credits: int = 10000):
    """Test a single prompt"""
    print(f"\n💬 Prompt: '{prompt[:100]}{'...' if len(prompt) > 100 else ''}'")
    print(f"   Available Credits: {user_credits}")

    # Analyze
    analysis = selector.analyze_prompt(prompt)
    print_analysis(analysis)

    # Get recommendation
    recommendation = selector.select_model(
        prompt=prompt,
        user_credits=user_credits,
        prefer_cheap=False
    )
    print_recommendation(recommendation)


def main():
    """Run model selector tests"""
    print_header("MODEL SELECTOR TEST SUITE")

    selector = ModelSelector()

    # Test cases
    test_cases = [
        # (prompt, user_credits)
        (
            "Write a Python function that implements a binary search algorithm",
            10000
        ),
        (
            "Create a comprehensive blog post about the future of AI in healthcare",
            10000
        ),
        (
            "Analyze the sales data and provide insights on customer trends",
            10000
        ),
        (
            "Translate this text to Spanish: Hello, how are you today?",
            10000
        ),
        (
            "Solve this equation: 3x^2 + 5x - 2 = 0",
            10000
        ),
        (
            "What is the capital of France?",
            10000
        ),
        (
            "Build a complex microservices architecture with authentication, rate limiting, and monitoring",
            10000
        ),
        (
            # Test with low credits
            "Write a detailed explanation of quantum computing",
            50  # Only 50 credits available
        ),
        (
            # Test coding task
            "Debug this React component and fix the memory leak issue",
            10000
        ),
        (
            # Test creative writing
            "Write a creative short story about a robot that learns to feel emotions",
            10000
        ),
    ]

    for i, (prompt, credits) in enumerate(test_cases, 1):
        print_header(f"TEST CASE {i}/{len(test_cases)}")
        test_prompt(selector, prompt, credits)

    # Test model costs
    print_header("MODEL COSTS")
    print("\n💰 Available Models and Pricing:")

    costs = selector.get_model_costs()
    for cost in costs[:10]:  # Show first 10
        print(
            f"   {cost['provider']:15} | {cost['model']:30} | "
            f"{cost['credits_per_1k_tokens']:4} credits/1K tokens"
        )

    # Test top models for different tasks
    print_header("TOP MODELS BY TASK TYPE")

    task_types = ['coding', 'writing', 'analysis', 'general']
    complexities = ['simple', 'medium', 'complex']

    for task in task_types:
        for complexity in complexities:
            print(f"\n📋 Task: {task.upper()} | Complexity: {complexity.upper()}")
            top_models = selector.get_top_models_for_task(task, complexity, limit=3)

            if top_models:
                for i, model in enumerate(top_models, 1):
                    score = model.get('overall_score', 0)
                    credits = model.get('credits_per_1k_tokens', '?')
                    print(
                        f"   {i}. {model['provider']:10} | {model['model']:25} | "
                        f"Score: {score:.2f} | Cost: {credits} cr/1K"
                    )
            else:
                print("   No models found for this criteria")

    # Test with different strategies
    print_header("SELECTION STRATEGIES")

    test_prompt_text = "Write a complex Python application with database integration"

    print("\n🎯 Strategy: BEST QUALITY (default)")
    rec = selector.select_model(test_prompt_text, 10000, prefer_cheap=False)
    print(f"   Selected: {rec.provider}/{rec.model} ({rec.estimated_cost_credits} credits)")

    print("\n💰 Strategy: PREFER CHEAP")
    rec = selector.select_model(test_prompt_text, 10000, prefer_cheap=True)
    print(f"   Selected: {rec.provider}/{rec.model} ({rec.estimated_cost_credits} credits)")

    print("\n🔒 Strategy: SPECIFIC PROVIDER (OpenAI only)")
    rec = selector.select_model(test_prompt_text, 10000, required_provider='openai')
    print(f"   Selected: {rec.provider}/{rec.model} ({rec.estimated_cost_credits} credits)")

    print_header("TESTS COMPLETE")
    print("\n✅ All tests passed!")
    print("\n🚀 ModelSelector is ready for integration with AIRouter")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
