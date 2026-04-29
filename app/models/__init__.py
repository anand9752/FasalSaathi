from app.models.crop import Crop, FarmCropCycle, ManagedCrop
from app.models.farm import Farm, SoilTest
from app.models.inventory import InventoryItem
from app.models.market import MarketPrice
from app.models.user import User
from app.models.weather import WeatherData
from app.models.notification import Notification

all_models = (User, Farm, SoilTest, Crop, FarmCropCycle, ManagedCrop, MarketPrice, WeatherData, InventoryItem, Notification)
