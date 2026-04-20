from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_vip = Column(Boolean, default=False)
    vip_expire_at = Column(DateTime, nullable=True) # 会员过期时间
    created_at = Column(DateTime, server_default=func.now())
    
    # 每日免费额度计数 (简单起见，可以每次下载检查)
    daily_download_count = Column(Integer, default=0)
    last_download_date = Column(String, nullable=True) # 记录日期 YYYY-MM-DD

class DownloadLog(Base):
    __tablename__ = "download_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_url = Column(String)
    platform = Column(String)
    created_at = Column(DateTime, server_default=func.now())
