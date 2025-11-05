import { NextRequest, NextResponse } from 'next/server';

// Simple chat API endpoint
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, sessionId } = body;

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Simple response logic for demonstration
    let response = '';

    if (message.toLowerCase().includes('hello')) {
      response = "Hello! I'm your AI assistant. I can help you with coding, answer questions about the system, or discuss your projects. What would you like to know?";
    } else if (message.toLowerCase().includes('help')) {
      response = "I can help you with:\n\n1. **Coding Questions** - Ask me about any programming language or framework\n2. **System Features** - Learn about agents, workflows, and integrations\n3. **Project Management** - Create and manage your projects\n4. **Analytics** - View system performance and metrics\n\nWhat specific area interests you?";
    } else if (message.toLowerCase().includes('code') || message.toLowerCase().includes('programming')) {
      response = "I'm proficient in multiple programming languages including Python, JavaScript, TypeScript, React, and more. I can help you with:\n\n- Writing code\n- Debugging issues\n- Code reviews\n- Architecture decisions\n- Best practices\n\nWhat coding challenge are you facing?";
    } else if (message.toLowerCase().includes('agents')) {
      response = "Our FractalAgents system is a self-organizing network of AI agents that can:\n\n- **Collaborate** on complex tasks\n- **Specialize** in different domains\n- **Learn** from interactions\n- **Scale** automatically based on demand\n\nYou can view the agent network visualization at /agents. Would you like to know more about specific agent capabilities?";
    } else if (message.toLowerCase().includes('thank')) {
      response = "You're welcome! I'm here to help anytime. Feel free to ask more questions or explore the various features of our system.";
    } else {
      // Default response with some context awareness
      response = `I understand you're asking about "${message}". Let me help you with that.\n\nBased on your question, here are some relevant features in our system:\n\n1. Check out the AI Models Ranking at /models-ranking\n2. View the Agent Network at /agents\n3. Monitor system performance at /admin/monitoring\n4. Analyze metrics at /admin/analytics\n\nFor more specific assistance, please provide additional details about what you're trying to accomplish.`;
    }

    // Simulate AI typing delay
    await new Promise(resolve => setTimeout(resolve, 500));

    return NextResponse.json({
      message: response,
      sessionId: sessionId || `session-${Date.now()}`,
      timestamp: new Date().toISOString(),
      metadata: {
        model: 'gpt-4',
        tokens: message.length + response.length,
        processingTime: 500
      }
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Failed to process chat message' },
      { status: 500 }
    );
  }
}

// GET endpoint to check if chat API is working
export async function GET() {
  return NextResponse.json({
    status: 'Chat API is running',
    endpoints: {
      POST: '/api/chat - Send a message to the AI assistant',
      GET: '/api/chat - Check API status'
    },
    example: {
      method: 'POST',
      body: {
        message: 'Your message here',
        sessionId: 'optional-session-id'
      }
    }
  });
}