from pydantic import Field, BaseModel
from typing import Optional, Union


class Anomaly(BaseModel):
    name: str = Field(..., title='Metric Name')
    target_id: str = Field(..., title="Target ID")
    tx_code_name: str = Field(..., title="Transaction Code Name")
    metric_desc: str
    value: float = Field(..., title='Value')
    lower: float = Field(..., description="Lower Value")
    upper: float = Field(..., description="Upper Value")
    failure: bool = Field(..., description="실패 여부")
    unit: str = Field(..., description="단위")

class Performance(BaseModel):
    lower: float = Field(..., description="하한값")
    upper: float = Field(..., description="상한값")
    elapse_avg: float = Field(..., description="평균 소요 시간")
    exec_count: float = Field(..., description="실행 횟수")

class TxCode(BaseModel):
    name: str = Field(..., description="트랜잭션 이름")
    performance: Performance = Field(..., description="성능 지표")
    anomaly: list[Anomaly] = Field(..., description="이상 세부 사항")

class ServiceDataDTO(BaseModel):
    time: str = Field(..., description="요청 시간")
    anomaly: bool = Field(..., description="이상 여부")
    tx_codes: dict[str, TxCode] = Field(..., description="트랜잭션 코드 데이터")
    tiers: list = Field(default_factory=list, description="티어 데이터")
    category_inst_type: str | None = Field(default=None, description="(Service), (Instance, HOST, DB) 구분 ")

class ServiceRequestDTO(BaseModel):
    inst_type: str | None = Field(default=None, description="Inst Type")
    category_inst_type: str | None = Field(default=None, description="(Service), (Instance, HOST, DB) 구분 ")
    success: bool = Field(..., description="성공 여부")
    message: Optional[str] = Field(None, description="메시지")
    total: int = Field(..., description="총 개수")
    data: ServiceDataDTO = Field(..., description="데이터")
