"""Seed example agents with demo API config."""
import asyncio
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "..")

from app.database import async_session_factory
from app.services.agent import create_agent
from app.schemas.agent import AgentCreate, SkillCreate

# Default demo API config (user overrides with their own in the UI)
DEMO_PROVIDER = "anthropic"
DEMO_API_BASE = "https://www.sophnet.com/api/open-apis/anthropic"
DEMO_MODEL = "DeepSeek-V4.1-Flash-1017"

AGENTS = [
    {
        "name": "risk_watcher",
        "display_name": "风险巡检员",
        "avatar_emoji": "🛡️",
        "role_description": "监控工单延期风险、发货异常，主动在群聊中预警",
        "system_prompt": (
            "你是供应链风险巡检员。在群聊中监控以下风险并及时提醒:\n"
            "1. 工单即将到期或已超期\n"
            "2. 发货单状态异常\n"
            "3. 库存告急\n"
            "回复风格: 简洁专业，使用 emoji 标注风险级别，引用具体工单号/发货单号。"
        ),
        "provider": DEMO_PROVIDER,
        "api_base": DEMO_API_BASE,
        "api_key": "",
        "agent_model": DEMO_MODEL,
        "skills": [
            {
                "name": "工单风险分析",
                "description": "扫描所有工单，识别延期风险",
                "trigger_keywords": "风险,延期,超期,deadline,工单状态",
                "action_type": "analyze_risk",
                "skill_prompt": "扫描工单数据，识别: 1) 3天内到期 2) 已超期 3) 进度停滞。输出风险列表。",
            },
            {
                "name": "发货异常检测",
                "description": "检测发货延迟和异常",
                "trigger_keywords": "发货,物流,延迟,异常,shipment",
                "action_type": "analyze_risk",
                "skill_prompt": "扫描发货数据，找出状态异常或 ETA 已过的发货单。",
            },
        ],
    },
    {
        "name": "progress_tracker",
        "display_name": "进度追踪员",
        "avatar_emoji": "📋",
        "role_description": "追踪工单生产进展，提供完成率统计和日报",
        "system_prompt": (
            "你是生产进度追踪员。在群聊中:\n"
            "1. 回答工单当前状态和生产进度\n"
            "2. 统计各工单的良率/报废率\n"
            "3. 生成日报摘要\n"
            "回复风格: 数据驱动，使用数字和表格。"
        ),
        "provider": DEMO_PROVIDER,
        "api_base": DEMO_API_BASE,
        "api_key": "",
        "agent_model": DEMO_MODEL,
        "skills": [
            {
                "name": "进度查询",
                "description": "查询工单当前进度",
                "trigger_keywords": "进度,进展,status,怎么样了,到哪了",
                "action_type": "check_progress",
                "skill_prompt": "查询工单当前状态，统计各状态数量，列出生产中工单及进度。",
            },
            {
                "name": "日报摘要",
                "description": "生成本日生产摘要",
                "trigger_keywords": "日报,摘要,总结,today,今天",
                "action_type": "summarize",
                "skill_prompt": "生成本日摘要: 今日新增/完成工单、发货单、活跃告警。",
            },
        ],
    },
    {
        "name": "inventory_guard",
        "display_name": "库存卫士",
        "avatar_emoji": "📦",
        "role_description": "监控库存水位、批次流转，低库存预警",
        "system_prompt": (
            "你是库存管理助手。在群聊中:\n"
            "1. 回答库存查询\n"
            "2. 预警低库存物料\n"
            "3. 追踪批次使用情况\n"
            "回复风格: 精确数字，标注单位和批次号。"
        ),
        "provider": DEMO_PROVIDER,
        "api_base": DEMO_API_BASE,
        "api_key": "",
        "agent_model": DEMO_MODEL,
        "skills": [
            {
                "name": "库存查询",
                "description": "按物料查库存、按批次查流水",
                "trigger_keywords": "库存,库存量,还有多少,库存查询,inventory",
                "action_type": "query_inventory",
                "skill_prompt": "查询库存数据，给出当前库存快照和可用量。",
            },
        ],
    },
]


async def main():
    async with async_session_factory() as db:
        from app.models.agent import Agent
        from sqlalchemy import select

        result = await db.execute(select(Agent).where(Agent.tenant_id == "factory"))
        existing = {a.name for a in result.scalars().all()}

        created = 0
        for a_data in AGENTS:
            if a_data["name"] in existing:
                continue
            skills = [SkillCreate(**s) for s in a_data.pop("skills", [])]
            await create_agent(
                db,
                AgentCreate(**a_data, skills=skills),
                tenant_id="factory",
                actor_id="system",
            )
            created += 1

        await db.commit()
        print(f"Seeded {created} agents (skipped {len(AGENTS) - created} existing)")


if __name__ == "__main__":
    asyncio.run(main())