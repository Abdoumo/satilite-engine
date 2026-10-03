import sys
import os

# Add backend to path so we can import from database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.session import SessionLocal
from database.models import Pipeline, PipelineSegment
from geoalchemy2.elements import WKTElement

def seed_database():
    db = SessionLocal()
    
    # Check if we already seeded
    if db.query(Pipeline).first():
        print("Database already seeded.")
        return
        
    print("Seeding Algerian Pipeline...")
    
    # Create the main Pipeline
    # Example LineString crossing near Annaba
    pipeline_wkt = "MULTILINESTRING((7.76 36.85, 7.765 36.90, 7.77 36.92))"
    
    p = Pipeline(
        name="Annaba Coastal Gas Line",
        operator="Sonatrach",
        status="ACTIVE",
        geometry=WKTElement(pipeline_wkt, srid=4326)
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    
    # Create Segments
    seg1_wkt = "LINESTRING(7.76 36.85, 7.765 36.90)"
    s1 = PipelineSegment(
        pipeline_id=p.id,
        segment_name="P-101",
        risk_level="MEDIUM",
        monitoring_status="ACTIVE",
        geometry=WKTElement(seg1_wkt, srid=4326)
    )
    
    seg2_wkt = "LINESTRING(7.765 36.90, 7.77 36.92)"
    s2 = PipelineSegment(
        pipeline_id=p.id,
        segment_name="P-102",
        risk_level="HIGH",
        monitoring_status="ACTIVE",
        geometry=WKTElement(seg2_wkt, srid=4326)
    )
    
    db.add_all([s1, s2])
    db.commit()
    
    print("Seeding complete! Added Pipeline and 2 Segments.")

if __name__ == "__main__":
    seed_database()
