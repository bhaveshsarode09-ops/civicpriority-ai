"""Social Media Mock Connector for CivicPriority AI.
Simulates authorized public civic grievance mentions (e.g. municipal hashtag / Twitter/X tagging).
NOTE: Marked as Synthetic demonstration data — not official government data.
"""

from typing import Any, Union
import json
from civicpriority.connectors.base import BaseConnector, ConnectorError
from civicpriority.models import ComplaintRecord, ComplaintSource, utc_now


class SocialMediaMockConnector(BaseConnector):
    """Parses social media grievance feeds from authorized municipal data pipelines."""

    DISCLAIMER = "Synthetic demonstration data — not official government data."

    def __init__(self):
        super().__init__(default_source=ComplaintSource.SOCIAL_MEDIA)

    def load(self, input_data: Union[list[dict[str, Any]], str]) -> list[ComplaintRecord]:
        if isinstance(input_data, str):
            try:
                posts = json.loads(input_data)
            except Exception as e:
                raise ConnectorError(f"Failed to parse JSON social media feed: {e}") from e
        elif isinstance(input_data, list):
            posts = input_data
        else:
            raise ConnectorError("SocialMediaMockConnector requires a list of dicts or JSON string.")

        records: list[ComplaintRecord] = []
        for post in posts:
            text = post.get("text") or post.get("caption") or post.get("post_body")
            if not text or len(str(text).strip()) < 5:
                continue

            raw_text = str(text).strip()
            masked_text = self.mask_contact_in_text(raw_text)

            # Anonymize username / handle into contact hash
            user_handle = post.get("handle") or post.get("username") or post.get("author_id")
            contact_hash = self.hash_contact(user_handle) if user_handle else None

            post_id = str(post.get("post_id") or post.get("id") or "")
            if post_id:
                rec_id = f"CMP-SOC-{post_id}"
            else:
                rec_id = self.generate_stable_id(self.default_source.value, masked_text[:60])

            locality = post.get("locality") or post.get("ward") or post.get("geo_tag") or "General Municipality"

            record = ComplaintRecord(
                id=rec_id,
                source=self.default_source,
                source_reference=f"social_post_{post_id}" if post_id else None,
                original_text=masked_text,
                original_language=post.get("language", "en"),
                submitted_at=self.parse_datetime(post.get("timestamp")),
                locality=str(locality),
                district=post.get("district"),
                citizen_contact_hash=contact_hash,
                consent_obtained=bool(post.get("consent_obtained", True)),
                metadata={
                    "platform": post.get("platform", "SocialMediaChannel"),
                    "synthetic_disclaimer": self.DISCLAIMER,
                    "engagement_likes": post.get("likes", 0),
                    "engagement_shares": post.get("shares", 0),
                },
            )
            records.append(record)

        return records
