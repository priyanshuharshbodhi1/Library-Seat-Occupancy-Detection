"""
Database service for seat occupancy management
"""
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from api.models.database import Seat, OccupancyHistory, OccupancyStats, SessionLocal


class DatabaseService:
    """
    Service for managing seat occupancy database operations
    """

    def __init__(self):
        self.db: Optional[Session] = None

    def get_session(self) -> Session:
        """Get database session"""
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def close(self):
        """Close database session"""
        if self.db:
            self.db.close()
            self.db = None

    # ===== Seat Operations =====

    def upsert_seat(self, seat_data: Dict) -> Seat:
        """
        Insert or update seat data

        Args:
            seat_data: Dictionary with seat information
                - seat_number: str
                - status: str (available/occupied)
                - person_id: int (optional)
                - bbox: list[float] (optional)
                - duration: int (optional)
                - duration_exceeded: bool (optional)
        """
        db = self.get_session()

        seat_number = seat_data.get('seat_number') or seat_data.get('id')

        # Try to find existing seat
        seat = db.query(Seat).filter(Seat.seat_number == str(seat_number)).first()

        if seat:
            # Update existing seat
            old_status = seat.status
            seat.status = seat_data.get('status', seat.status)
            seat.person_id = seat_data.get('person_id', seat.person_id)
            seat.duration = seat_data.get('duration', seat.duration)
            seat.duration_exceeded = seat_data.get('duration_exceeded', seat.duration_exceeded)

            # Update bbox if provided
            if 'bbox' in seat_data and seat_data['bbox']:
                bbox = seat_data['bbox']
                seat.bbox_x1 = bbox[0]
                seat.bbox_y1 = bbox[1]
                seat.bbox_x2 = bbox[2]
                seat.bbox_y2 = bbox[3]

            # Update occupied_since
            if seat.status == 'occupied' and old_status == 'available':
                seat.occupied_since = datetime.utcnow()
            elif seat.status == 'available':
                seat.occupied_since = None

            seat.last_updated = datetime.utcnow()

            # Log status change
            if old_status != seat.status:
                self._log_occupancy_event(
                    seat_number=seat_number,
                    person_id=seat.person_id,
                    event_type='occupied' if seat.status == 'occupied' else 'freed',
                    duration=seat.duration if seat.status == 'available' else None
                )

        else:
            # Create new seat
            bbox = seat_data.get('bbox', [None, None, None, None])
            seat = Seat(
                seat_number=str(seat_number),
                status=seat_data.get('status', 'available'),
                person_id=seat_data.get('person_id'),
                duration=seat_data.get('duration', 0),
                duration_exceeded=seat_data.get('duration_exceeded', False),
                bbox_x1=bbox[0] if bbox else None,
                bbox_y1=bbox[1] if bbox else None,
                bbox_x2=bbox[2] if bbox else None,
                bbox_y2=bbox[3] if bbox else None,
                occupied_since=datetime.utcnow() if seat_data.get('status') == 'occupied' else None
            )
            db.add(seat)

        db.commit()
        db.refresh(seat)
        return seat

    def get_seat(self, seat_number: str) -> Optional[Seat]:
        """Get seat by number"""
        db = self.get_session()
        return db.query(Seat).filter(Seat.seat_number == str(seat_number)).first()

    def get_all_seats(self) -> List[Seat]:
        """Get all seats"""
        db = self.get_session()
        return db.query(Seat).order_by(Seat.seat_number).all()

    def delete_seat(self, seat_number: str) -> bool:
        """Delete seat"""
        db = self.get_session()
        seat = db.query(Seat).filter(Seat.seat_number == str(seat_number)).first()
        if seat:
            db.delete(seat)
            db.commit()
            return True
        return False

    def clear_all_seats(self):
        """Clear all seats (for reset)"""
        db = self.get_session()
        db.query(Seat).delete()
        db.commit()

    # ===== Occupancy History Operations =====

    def _log_occupancy_event(
        self,
        seat_number: str,
        person_id: Optional[int],
        event_type: str,
        duration: Optional[int] = None,
        notes: Optional[str] = None
    ) -> OccupancyHistory:
        """
        Log occupancy event to history

        Args:
            seat_number: Seat identifier
            person_id: Person ID (if applicable)
            event_type: Type of event (occupied, freed, duration_exceeded)
            duration: Duration in seconds (for freed events)
            notes: Additional notes
        """
        db = self.get_session()

        event = OccupancyHistory(
            seat_number=str(seat_number),
            person_id=person_id,
            event_type=event_type,
            duration=duration,
            notes=notes,
            timestamp=datetime.utcnow()
        )

        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_seat_history(
        self,
        seat_number: Optional[str] = None,
        limit: int = 100
    ) -> List[OccupancyHistory]:
        """
        Get occupancy history

        Args:
            seat_number: Filter by seat number (optional)
            limit: Max number of records to return
        """
        db = self.get_session()
        query = db.query(OccupancyHistory).order_by(OccupancyHistory.timestamp.desc())

        if seat_number:
            query = query.filter(OccupancyHistory.seat_number == str(seat_number))

        return query.limit(limit).all()

    # ===== Statistics Operations =====

    def save_stats(self, stats_data: Dict) -> OccupancyStats:
        """
        Save occupancy statistics snapshot

        Args:
            stats_data: Dictionary with stats
                - total_seats: int
                - occupied_seats: int
                - available_seats: int
                - person_count: int
        """
        db = self.get_session()

        stats = OccupancyStats(
            total_seats=stats_data.get('total_seats', 0),
            occupied_seats=stats_data.get('occupied_seats', 0),
            available_seats=stats_data.get('available_seats', 0),
            person_count=stats_data.get('person_count', 0),
            timestamp=datetime.utcnow()
        )

        db.add(stats)
        db.commit()
        db.refresh(stats)
        return stats

    def get_latest_stats(self) -> Optional[OccupancyStats]:
        """Get latest occupancy statistics"""
        db = self.get_session()
        return db.query(OccupancyStats).order_by(OccupancyStats.timestamp.desc()).first()

    def get_stats_history(self, limit: int = 100) -> List[OccupancyStats]:
        """Get statistics history"""
        db = self.get_session()
        return db.query(OccupancyStats).order_by(OccupancyStats.timestamp.desc()).limit(limit).all()

    # ===== Bulk Operations =====

    def update_all_seats(self, seats_data: List[Dict]):
        """
        Update all seats at once (for frame processing)

        Args:
            seats_data: List of seat dictionaries
        """
        for seat_data in seats_data:
            self.upsert_seat(seat_data)

    def get_current_occupancy(self) -> Dict:
        """
        Get current occupancy summary

        Returns:
            Dictionary with occupancy info:
                - total_seats: int
                - occupied_seats: int
                - available_seats: int
                - seats: List[Dict]
        """
        seats = self.get_all_seats()

        occupied = sum(1 for s in seats if s.status == 'occupied')
        available = sum(1 for s in seats if s.status == 'available')

        return {
            'total_seats': len(seats),
            'occupied_seats': occupied,
            'available_seats': available,
            'seats': [seat.to_dict() for seat in seats]
        }


# Global instance
_db_service = None


def get_database_service() -> DatabaseService:
    """Get global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
