import asyncio
import os
from agno.agent import Agent
from agno.models.anthropic import Claude
from app.db.supabase_client import get_settings
from dotenv import load_dotenv

async def test_error():
    load_dotenv()
    settings = get_settings()
    model = Claude(
        id="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
        temperature=0.0,
    )
    agent = Agent(
        model=model,
        instructions="Return JSON",
        markdown=False,
    )
    
    try:
        response = await agent.arun("Oferta: Aspirina 10,00")
        print("METRICS:")
        print(getattr(response, "metrics", getattr(response, "run_metrics", "MISSING")))
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == '__main__':
    asyncio.run(test_error())
