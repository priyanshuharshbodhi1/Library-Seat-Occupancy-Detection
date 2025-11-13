"""
Database models for seat occupancy tracking
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Create database directory
db_dir = Path(__file__).parent.parent.parent / "data"
db_dir.mkdir(exist_ok=True)

# Database URL
DATABASE_URL = f"sqlite:///{db_dir}/occupancy.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Seat(Base):
    """
    Seat model - represents a physical seat/chair in the library
    """
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    seat_number = Column(String, unique=True, nullable=False, index=True)

    # Current status
    status = Column(String, default="available")  # available, occupied

    # Person tracking
    person_id = Column(Integer, nullable=True)

    # Timing
    occupied_since = Column(DateTime, nullable=True)
    duration = Column(Integer, default=0)  # Duration in seconds
    duration_exceeded = Column(Boolean, default=False)

    # Location (bounding box)
    bbox_x1 = Column(Float, nullable=True)
    bbox_y1 = Column(Float, nullable=True)
    bbox_x2 = Column(Float, nullable=True)
    bbox_y2 = Column(Float, nullable=True)

    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.seat_number,
            "status": self.status,
            "person_id": self.person_id,
            "occupied_since": self.occupied_since.isoformat() if self.occupied_since else None,
            "duration": self.duration,
            "duration_exceeded": self.duration_exceeded,
            "bbox": [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2] if self.bbox_x1 else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


class OccupancyHistory(Base):
    """
    Occupancy history - tracks all occupancy events
    """
    __tablename__ = "occupancy_history"

    id = Column(Integer, primary_key=True, index=True)
    seat_number = Column(String, index=True)
    person_id = Column(Integer, nullable=True)

    # Event details
    event_type = Column(String)  # occupied, freed, duration_exceeded

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    duration = Column(Integer, nullable=True)  # Duration when freed

    # Metadata
    notes = Column(Text, nullable=True)

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "seat_number": self.seat_number,
            "person_id": self.person_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "notes": self.notes
        }


class OccupancyStats(Base):
    """
    Aggregated occupancy statistics
    """
    __tablename__ = "occupancy_stats"

    id = Column(Integer, primary_key=True, index=True)

    # Counts
    total_seats = Column(Integer, default=0)
    occupied_seats = Column(Integer, default=0)
    available_seats = Column(Integer, default=0)
    person_count = Column(Integer, default=0)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "total_seats": self.total_seats,
            "occupied_seats": self.occupied_seats,
            "available_seats": self.available_seats,
            "person_count": self.person_count,
            "timestamp": self.timestamp.isoformat()
        }


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    """
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at {DATABASE_URL}")


def reset_db():
    """
    Reset database - drop and recreate all tables
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset complete")


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
