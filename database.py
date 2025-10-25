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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agentic_grocery.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Models
class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    recipes = relationship("SavedRecipe", back_populates="user")
    grocery_lists = relationship("GroceryList", back_populates="user")
    meal_history = relationship("MealHistory", back_populates="user")
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)


class UserProfile(Base):
    """User dietary profile and preferences"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Physical stats
    height_cm = Column(Float)
    weight_kg = Column(Float)
    age = Column(Integer)
    gender = Column(String)
    
    # Fitness goals
    goal = Column(String)  # cut, bulk, maintain
    workout_frequency = Column(String)
    activity_level = Column(String)  # sedentary, light, moderate, active, very_active
    
    # Dietary preferences
    diet = Column(String)  # vegetarian, vegan, omnivore, pescatarian, etc.
    allergies = Column(JSON)  # List of allergies
    likes = Column(JSON)  # Favorite foods/cuisines
    dislikes = Column(JSON)  # Foods to avoid
    
    # Target macros
    target_protein_g = Column(Float)
    target_carbs_g = Column(Float)
    target_fat_g = Column(Float)
    target_calories = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")


class SavedRecipe(Base):
    """User's saved recipes"""
    __tablename__ = "saved_recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    title = Column(String, nullable=False)
    description = Column(String)
    cook_time = Column(String)
    servings = Column(Integer)
    cuisine = Column(String)
    difficulty = Column(String)
    
    # Macros
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
    calories = Column(Float)
    fiber_g = Column(Float)
    
    # Recipe details
    ingredients = Column(JSON)  # List of {name, quantity}
    instructions = Column(JSON)  # List of steps
    image_url = Column(String)
    
    # Metadata
    is_favorite = Column(Boolean, default=False)
    times_cooked = Column(Integer, default=0)
    last_cooked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="recipes")


class GroceryList(Base):
    """User's grocery lists"""
    __tablename__ = "grocery_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("saved_recipes.id"), nullable=True)
    
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
    recipe_id = Column(Integer, ForeignKey("saved_recipes.id"), nullable=True)
    
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


def save_recipe(db: Session, user_id: int, recipe_data: dict) -> SavedRecipe:
    """Save a recipe for user"""
    recipe = SavedRecipe(user_id=user_id, **recipe_data)
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

