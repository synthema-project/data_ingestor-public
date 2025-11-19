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
from typing import Dict, List, Union
import json
import uuid as uuid_pkg
from typing import Optional

class DatasetSchema(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    disease: str # to change into use_case
    data: str  # JSON string

    def data_dict(self):
        return json.loads(self.data)

class NewDataset(SQLModel):
    disease: str # to change into use_case
    data: Dict[str, Dict[str, List[Union[str, int, float, bool]]]]

class RemoveDatasetObject(SQLModel):
    node: str
    disease: str # to change into use_case
    path: str

class NodeDatasetInfo(SQLModel, table=True):
    #id: int = Field(default=None, primary_key=True)
    id: Optional[uuid_pkg.UUID] = Field(default_factory=uuid_pkg.uuid4,
                                             primary_key=True)
    node: str
    path: str
    disease: str

