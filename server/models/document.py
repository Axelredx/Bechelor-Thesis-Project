from mongoengine import Document, StringField, BinaryField, DateTimeField, FloatField, IntField
from datetime import datetime, timezone

class DocumentModel(Document):
    # required document fields
    filename = StringField(required=True, max_length=255)
    file_extension = StringField(required=True, max_length=10)
    binary_file_content = BinaryField(required=True)  
    file_size = IntField(required=True)
    # to prevent duplicate uploads
    file_hash = StringField(required=True, unique=True)
    mime_type = StringField(required=True)
    file_category = StringField(required=True)
    upload_date = StringField(required=True) 

    # other optional document fields
    sender = StringField()
    receiver = StringField()
    subject = StringField()
    total_cost = FloatField()
    document_date = StringField()
    
    meta = {
        # collection name in MongoDB
        'collection': 'documents',  
        # internal indexing based on...
        'indexes': ['filename', 'upload_date', 'file_hash']
    }
    