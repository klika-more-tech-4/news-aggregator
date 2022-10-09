from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel, Field

from master.aggregation_master import UserRole, NewsFilterType


class InputDTO(BaseModel):
    date_at: datetime = Field(default=datetime.now() - timedelta(days=7))
    user_role: UserRole = Field(default=UserRole.entrepreneur)
    filter_type: NewsFilterType = Field(default=NewsFilterType.my_and_contractor_okveds)
    okveds: List[str] = Field(default=[])
