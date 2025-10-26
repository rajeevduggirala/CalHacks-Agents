"""
Database models and utilities for Agentic Grocery
Uses SQLite with SQLAlchemy ORM for user management and profiles
"""

import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from passlib.context import CryptContext

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_agentic_grocery.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing - use pbkdf2_sha256 as fallback
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


# Models
class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)  # Full name
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    recipes = relationship("Recipe", back_populates="user")
    grocery_lists = relationship("GroceryList", back_populates="user")
    meal_history = relationship("MealHistory", back_populates="user")
    daily_plans = relationship("DailyMealPlan", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user")
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash (truncate to 72 bytes for bcrypt compatibility)"""
        # bcrypt has a 72-byte limit, so truncate if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncate to 72 bytes and decode back to string
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(password, self.hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password (truncate to 72 bytes for bcrypt compatibility)"""
        # bcrypt has a 72-byte limit, so truncate if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncate to 72 bytes and decode back to string
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)


class UserProfile(Base):
    """User dietary profile and preferences"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Required dietary information
    daily_calories = Column(Float, nullable=False)  # Daily calorie target
    dietary_restrictions = Column(JSON, nullable=False)  # Includes allergies, diet type, restrictions
    likes = Column(JSON, nullable=False)  # Cuisines and flavor profiles (spicy, sweet, etc.)
    additional_information = Column(String)  # Free text for additional food preferences
    
    # Physical information
    height_cm = Column(Float)
    weight_kg = Column(Float)
    goal = Column(String)  # cut, bulk, maintain
    diet = Column(String)  # vegetarian, vegan, etc.
    workout_frequency = Column(String)
    
    # Preferences
    dislikes = Column(JSON)
    allergies = Column(JSON)
    
    # Optional macros
    target_protein_g = Column(Float)
    target_carbs_g = Column(Float)
    target_fat_g = Column(Float)
    target_calories = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")


class Recipe(Base):
    """Recipe model for daily meal planning"""
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Basic recipe info
    title = Column(String, nullable=False)
    description = Column(String)
    meal_type = Column(String, nullable=False)  # breakfast, lunch, dinner
    cook_time = Column(String)
    prep_time = Column(String)
    servings = Column(Integer, default=1)
    cuisine = Column(String)
    difficulty = Column(String)
    
    # Macros per serving
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
    calories = Column(Float)
    fiber_g = Column(Float)
    
    # Recipe details
    ingredients = Column(JSON)  # List of {name, quantity, unit}
    instructions = Column(String)  # Markdown formatted instructions
    image_url = Column(String)
    
    # User interaction tracking
    times_generated = Column(Integer, default=0)
    times_selected = Column(Integer, default=0)
    user_rating = Column(Float, nullable=True)  # Average rating
    is_favorite = Column(Boolean, default=False)
    
    # ChromaDB integration
    chroma_id = Column(String, unique=True)  # ChromaDB document ID
    embedding_vector = Column(JSON)  # Store embedding for similarity search
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="recipes")


class DailyMealPlan(Base):
    """Daily meal plans for users"""
    __tablename__ = "daily_meal_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, nullable=False)  # Date for the meal plan
    
    # Generated recipes for each meal
    breakfast_recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    lunch_recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    dinner_recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # Overall day rating 1-5
    notes = Column(String, nullable=True)
    
    # Status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="daily_plans")
    breakfast_recipe = relationship("Recipe", foreign_keys=[breakfast_recipe_id])
    lunch_recipe = relationship("Recipe", foreign_keys=[lunch_recipe_id])
    dinner_recipe = relationship("Recipe", foreign_keys=[dinner_recipe_id])

class UserPreference(Base):
    """User preference learning for ChromaDB"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Preference data
    preference_type = Column(String, nullable=False)  # "liked", "disliked", "avoid"
    item_name = Column(String, nullable=False)  # Recipe title, ingredient, cuisine
    item_type = Column(String, nullable=False)  # "recipe", "ingredient", "cuisine", "flavor"
    
    # Context
    context = Column(String)  # Why they liked/disliked it
    strength = Column(Float, default=1.0)  # Preference strength 0.0-1.0
    
    # ChromaDB integration
    chroma_id = Column(String, unique=True)
    embedding_vector = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")

class GroceryList(Base):
    """User's grocery lists"""
    __tablename__ = "grocery_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    
    name = Column(String, nullable=False)
    store = Column(String)
    total_cost = Column(Float)
    items = Column(JSON)  # List of {name, quantity, category, price}
    
    # Status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="grocery_lists")


class MealHistory(Base):
    """Track user's meal history for learning preferences"""
    __tablename__ = "meal_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    
    date = Column(DateTime, default=datetime.utcnow)
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    recipe_title = Column(String)
    
    # Actual macros consumed
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
    calories = Column(Float)
    
    # User feedback
    rating = Column(Integer, nullable=True)  # 1-5 stars
    notes = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="meal_history")


# Database helper functions
def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")


def create_user(db: Session, email: str, username: str, password: str) -> User:
    """Create a new user"""
    hashed_password = User.hash_password(password)
    db_user = User(
        email=email,
        username=username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def create_user_profile(db: Session, user_id: int, profile_data: dict) -> UserProfile:
    """Create or update user profile"""
    # Check if profile exists
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if profile:
        # Update existing
        for key, value in profile_data.items():
            setattr(profile, key, value)
    else:
        # Create new
        profile = UserProfile(user_id=user_id, **profile_data)
        db.add(profile)
    
    db.commit()
    db.refresh(profile)
    return profile


def save_recipe(db: Session, user_id: int, recipe_data: dict) -> Recipe:
    """Save a recipe for user"""
    recipe = Recipe(user_id=user_id, **recipe_data)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def create_grocery_list(db: Session, user_id: int, list_data: dict) -> GroceryList:
    """Create grocery list"""
    grocery_list = GroceryList(user_id=user_id, **list_data)
    db.add(grocery_list)
    db.commit()
    db.refresh(grocery_list)
    return grocery_list


def log_meal(db: Session, user_id: int, meal_data: dict) -> MealHistory:
    """Log a meal in history"""
    meal = MealHistory(user_id=user_id, **meal_data)
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


def create_daily_meal_plan(db: Session, user_id: int, date: datetime, 
                          breakfast_recipe_id: int, lunch_recipe_id: int, dinner_recipe_id: int) -> DailyMealPlan:
    """Create a daily meal plan"""
    meal_plan = DailyMealPlan(
        user_id=user_id,
        date=date,
        breakfast_recipe_id=breakfast_recipe_id,
        lunch_recipe_id=lunch_recipe_id,
        dinner_recipe_id=dinner_recipe_id
    )
    db.add(meal_plan)
    db.commit()
    db.refresh(meal_plan)
    return meal_plan


def get_daily_meal_plan(db: Session, user_id: int, date: datetime) -> Optional[DailyMealPlan]:
    """Get daily meal plan for a specific date"""
    return db.query(DailyMealPlan).filter(
        DailyMealPlan.user_id == user_id,
        DailyMealPlan.date == date
    ).first()


def create_user_preference(db: Session, user_id: int, preference_data: dict) -> UserPreference:
    """Create a user preference"""
    preference = UserPreference(user_id=user_id, **preference_data)
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Create test user
    db = SessionLocal()
    try:
        test_user = create_user(
            db,
            email="test@example.com",
            username="testuser",
            password="testpassword123"
        )
        print(f"✅ Created test user: {test_user.email}")
        
        # Create test profile
        test_profile = create_user_profile(
            db,
            user_id=test_user.id,
            profile_data={
                "height_cm": 175,
                "weight_kg": 70,
                "goal": "cut",
                "diet": "vegetarian",
                "workout_frequency": "5/week",
                "likes": ["spicy", "south indian"],
                "dislikes": ["mushrooms"],
                "allergies": [],
                "target_protein_g": 140,
                "target_carbs_g": 200,
                "target_fat_g": 50,
                "target_calories": 1800
            }
        )
        print(f"✅ Created test profile for user {test_user.username}")
        
    finally:
        db.close()

