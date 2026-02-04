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
import json
import uuid as uuid_pkg
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import Column, String, JSON as JSONType
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from pydantic import field_serializer, BaseModel

class Publisher(BaseModel):
    name: Optional[str]
    url: Optional[str]
    mail: Optional[str]
    type: Optional[str]
    note: Optional[str]

class Temporal(BaseModel):
    startDate: Optional[str]
    endDate: Optional[str]

class TechnicalMetadata(BaseModel):
    datasetIdentifier: Optional[str]
    metadataUpdateDate: Optional[str]

class Distribution(BaseModel):
    title: Optional[str]
    accessURL: Optional[str]
    description: Optional[str]
    downloadURL: Optional[str]
    mediaType: Optional[str]
    format: Optional[str]
    byteSize: Optional[str]
    rights: Optional[str]
    license: Optional[str]
    documentation: Optional[str]

class DatasetMetadata(BaseModel):
    title: Optional[str]
    description: Optional[str]
    publisher: Optional[Publisher]
    contactPoint: Optional[str]
    theme: Optional[str]
    keyword: Optional[str]
    accessRights: Optional[str]
    license: Optional[str]
    conformsTo: Optional[str]
    language: Optional[str]
    spatial: Optional[str]
    temporal: Optional[Temporal]
    issued: Optional[str]
    modified: Optional[str]
    provenance: Optional[str]
    purpose: Optional[str]
    populationCoverage: Optional[str]
    updateFrequency: Optional[str]
    applicableLegislation: Optional[str]
    numberOfRecords: Optional[str]
    numberOfIndividuals: Optional[str]
    technicalMetadata: Optional[TechnicalMetadata]
    distribution: Optional[Distribution]


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










