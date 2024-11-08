from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, JSON, CheckConstraint, Index, func
from sqlalchemy.orm import DeclarativeBase

Base = DeclarativeBase()

class User(Base):
    __tablename__ = 'user'
    id = Column(Text, primary_key=True, nullable=False)
    createdAt = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updatedAt = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    email = Column(Text)
    isTemporary = Column(Boolean, nullable=False, default=True)
    isAnonymous = Column(Boolean, nullable=False, default=True)

class Application(Base):
    __tablename__ = 'applications'
    id = Column(Text, primary_key=True, nullable=False)
    userId = Column(Text, ForeignKey('user.id'), nullable=False)
    status = Column(Text, nullable=False)
    createdAt = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updatedAt = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    data = Column(JSON, nullable=False)
    name = Column(Text)
    naic = Column(Text)
    zip = Column(Text, nullable=False)
    county = Column(Text, nullable=False)
    dob = Column(Text, nullable=False)
    schema = Column(JSON, nullable=False)
    originalSchema = Column(JSON, nullable=False)
    underwritingType = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index('idx_applications_csg_key', "id"),
        CheckConstraint("underwritingType IN (0, 1, 2)", name="underwriting_type_check"),
    )

class CSGApplication(Base):
    __tablename__ = 'csg_applications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    applicationId = Column(Text, ForeignKey('applications.id'), nullable=False)
    key = Column(Text, nullable=False)
    responseBody = Column(Text, nullable=False)
    brokerEmail = Column(Text)
    createdAt = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updatedAt = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    __table_args__ = (
        Index('idx_csg_applications_application_id', 'applicationId'),
        Index('idx_csg_applications_key', 'key'),
    )

class Onboarding(Base):
    __tablename__ = 'onboarding'
    id = Column(Text, primary_key=True)
    userId = Column(Text, ForeignKey('user.id'), nullable=False)
    createdAt = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updatedAt = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    data = Column(JSON, nullable=False)

class CSGToken(Base):
    __tablename__ = 'csg_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(Text, nullable=False)
    expiresAt = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updatedAt = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    __table_args__ = (
        Index('idx_csg_tokens_token', 'token'),
        Index('idx_csg_tokens_expires_at', 'expiresAt'),
    )

class Broker(Base):
    __tablename__ = 'brokers'
    id = Column(Text, primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    passwordHash = Column(Text, nullable=False)
    createdAt = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updatedAt = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

