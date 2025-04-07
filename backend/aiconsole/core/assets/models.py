from sqlalchemy import Column, String, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AssetModel(Base):
    __tablename__ = 'assets'

    id = Column(String, primary_key=True)
    name = Column(String)
    version = Column(String, default="0.0.1")
    usage = Column(String)
    usage_examples = Column(String)  # We'll store this as a JSON string
    defined_in = Column(String)  # We'll store AssetLocation as string
    type = Column(String)  # We'll store AssetType as string
    default_status = Column(String, default="ENABLED")  # We'll store AssetStatus as string
    status = Column(String, default="ENABLED")  # We'll store AssetStatus as string
    override = Column(Boolean, default=False)
    content_type = Column(String)  # We'll store MaterialContentType as string
    content = Column(String)
    system = Column(String, nullable=True)  # For AICAgent
    gpt_mode = Column(String, nullable=True)  # For AICAgent
    execution_mode = Column(String, nullable=True)  # For AICAgent 