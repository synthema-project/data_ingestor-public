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

class DatasetSchema(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    disease: str
    data: str  # JSON string

    def data_dict(self):
        return json.loads(self.data)

class NewDataset(SQLModel):
    disease: str
    data: Dict[str, Dict[str, List[Union[str, int, float, bool]]]]

class RemoveDatasetObject(SQLModel):
    node: str
    disease: str
    path: str

class NodeDatasetInfo(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    node: str
    path: str
    disease: str