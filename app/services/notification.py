from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.services.websocket import manager
from app.schemas.notification import NotificationResponse
from app.services.email import send_urgent_email

async def create_notification(db: Session, notification_in: NotificationCreate) -> Notification:
    notification = Notification(
        user_id=notification_in.user_id,
        title=notification_in.title,
        message=notification_in.message,
        type=notification_in.type,
        priority=notification_in.priority
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Emit via websocket
    try:
        # Convert to pydantic model then to dict for JSON serialization
        response = NotificationResponse.model_validate(notification)
        await manager.send_personal_message(response.model_dump(mode='json'), notification_in.user_id)
    except Exception as e:
        print(f"Error sending websocket message: {e}")

    # Optionally trigger email for high priority here
    if notification.priority.lower() == "high":
        # Query user explicitly to avoid lazy-loading issues in async context
        user = db.query(User).filter(User.id == notification.user_id).first()
        if user and user.email:
            send_urgent_email(
                to_email=user.email,
                title=notification.title,
                message=notification.message,
                time=notification.created_at.strftime("%I:%M %p")
            )

    return notification

