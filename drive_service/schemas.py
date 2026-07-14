from pydantic import BaseModel
from datetime import datetime

class DriveFile(BaseModel):
    id:str
    name:str
    modified_time:datetime
    mime_type:str


class DriveFileListResponse(BaseModel):
    files:list[DriveFile]
    count:int

class DriveFileDownloadResponse(BaseModel):
    id:str
    name:str
    mime_type:str
    content_base64:str