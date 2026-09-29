"""Connectors package for CivicPriority AI."""

from civicpriority.connectors.base import BaseConnector, ConnectorError
from civicpriority.connectors.csv_connector import CSVConnector
from civicpriority.connectors.grievance_portal_mock import GrievancePortalMockConnector
from civicpriority.connectors.messaging_mock import MessagingMockConnector
from civicpriority.connectors.social_media_mock import SocialMediaMockConnector
from civicpriority.connectors.text_connector import TextFileConnector
from civicpriority.connectors.transcript_connector import TranscriptConnector

__all__ = [
    "BaseConnector",
    "ConnectorError",
    "CSVConnector",
    "TextFileConnector",
    "TranscriptConnector",
    "SocialMediaMockConnector",
    "GrievancePortalMockConnector",
    "MessagingMockConnector",
]
