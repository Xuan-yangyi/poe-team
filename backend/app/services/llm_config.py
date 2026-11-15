import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import LLMConfigCreate, LLMConfigUpdate


async def get_config(db: AsyncSession, tenant_id: str) -> LLMConfig | None:
    return (await db.execute(
        select(LLMConfig).where(LLMConfig.tenant_id == tenant_id, LLMConfig.is_active == True)
        .order_by(LLMConfig.updated_at.desc()).limit(1)
    )).scalar_one_or_none()


async def list_configs(db: AsyncSession, tenant_id: str) -> list[LLMConfig]:
    return list((await db.execute(
        select(LLMConfig).where(LLMConfig.tenant_id == tenant_id)
        .order_by(LLMConfig.created_at.desc())
    )).scalars().all())


async def create_config(db: AsyncSession, data: LLMConfigCreate,
                        tenant_id: str) -> LLMConfig:
    config = LLMConfig(
        id=str(uuid.uuid4()),
        provider=data.provider,
        api_base=data.api_base,
        api_key=data.api_key,
        model=data.model,
        extra_params=data.extra_params,
        description=data.description,
        tenant_id=tenant_id,
    )
    db.add(config)
    await db.flush()
    return config


async def update_config(db: AsyncSession, config: LLMConfig, data: LLMConfigUpdate) -> LLMConfig:
    upd = data.model_dump(exclude_unset=True)
    for k, v in upd.items():
        setattr(config, k, v)
    await db.flush()
    return config


async def delete_config(db: AsyncSession, config: LLMConfig) -> None:
    await db.delete(config)
    await db.flush()


async def test_connection(config: LLMConfig, test_message: str = "Hello, respond 'OK'.") -> dict:
    """Test the LLM connection. Returns {ok: bool, message: str, latency_ms: int}."""
    import time
    start = time.time()

    try:
        if config.provider == "anthropic":
            result = await _test_anthropic(config, test_message)
        else:
            result = await _test_openai_compatible(config, test_message)

        elapsed_ms = int((time.time() - start) * 1000)
        return {"ok": True, "message": result, "latency_ms": elapsed_ms}
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return {"ok": False, "message": str(e), "latency_ms": elapsed_ms}


async def _test_anthropic(config: LLMConfig, message: str) -> str:
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{config.api_base.rstrip('/')}/v1/messages",
            headers={
                "x-api-key": config.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.model,
                "max_tokens": 50,
                "messages": [{"role": "user", "content": message}],
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["content"][0]["text"].strip()
        raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")


async def _test_openai_compatible(config: LLMConfig, message: str) -> str:
    import httpx
    base = config.api_base.rstrip("/")
    url = f"{base}/chat/completions" if "/v1" in base else f"{base}/v1/chat/completions"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.model,
                "max_tokens": 50,
                "messages": [{"role": "user", "content": message}],
                **(config.extra_params or {}),
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")