"""
Database Schemas for Zapgen (WhatsApp SaaS)

Each Pydantic model = one MongoDB collection (lowercased name).
Use these models for validation in API routes.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Contact(BaseModel):
    name: str = Field(..., description="Contact name")
    phone: str = Field(..., description="WhatsApp phone number in international format")
    tags: List[str] = Field(default_factory=list, description="Tags for segmentation")
    notes: Optional[str] = Field(None, description="Internal notes")


class Message(BaseModel):
    contact_id: str = Field(..., description="ID of the contact")
    direction: str = Field(..., pattern="^(inbound|outbound)$", description="Message direction")
    text: str = Field(..., description="Message text content")
    campaign_id: Optional[str] = Field(None, description="If part of a campaign")


class Campaign(BaseModel):
    name: str
    message: str
    status: str = Field("draft", description="draft | scheduled | sending | sent | failed")
    segment_tags: List[str] = Field(default_factory=list, description="Tags to filter contacts (OR)")


class Template(BaseModel):
    name: str
    language: str = Field("en", description="Language code")
    body: str
    variables: List[str] = Field(default_factory=list)


class Flow(BaseModel):
    name: str
    definition: Dict[str, Any] = Field(default_factory=dict, description="Flow JSON definition (nodes, edges)")
    description: Optional[str] = None


class ChatSession(BaseModel):
    contact_id: str
    last_message: Optional[str] = None

