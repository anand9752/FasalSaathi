import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.price_alert import PriceAlert
from app.models.user import User
from app.schemas.notification import NotificationCreate
from app.services.notification import create_notification
from app.services.market import get_current_prices
from app.services.email import send_urgent_email
from app.core.config import settings

async def check_market_alerts_and_notify():
    print("Checking market price alerts...")
    db = SessionLocal()
    try:
        # Get all active alerts that haven't been notified yet
        active_alerts = db.query(PriceAlert).filter(
            PriceAlert.is_active == True,
            PriceAlert.is_notified == False
        ).all()

        if not active_alerts:
            return

        # Group alerts by commodity to minimize API calls
        commodities = {alert.commodity for alert in active_alerts}
        
        for commodity in commodities:
            # Fetch current live prices for this commodity
            # Note: get_current_prices uses httpx to fetch from Data.gov.in
            live_data = get_current_prices(db, commodity=commodity)
            if not live_data:
                continue
            
            # Use the first available market price as the "current" price for general alert
            current_price = live_data[0].price
            market_name = live_data[0].market_name
            
            # Check alerts for this commodity
            relevant_alerts = [a for a in active_alerts if a.commodity == commodity]
            for alert in relevant_alerts:
                condition_met = False
                if alert.condition == 'above' and current_price >= alert.target_price:
                    condition_met = True
                elif alert.condition == 'below' and current_price <= alert.target_price:
                    condition_met = True
                
                if condition_met:
                    user = db.get(User, alert.user_id)
                    if not user:
                        continue
                        
                    message = f"Price Alert: {commodity} is now ₹{current_price} (Target: {alert.condition} ₹{alert.target_price}) at {market_name}."
                    
                    # 1. Create In-App Notification
                    notif_in = NotificationCreate(
                        title=f"Price Alert: {commodity}",
                        message=message,
                        type="market",
                        priority="high",
                        user_id=user.id
                    )
                    await create_notification(db, notif_in)
                    
                    # 2. Send Email Notification
                    if user.email:
                        send_urgent_email(
                            to_email=user.email,
                            title=f"Market Alert: {commodity} Price Update",
                            message=message,
                            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                    
                    # 3. Mark alert as notified (prevent spam)
                    alert.is_notified = True
                    db.add(alert)
        
        db.commit()
    except Exception as e:
        print(f"Error in market alert service: {e}")
        db.rollback()
    finally:
        db.close()

def start_market_scheduler(scheduler):
    # Check market alerts every 3 hours
    scheduler.add_job(check_market_alerts_and_notify, 'interval', hours=3)
    print("Market price alert scheduler started.")
