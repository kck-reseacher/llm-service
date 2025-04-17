from sqlalchemy import Column, TIMESTAMP, String, Float, Integer

from llm_api.Models.database import Base


class DbslnResultAnomalyModel(Base):
    __tablename__ = 'dbsln_result_anomaly'

    time = Column(TIMESTAMP, primary_key=True)
    inst_type = Column(String(300), primary_key=True)
    target_id = Column(String(300), primary_key=True)
    metric = Column(String(100), primary_key=True)
    real_value = Column(Float, nullable=True)
    dbsln_lower = Column(Float, nullable=False)
    dbsln_upper = Column(Float, nullable=False)
    dbsln_grade = Column(Integer, nullable=False)