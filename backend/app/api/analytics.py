from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, cast, Date, desc
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.message import Message, MessageRoleEnum
from app.models.feedback import Feedback
from app.models.message_source import MessageSource
from app.models.conversation import Conversation
from app.models.department import Department
from app.schemas.analytics import MetricsResponse, ChartDataResponse
from app.api import deps

router = APIRouter(tags=["analytics"])

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role(["admin"]))
):
    # Total students
    students = (await db.execute(select(func.count(User.id)).where(User.role == "student"))).scalar() or 0
    # Total faculty
    faculty = (await db.execute(select(func.count(User.id)).where(User.role == "faculty"))).scalar() or 0
    
    # Total documents
    total_docs = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    approved_docs = (await db.execute(select(func.count(Document.id)).where(Document.status == "approved"))).scalar() or 0
    
    # Questions
    total_qs = (await db.execute(select(func.count(Message.id)).where(Message.role == MessageRoleEnum.user))).scalar() or 0
    
    today = datetime.utcnow() - timedelta(days=1)
    qs_today = (await db.execute(
        select(func.count(Message.id))
        .where(Message.role == MessageRoleEnum.user, Message.created_at >= today)
    )).scalar() or 0
    
    # Unanswered (simplified: let's say all questions get an answer right now in the API, so we just return 0, 
    # but we can count negative feedback as an indicator of unanswered/badly answered)
    neg_fb = (await db.execute(select(func.count(Feedback.id)).where(Feedback.rating == False))).scalar() or 0
    pos_fb = (await db.execute(select(func.count(Feedback.id)).where(Feedback.rating == True))).scalar() or 0
    
    return MetricsResponse(
        total_students=students,
        total_faculty=faculty,
        total_documents=total_docs,
        approved_documents=approved_docs,
        questions_today=qs_today,
        total_questions=total_qs,
        unanswered_questions=neg_fb, # Mapping to bad answers
        positive_feedback=pos_fb,
        negative_feedback=neg_fb
    )

@router.get("/charts", response_model=ChartDataResponse)
async def get_charts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role(["admin"]))
):
    # Questions over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    qot_query = (
        select(
            cast(Message.created_at, Date).label('date'),
            func.count(Message.id).label('count')
        )
        .where(Message.role == MessageRoleEnum.user, Message.created_at >= thirty_days_ago)
        .group_by(cast(Message.created_at, Date))
        .order_by(cast(Message.created_at, Date))
    )
    qot_res = await db.execute(qot_query)
    qot_data = [{"date": row.date.strftime("%Y-%m-%d") if row.date else "", "count": row.count} for row in qot_res.all()]
    
    # Popular categories (using Document.category from message_sources)
    cat_query = (
        select(Document.category, func.count(MessageSource.id).label('count'))
        .join(Document, Document.id == MessageSource.document_id)
        .group_by(Document.category)
        .order_by(desc('count'))
        .limit(5)
    )
    cat_res = await db.execute(cat_query)
    cat_data = [{"name": row.category or "Uncategorized", "value": row.count} for row in cat_res.all()]
    
    # Popular documents
    doc_query = (
        select(Document.title, func.count(MessageSource.id).label('count'))
        .join(Document, Document.id == MessageSource.document_id)
        .group_by(Document.title)
        .order_by(desc('count'))
        .limit(5)
    )
    doc_res = await db.execute(doc_query)
    doc_data = [{"name": row.title, "value": row.count} for row in doc_res.all()]
    
    # Department usage (Users joining Conversations joining Messages)
    # But User department_id is nullable. We join User -> Conversation -> Message
    dept_query = (
        select(Department.name, func.count(Message.id).label('count'))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .join(User, User.id == Conversation.user_id)
        .join(Department, Department.id == User.department_id)
        .where(Message.role == MessageRoleEnum.user)
        .group_by(Department.name)
        .order_by(desc('count'))
    )
    dept_res = await db.execute(dept_query)
    dept_data = [{"name": row.name, "value": row.count} for row in dept_res.all()]
    
    # Feedback trends (Positive vs Negative over time)
    # Using a safe grouping approach that works across SQLite and Postgres
    fb_query_safe = (
        select(
            cast(Feedback.created_at, Date).label('date'),
            Feedback.rating,
            func.count(Feedback.id).label('count')
        )
        .where(Feedback.created_at >= thirty_days_ago)
        .group_by(cast(Feedback.created_at, Date), Feedback.rating)
        .order_by(cast(Feedback.created_at, Date))
    )
    fb_res_safe = await db.execute(fb_query_safe)
    
    fb_dict = {}
    for row in fb_res_safe.all():
        date_str = row.date.strftime("%Y-%m-%d") if row.date else ""
        if date_str not in fb_dict:
            fb_dict[date_str] = {"date": date_str, "positive": 0, "negative": 0}
        if row.rating:
            fb_dict[date_str]["positive"] = row.count
        else:
            fb_dict[date_str]["negative"] = row.count
            
    fb_data = list(fb_dict.values())
    fb_data.sort(key=lambda x: x["date"])
    
    return ChartDataResponse(
        questions_over_time=qot_data,
        popular_categories=cat_data,
        popular_documents=doc_data,
        department_usage=dept_data,
        feedback_trends=fb_data
    )
