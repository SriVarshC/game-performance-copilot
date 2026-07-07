from sqlalchemy import (
    Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id       = Column(Integer, primary_key=True, index=True)
    username      = Column(String, unique=True, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)

    systems = relationship("System", back_populates="user")


class System(Base):
    __tablename__ = "systems"

    system_id  = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    cpu        = Column(String)
    gpu        = Column(String)
    ram_gb     = Column(Integer)
    os         = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user      = relationship("User", back_populates="systems")
    telemetry = relationship("Telemetry", back_populates="system")
    predictions = relationship("Prediction", back_populates="system")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id            = Column(Integer, primary_key=True, index=True)
    system_id     = Column(Integer, ForeignKey("systems.system_id"), nullable=True)
    user_id       = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)
    timestamp     = Column(DateTime, default=datetime.datetime.utcnow)
    fps           = Column(Float, nullable=True)
    cpu_usage     = Column(Float, nullable=True)
    gpu_usage     = Column(Float, nullable=True)
    vram_used_gb  = Column(Float, nullable=True)
    gpu_temp      = Column(Float, nullable=True)
    ram_usage     = Column(Float, nullable=True)
    gpu_clock_mhz = Column(Float, nullable=True)
    gpu_power_w   = Column(Float, nullable=True)

    system = relationship("System", back_populates="telemetry")


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id    = Column(Integer, primary_key=True, index=True)
    system_id        = Column(Integer, ForeignKey("systems.system_id"), nullable=True)
    user_id          = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)
    game_genre       = Column(String, nullable=True)
    resolution       = Column(String, nullable=True)
    preset           = Column(String, nullable=True)
    ray_tracing      = Column(Boolean, nullable=True)
    upscaling        = Column(String, nullable=True)
    predicted_fps    = Column(Float, nullable=True)
    low_1pct_fps     = Column(Float, nullable=True)
    health_score     = Column(Float, nullable=True)
    bottleneck_class = Column(String, nullable=True)
    confidence       = Column(Float, nullable=True)
    created_at       = Column(DateTime, default=datetime.datetime.utcnow)

    system          = relationship("System", back_populates="predictions")
    recommendations = relationship("Recommendation", back_populates="prediction")


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id  = Column(Integer, primary_key=True, index=True)
    prediction_id      = Column(Integer, ForeignKey("predictions.prediction_id"), nullable=True)
    user_id            = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)
    message            = Column(String, nullable=True)
    severity           = Column(String, nullable=True)
    category           = Column(String, nullable=True)
    estimated_fps_gain = Column(Float, nullable=True)
    was_helpful        = Column(Boolean, nullable=True)
    created_at         = Column(DateTime, default=datetime.datetime.utcnow)

    prediction = relationship("Prediction", back_populates="recommendations")