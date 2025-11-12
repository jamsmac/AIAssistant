"""
Example: LLM Integration with Intelligent Routing
Demonstrates how to use the LLM Manager and Router
"""

import asyncio
import os
from agents.llm import LLMManager
from agents.routing import LLMRouter


async def example_basic_llm_usage():
    """Example 1: Basic LLM Manager usage"""
    print("=" * 60)
    print("Example 1: Basic LLM Manager Usage")
    print("=" * 60)
    
    # Initialize LLM Manager (uses API keys from environment)
    llm = LLMManager()
    
    # List available models
    print(f"\nAvailable models: {llm.list_available_models()}")
    print(f"Cheapest model: {llm.get_cheapest_model()}")
    print(f"Best model: {llm.get_best_model()}")
    
    # Simple chat with Anthropic Claude
    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    response = llm.chat(messages, model="haiku")
    
    print(f"\nModel: {response['model']}")
    print(f"Response: {response['content']}")
    print(f"Tokens: {response['usage']['total_tokens']}")
    print(f"Cost: ${response['cost']:.6f}")


async def example_intelligent_routing():
    """Example 2: Intelligent routing with LLM Router"""
    print("\n" + "=" * 60)
    print("Example 2: Intelligent Routing")
    print("=" * 60)
    
    # Initialize router
    router = LLMRouter(prefer_cost_efficiency=True)
    
    # Simple task - should route to cheap model
    simple_task = "What is 2+2?"
    response1 = await router.execute(simple_task)
    
    print(f"\nSimple Task: {simple_task}")
    print(f"Routed to: {response1['routing']['model']}")
    print(f"Complexity: {response1['routing']['complexity']}")
    print(f"Response: {response1['content']}")
    print(f"Cost: ${response1['cost']:.6f}")
    print(f"Saved: ${response1['routing']['cost_saved_vs_gpt4']:.6f}")
    
    # Complex task - should route to powerful model
    complex_task = """
    Analyze the philosophical implications of quantum mechanics on free will,
    considering both deterministic and probabilistic interpretations.
    Provide arguments from multiple perspectives.
    """
    
    response2 = await router.execute(complex_task.strip())
    
    print(f"\nComplex Task: {complex_task.strip()[:50]}...")
    print(f"Routed to: {response2['routing']['model']}")
    print(f"Complexity: {response2['routing']['complexity']}")
    print(f"Response length: {len(response2['content'])} chars")
    print(f"Cost: ${response2['cost']:.6f}")
    print(f"Saved: ${response2['routing']['cost_saved_vs_gpt4']:.6f}")
    
    # Show statistics
    stats = router.get_statistics()
    print(f"\nRouter Statistics:")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Simple tasks: {stats['simple_tasks']}")
    print(f"Complex tasks: {stats['complex_tasks']}")
    print(f"Total saved: ${stats['estimated_cost_saved']:.6f}")
    print(f"Savings: {stats.get('cost_savings_percentage', 0):.1f}%")


async def example_streaming():
    """Example 3: Streaming responses"""
    print("\n" + "=" * 60)
    print("Example 3: Streaming Responses")
    print("=" * 60)
    
    llm = LLMManager()
    
    messages = [
        {"role": "user", "content": "Write a short poem about AI"}
    ]
    
    print("\nStreaming response:")
    print("-" * 40)
    
    for chunk in llm.stream_chat(messages, model="sonnet"):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 40)


async def example_multi_provider():
    """Example 4: Using multiple providers"""
    print("\n" + "=" * 60)
    print("Example 4: Multi-Provider Comparison")
    print("=" * 60)
    
    llm = LLMManager()
    
    prompt = "Explain quantum computing in one sentence."
    messages = [{"role": "user", "content": prompt}]
    
    # Try different models
    models_to_test = ["haiku", "gpt-3.5-turbo", "gemini-flash"]
    
    for model in models_to_test:
        try:
            response = llm.chat(messages, model=model)
            print(f"\n{model}:")
            print(f"  Response: {response['content']}")
            print(f"  Cost: ${response['cost']:.6f}")
        except Exception as e:
            print(f"\n{model}: Not available ({str(e)})")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("LLM Integration Examples")
    print("=" * 60)
    
    # Check for API keys
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    
    print(f"\nAPI Keys configured:")
    print(f"  Anthropic: {'✓' if has_anthropic else '✗'}")
    print(f"  OpenAI: {'✓' if has_openai else '✗'}")
    print(f"  Gemini: {'✓' if has_gemini else '✗'}")
    
    if not (has_anthropic or has_openai or has_gemini):
        print("\n⚠️  No API keys configured!")
        print("Set at least one of:")
        print("  export ANTHROPIC_API_KEY=your_key")
        print("  export OPENAI_API_KEY=your_key")
        print("  export GEMINI_API_KEY=your_key")
        return
    
    try:
        # Run examples
        await example_basic_llm_usage()
        await example_intelligent_routing()
        await example_streaming()
        await example_multi_provider()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
