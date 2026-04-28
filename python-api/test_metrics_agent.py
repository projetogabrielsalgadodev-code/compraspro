import asyncio
import os
from pprint import pprint
from app.services.offer_extractor import extrair_itens_llm
from app.db.supabase_client import get_settings

async def test_llm():
    from agno.agent import Agent
    from agno.models.anthropic import Claude
    
    settings = get_settings()
    model = Claude(
        id=settings.anthropic_model or "claude-3-5-sonnet-20241022",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
        temperature=0.0,
    )
    agent = Agent(
        model=model,
        instructions="Voce e um extrator de dados. Extraia itens de ofertas farmaceuticas e retorne JSON puro. Sem explicacao.",
        markdown=False,
    )
    
    prompt = "Oferta: ASPIRINA 500MG R$ 10,00"
    response = await agent.arun(prompt)
    print("Response Content:")
    print(response.content)
    print("\nDir(response):")
    print(dir(response))
    print("\nMetrics:")
    if hasattr(response, "metrics"):
        print("has metrics:", response.metrics)
        print("type:", type(response.metrics))
    else:
        print("NO METRICS ATTR")
        
    print("\nRun Response dict:")
    print(response.model_dump() if hasattr(response, "model_dump") else "No model_dump")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_llm())
