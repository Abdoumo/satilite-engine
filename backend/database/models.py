from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
import datetime
import enum

Base = declarative_base()

class AlertStatus(str, enum.Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    RESOLVED = "RESOLVED"

class Pipeline(Base):
    __tablename__ = 'pipelines'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    operator = Column(String)
    status = Column(String)
    geometry = Column(Geometry(geometry_type='MULTILINESTRING', srid=4326))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PipelineSegment(Base):
    __tablename__ = 'pipeline_segments'
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'))
    segment_name = Column(String)
    geometry = Column(Geometry(geometry_type='LINESTRING', srid=4326))
    risk_level = Column(String)
    monitoring_status = Column(String)
    pipeline = relationship("Pipeline")

class SatelliteAnomaly(Base):
    __tablename__ = 'satellite_anomalies'
    id = Column(Integer, primary_key=True)
    source = Column(String)
    product = Column(String)
    acquisition_time = Column(DateTime)
    anomaly_type = Column(String)
    severity = Column(String)
    confidence = Column(Float)
    geometry = Column(Geometry(geometry_type='POINT', srid=4326))
    latitude = Column(Float)
    longitude = Column(Float)
    pipeline_segment_id = Column(Integer, ForeignKey('pipeline_segments.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class InfrastructureNode(Base):
    __tablename__ = 'infrastructure_nodes'
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'))
    node_type = Column(String) # VALVE, PUMP
    geometry = Column(Geometry(geometry_type='POINT', srid=4326))

class VideoAsset(Base):
    __tablename__ = 'video_assets'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    asset_type = Column(String) # CAMERA, DRONE
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    stream_url = Column(String)
    status = Column(String)
    
class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    alert_type = Column(String)
    source = Column(String)
    severity = Column(String)
    status = Column(Enum(AlertStatus), default=AlertStatus.NEW)
    confidence = Column(Float)
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    pipeline_segment_id = Column(Integer, ForeignKey('pipeline_segments.id'), nullable=True)
    satellite_anomaly_id = Column(Integer, ForeignKey('satellite_anomalies.id'), nullable=True)
    video_asset_id = Column(Integer, ForeignKey('video_assets.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
