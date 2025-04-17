from sqlalchemy import Column, Integer, String, Text
from llm_api.Models.database import Base

class XaiopsMetaMetric(Base):
    __tablename__ = 'xaiops_meta_metric'

    meta_metric_id = Column(Integer, primary_key=True)
    target_type = Column(String(255), nullable=False)
    inst_product_type = Column(Text, nullable=True)
    metric_id = Column(String(255), nullable=False)
    metric_desc = Column(String(100), nullable=False)
    metric_unit = Column(String(20), nullable=False)
    metric_explain = Column(Text, nullable=True)
    property = Column(String, nullable=False)
