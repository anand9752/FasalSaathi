import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.notification import NotificationCreate
from app.services.notification import create_notification
import httpx
from app.core.config import settings

scheduler = AsyncIOScheduler()

async def check_weather_and_notify():
    # This runs every 1 hour
    print("Checking weather for potential alerts...")
    
    # We would loop through users, get their location, and call weather API
    # Since we need lat/lon, let's assume we do this for all users with a farm.
    
    try:
        db = SessionLocal()
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            # Simulated weather check
            condition = "Heavy Rain" 
            
            if condition in ["Heavy Rain", "Storm", "Extreme Heat"]:
                message = f"Warning: {condition} expected in your area. Protect your crops immediately."
                
                notif_in = NotificationCreate(
                    title=f"Weather Alert: {condition}",
                    message=message,
                    type="weather",
                    priority="high",
                    user_id=user.id
                )
                
                await create_notification(db, notif_in)
        db.close()
    except Exception as e:
        print(f"Error checking weather: {e}")

def start_scheduler():
    scheduler.add_job(check_weather_and_notify, 'interval', hours=1)
    scheduler.start()
