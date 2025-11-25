from src.celery_app import celery
from sqlalchemy import select
from src.database import SessionLocal
from src.models import ActivationToken
from datetime import datetime, timezone

@celery.task
def delete_expired_tokens():
    import asyncio

    async def _delete():
        async with SessionLocal() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(ActivationToken).where(ActivationToken.expires_at < now)
            )
            tokens = result.scalars().all()
            if tokens:
                print(f"Deleting {len(tokens)} expired tokens...")
                for token in tokens:
                    await db.delete(token)
                await db.commit()
            else:
                print("No expired tokens found.")

    asyncio.run(_delete())
