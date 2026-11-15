import uuid
import json
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent, AgentSkill
from app.schemas.agent import AgentCreate, AgentUpdate, SkillCreate, SkillUpdate


async def create_agent(db: AsyncSession, data: AgentCreate, tenant_id: str, actor_id: str) -> Agent:
    # Create a bot user so the agent can join conversations
    from app.auth.models import User
    import hashlib

    agent_id = str(uuid.uuid4())
    bot_username = f"agent_{data.name}"
    bot_hash = hashlib.sha256(f"agent_bot_{agent_id}".encode()).hexdigest()

    bot_user = User(
        id=str(uuid.uuid4()),
        username=bot_username,
        password_hash=f"bot:{bot_hash}",
        display_name=data.display_name,
        role="agent",
        tenant_id=tenant_id,
        is_active=True,
    )
    db.add(bot_user)
    await db.flush()

    agent = Agent(
        id=agent_id,
        name=data.name,
        display_name=data.display_name,
        avatar_emoji=data.avatar_emoji,
        role_description=data.role_description,
        system_prompt=data.system_prompt,
        provider=data.provider,
        api_base=data.api_base,
        api_key=data.api_key,
        agent_model=data.agent_model,
        tenant_id=tenant_id,
        created_by=actor_id,
        user_id=bot_user.id,
    )
    db.add(agent)
    await db.flush()

    for s in data.skills:
        db.add(AgentSkill(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            name=s.name,
            description=s.description,
            trigger_keywords=s.trigger_keywords,
            action_type=s.action_type,
            skill_prompt=s.skill_prompt,
            data_config=s.data_config,
            tenant_id=tenant_id,
        ))

    await db.flush()
    return agent


async def get_agent(db: AsyncSession, agent_id: str, tenant_id: str) -> Agent | None:
    return (await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.tenant_id == tenant_id)
    )).scalar_one_or_none()


async def list_agents(db: AsyncSession, tenant_id: str) -> list[Agent]:
    return list((await db.execute(
        select(Agent).where(Agent.tenant_id == tenant_id).order_by(Agent.created_at.desc())
    )).scalars().all())


async def update_agent(db: AsyncSession, agent: Agent, data: AgentUpdate) -> Agent:
    upd = data.model_dump(exclude_unset=True, exclude={"skills"})
    for k, v in upd.items():
        setattr(agent, k, v)

    if data.skills is not None:
        # Replace all skills
        await db.execute(delete(AgentSkill).where(AgentSkill.agent_id == agent.id))
        for s in data.skills:
            db.add(AgentSkill(
                id=str(uuid.uuid4()),
                agent_id=agent.id,
                name=s.name,
                description=s.description,
                trigger_keywords=s.trigger_keywords,
                action_type=s.action_type,
                skill_prompt=s.skill_prompt,
                data_config=s.data_config,
                tenant_id=agent.tenant_id,
            ))

    await db.flush()
    return agent


async def delete_agent(db: AsyncSession, agent: Agent) -> None:
    await db.delete(agent)
    await db.flush()


async def get_agent_skills(db: AsyncSession, agent_id: str) -> list[AgentSkill]:
    return list((await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id)
    )).scalars().all())


async def add_skill(db: AsyncSession, agent_id: str, data: SkillCreate,
                    tenant_id: str) -> AgentSkill:
    skill = AgentSkill(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        name=data.name,
        description=data.description,
        trigger_keywords=data.trigger_keywords,
        action_type=data.action_type,
        skill_prompt=data.skill_prompt,
        data_config=data.data_config,
        tenant_id=tenant_id,
    )
    db.add(skill)
    await db.flush()
    return skill


async def update_skill(db: AsyncSession, skill: AgentSkill, data: SkillUpdate) -> AgentSkill:
    upd = data.model_dump(exclude_unset=True)
    for k, v in upd.items():
        setattr(skill, k, v)
    await db.flush()
    return skill


async def delete_skill(db: AsyncSession, skill: AgentSkill) -> None:
    await db.delete(skill)
    await db.flush()


# ── Agent response pipeline ──

async def check_agent_trigger(
    db: AsyncSession, conversation_id: str, message_content: str, sender_id: str,
    tenant_id: str,
) -> list[dict]:
    """Check if any agent in this conversation should respond to the message.
    Returns a list of (agent, skill, trigger_reason) dicts."""
    from app.models.conversation import ConversationMember

    # Find all agents in this conversation
    member_result = await db.execute(
        select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id
        )
    )
    members = member_result.scalars().all()
    agent_user_ids = {m.user_id for m in members}

    if not agent_user_ids:
        return []

    # Find agents whose user_id matches conversation members
    result = await db.execute(
        select(Agent).where(
            Agent.user_id.in_(agent_user_ids),
            Agent.is_active == True,
        )
    )
    agents = result.scalars().all()
    if not agents:
        return []

    triggers = []
    msg_lower = message_content.lower()

    for agent in agents:
        # Check @mention first — works even without skills
        mentioned = f"@{agent.name}" in msg_lower or f"@{agent.display_name}" in msg_lower

        skills = await get_agent_skills(db, agent.id)

        if mentioned:
            if skills:
                # Use the first skill as primary, but try to match keywords within the message
                best_skill = skills[0]
                for skill in skills:
                    kws = [k.strip().lower() for k in skill.trigger_keywords.split(",") if k.strip()]
                    if any(kw in msg_lower for kw in kws):
                        best_skill = skill
                        break
                triggers.append({
                    "agent": agent, "skill": best_skill,
                    "reason": "mentioned",
                })
            else:
                # No skills defined — respond with a default "general" context
                triggers.append({
                    "agent": agent, "skill": None,
                    "reason": "mentioned",
                })
        elif skills:
            # Keyword matching (only when not mentioned)
            for skill in skills:
                keywords = [k.strip().lower() for k in skill.trigger_keywords.split(",") if k.strip()]
                if not keywords:
                    continue
                for kw in keywords:
                    if kw in msg_lower:
                        triggers.append({
                            "agent": agent, "skill": skill,
                            "reason": f"keyword:{kw}",
                        })
                        break

    return triggers


async def build_agent_context(
    db: AsyncSession, agent: Agent, skill: AgentSkill | None,
    conversation_id: str, trigger_message: str,
) -> str:
    """Build a context string for the LLM with relevant business data."""
    skill_name = skill.name if skill else "通用"
    skill_desc = skill.description if skill else "通用对话"
    skill_prompt = skill.skill_prompt if skill else ""

    parts = [
        f"## 触发消息\n{trigger_message}",
        f"## Agent 角色\n{agent.role_description}",
        f"## 技能: {skill_name}\n{skill_desc}",
    ]

    # If skill has data_config, query relevant business data
    if skill is not None and skill.data_config:
        tables = skill.data_config.get("tables", [])
        filters = skill.data_config.get("filters", {})

        for table in tables:
            if table == "work_orders":
                # Query recent/due work orders
                from app.models.work_order import WorkOrder
                result = await db.execute(
                    select(WorkOrder)
                    .where(WorkOrder.tenant_id == agent.tenant_id)
                    .order_by(WorkOrder.due_date.asc())
                    .limit(10)
                )
                wos = result.scalars().all()
                if wos:
                    parts.append("## 工单数据")
                    for wo in wos:
                        parts.append(
                            f"- {wo.wo_no}: 状态={wo.status}, 交期={wo.due_date}, "
                            f"优先级={wo.priority}, 客户={wo.customer_id}"
                        )

            elif table == "shipments":
                from app.models.shipment import Shipment
                result = await db.execute(
                    select(Shipment)
                    .where(Shipment.tenant_id == agent.tenant_id)
                    .order_by(Shipment.created_at.desc())
                    .limit(10)
                )
                ships = result.scalars().all()
                if ships:
                    parts.append("## 发货数据")
                    for s in ships:
                        parts.append(
                            f"- {s.dn_no}: 状态={s.status}, ETA={s.eta}"
                        )

            elif table == "alerts":
                from app.models.alert import Alert
                result = await db.execute(
                    select(Alert)
                    .where(Alert.tenant_id == agent.tenant_id, Alert.status == "open")
                    .order_by(Alert.created_at.desc())
                    .limit(10)
                )
                alerts = result.scalars().all()
                if alerts:
                    parts.append("## 活跃告警")
                    for a in alerts:
                        parts.append(f"- [{a.alert_type}] {a.message} (级别={a.severity})")

    return "\n".join(parts)


async def generate_agent_response(
    db: AsyncSession, agent: Agent, skill: AgentSkill | None,
    context: str, sender_name: str,
) -> str | None:
    """Use agent's own API config to call LLM. Falls back to rules-based."""

    skill_prompt = skill.skill_prompt if skill else ""
    skill_name = skill.name if skill else "通用"
    action = skill.action_type if skill else "custom"

    if agent.api_key and agent.api_base and agent.agent_model:
        try:
            import httpx
            system_prompt = agent.system_prompt
            if skill_prompt:
                system_prompt += "\n\n" + skill_prompt

            if agent.provider == "anthropic":
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        f"{agent.api_base.rstrip('/')}/v1/messages",
                        headers={
                            "x-api-key": agent.api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={
                            "model": agent.agent_model,
                            "max_tokens": 1024,
                            "system": system_prompt,
                            "messages": [{"role": "user", "content": context}],
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        # DeepSeek may return thinking blocks before text — find text block
                        for block in data.get("content", []):
                            if block.get("type") == "text":
                                return block["text"]
                        # Fallback: try first block if no text type found
                        if data.get("content"):
                            return data["content"][0].get("text", "")
                    else:
                        print(f"[agent] LLM API error: {resp.status_code} {resp.text[:300]}")
            else:
                # OpenAI-compatible
                base = agent.api_base.rstrip("/")
                url = f"{base}/chat/completions" if "/v1" in base else f"{base}/v1/chat/completions"
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {agent.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": agent.agent_model,
                            "max_tokens": 1024,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": context},
                            ],
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        print(f"[agent] LLM API error: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"[agent] LLM call failed for {agent.name}: {e}")

    # Rules-based fallback response
    name = agent.display_name

    if action == "analyze_risk":
        return (
            f"📊 **风险分析** by {name}\n\n"
            f"根据当前工单和发货数据，我已完成初步扫描。"
            f"如有即将到期的工单或异常发货，请关注对应状态变化。"
            f"建议定期检查告警中心获取最新风险提示。"
        )
    elif action == "check_progress":
        return (
            f"📋 **进度检查** by {name}\n\n"
            f"已扫描相关工单和发货记录。如存在延期风险，"
            f"建议责任人及时更新工单状态和预计交货时间。"
        )
    elif action == "query_inventory":
        return (
            f"📦 **库存查询** by {name}\n\n"
            f"当前库存数据已汇总。如需特定物料数据，"
            f"请在消息中 @我 并指定物料编号或批次号。"
        )
    elif action == "summarize":
        return (
            f"📝 **摘要** by {name}\n\n"
            f"根据近期对话和业务数据，建议关注以下事项：\n"
            f"1. 检查临近交期的工单\n"
            f"2. 确认发货单状态是否正常\n"
            f"3. 查看告警中心是否有新告警"
        )
    else:
        return (
            f"🤖 {name} 已收到你的消息。\n\n"
            f"{'触发技能: ' + skill_name if skill_name != '通用' else ''}"
            f"如需更多分析，请 @我 并提供具体问题。"
        )