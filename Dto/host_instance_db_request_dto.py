from typing import Optional

from pydantic import BaseModel, Field


# 요청 데이터 모델
# class Instance(BaseModel):
#     target_id: str = Field(..., title="Target ID")
#     status: str
#     metric: str
#     instance_name: str
#     blocking_session: str | None = None
#
# class Tier(BaseModel):
#     name: str = Field(..., title="Tiers Name")
#     type: str = Field(..., title="Tiers Type")
#     instances: list[Instance] = Field(..., title="Instances List")
#
# class HostInstanceDBRequestData(BaseModel):
#     time: str = Field(..., title="Request Time")
#     anomaly: bool
#     tx_codes: dict
#     tiers: list[Tier]  # 단일 Tier만 포함
#     category_inst_type: str | None = Field(default=None, description="(Service), (Instance, HOST, DB) 구분 ")
#
# class HostInstanceDBRequestDTO(BaseModel):
#     inst_type: str | None = Field(default=None, description="Instance Type")
#     category_inst_type: str | None = Field(default=None, description="(Service), (Instance, HOST, DB) 구분 ")
#     success: bool
#     message: str | None
#     total: int
#     data: HostInstanceDBRequestData

class Instance(BaseModel):
    status: str
    metric: str
    normalityScore: float
    target_id: str = Field(..., title="Target ID")
    instance_name: str
    blocking_session: str | None = None

class Tier(BaseModel):
    name: str = Field(..., title="Tiers Name")
    type: str = Field(..., title="Tiers Type")
    instances: list[Instance] = Field(..., title="Instances List")

class AnomalyCount(BaseModel):
    os: int = Field(...)
    was: int = Field(...)
    tran: int = Field(...)
    db: int = Field(...)

class Summary(BaseModel):
    time: str = Field(..., title="Request Time")
    anomaly: bool
    tx_codes: dict
    anomalyCountMap: AnomalyCount
    tiers: list[Tier]  # 단일 Tier만 포함
    category_inst_type: str | None = Field(default=None, description="(Service), (Instance, HOST, DB) 구분 ")

class HostInstanceDBRequestDTO(BaseModel):
    summary: Summary
    nav: str | None = None
    category_inst_type: str | None = Field(default=None, description="(Service), (Instance, HOST, DB) 구분")

# class HostInstanceDBRequestDTO(BaseModel):
#     inst_type: str | None = Field(default=None, description="Instance Type")
#     category_inst_type: str | None = Field(default=None, description="(Service), (Instance, HOST, DB) 구분 ")
#     success: bool
#     message: str | None
#     total: int
#     data: HostInstanceDBRequestData