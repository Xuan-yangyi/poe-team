"""
Seed direct conversations between all test users.
Run: python -m scripts.seed_direct_convs
"""
import asyncio
import uuid
import sys
sys.path.insert(0, ".")

from sqlalchemy import select, text
from app.database import async_session_factory
from app.models.conversation import Conversation, ConversationMember
from app.auth.models import User


async def main():
    async with async_session_factory() as db:
        # Fetch all active test users
        result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()

        if len(users) < 2:
            print("Need at least 2 users to create conversations")
            return

        usernames = [u.username for u in users]
        print(f"Found {len(users)} users: {usernames}")

        # Check existing direct conversations
        existing = await db.execute(
            select(Conversation).where(Conversation.conv_type == "direct")
        )
        existing_direct = existing.scalars().all()
        existing_pairs = set()
        for conv in existing_direct:
            # Find members of this conversation
            mbrs = await db.execute(
                select(ConversationMember.user_id).where(
                    ConversationMember.conversation_id == conv.id
                )
            )
            member_ids = sorted(mbrs.scalars().all())
            if len(member_ids) == 2:
                existing_pairs.add(tuple(member_ids))

        created = 0
        for i, u1 in enumerate(users):
            for u2 in users[i + 1:]:
                uid1, uid2 = str(u1.id), str(u2.id)
                pair = tuple(sorted([uid1, uid2]))
                if pair in existing_pairs:
                    continue

                conv_id = str(uuid.uuid4())
                db.add(Conversation(
                    id=conv_id,
                    conv_type="direct",
                    ref_id=f"dm-{u1.username}-{u2.username}",
                    title="",
                    tenant_id=u1.tenant_id,
                ))
                db.add(ConversationMember(
                    id=str(uuid.uuid4()),
                    conversation_id=conv_id,
                    user_id=uid1,
                    tenant_id=u1.tenant_id,
                ))
                db.add(ConversationMember(
                    id=str(uuid.uuid4()),
                    conversation_id=conv_id,
                    user_id=uid2,
                    tenant_id=u2.tenant_id,
                ))
                created += 1

        await db.commit()
        print(f"Created {created} new direct conversations (total pairs: {len(users) * (len(users) - 1) // 2})")


if __name__ == "__main__":
    asyncio.run(main())