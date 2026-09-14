import asyncio
from app.db.database import AsyncSessionLocal
from app.models.user import User, RoleEnum
from app.security.auth import get_password_hash
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        # Create student
        res = await db.execute(select(User).where(User.email == "student@college.edu"))
        user = res.scalars().first()
        if not user:
            user = User(
                name="Student",
                email="student@college.edu",
                password_hash=get_password_hash("password123"),
                role=RoleEnum.student,
                is_active=True
            )
            db.add(user)
            await db.commit()
            print("Created student@college.edu / password123")
        else:
            print("Student exists:", user.email)

        # Create admin
        res_admin = await db.execute(select(User).where(User.email == "admin@college.edu"))
        admin_user = res_admin.scalars().first()
        if not admin_user:
            admin_user = User(
                name="Admin",
                email="admin@college.edu",
                password_hash=get_password_hash("password123"),
                role=RoleEnum.admin,
                is_active=True
            )
            db.add(admin_user)
            await db.commit()
            print("Created admin@college.edu / password123")
        else:
            print("Admin exists:", admin_user.email)

asyncio.run(main())
