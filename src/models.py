#from sqlmodel import SQLModel, Field
#from pydantic import BaseModel

#class NodeDatasetInfo(SQLModel, table=True):
#    id: int = Field(default=None, primary_key=True)
#    node: str
##    path: str
#    disease: str

#class RemoveDatasetObject(BaseModel):
#    node: str
##    disease: str
#    path: str

#class Schema(SQLModel, table=True):
#    id: int = Field(default=None, primary_key=True)
#    disease: str
#    schema: str

from sqlmodel import SQLModel, Field
from typing import Dict, List, Union, Optional
import json
import uuid as uuid_pkg
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, JSON as JSONType
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from typing import Dict, Any
from pydantic import field_serializer

class DatasetSchema(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    use_case: str # to change into use_case
    data: str  # JSON string

    def data_dict(self):
        return json.loads(self.data)

class NewDataset(SQLModel):
    use_case: str # to change into use_case
    data: Dict[str, Dict[str, List[Union[str, int, float, bool]]]]

class RemoveDatasetObject(SQLModel):
    node: str
    use_case: str # to change into use_case
    path: str

#class NodeDatasetInfo(SQLModel, table=True):
#    #id: int = Field(default=None, primary_key=True)
#    id: Optional[uuid_pkg.UUID] = Field(default_factory=uuid_pkg.uuid4,
#                                             primary_key=True)
#    node: str
#    path: str
#    use_case: str #to change into use_case

class NodeDatasetInfo(SQLModel, table=True, __tablename__="data_catalogue"):
    #id: str = Field(default=None, primary_key=True)
    #id: Optional[int] = Field(default=None, primary_key=True)
    id: Optional[uuid_pkg.UUID] = Field(default_factory=uuid_pkg.uuid4,
                                             primary_key=True)
    node: str
    path: str
    use_case: str # to change into use_case

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    @field_serializer("timestamp")
    def serialize_ts(self, ts: datetime):
        return ts.isoformat()
    
    num_records: Optional[int] = None
    num_features: Optional[int] = None
    
    schema: Optional[Dict[str, Any]] = Field(
        sa_column=Column(JSONB)
    )






