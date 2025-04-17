from sqlalchemy import Column, TIMESTAMP, String, Float, Text, PrimaryKeyConstraint

from llm_api.Models.database import Base


class AiResultGdnPerformance(Base):
    __tablename__ = 'ai_result_gdn_performance'

    time = Column(TIMESTAMP, primary_key=True)
    target_id = Column(String(300), primary_key=True)
    inst_type = Column(String, primary_key=True)
    real_value = Column(Float, nullable=True)
    metric = Column(String, primary_key=True)
    attention_map = Column(Text, nullable=True)
    model_value = Column(Float, nullable=True)
    anomaly_contribution = Column(Float, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('time', 'target_id', 'inst_type', 'metric', name='ai_result_gdn_performance_pk'),
    )

    def __repr__(self):
        return (f"<AiResultGdnPerformance(time={self.time}, "
                f"target_id='{self.target_id}', inst_type='{self.inst_type}', "
                f"metric='{self.metric}', real_value={self.real_value}, "
                f"model_value={self.model_value}, anomaly_contribution={self.anomaly_contribution})>")
