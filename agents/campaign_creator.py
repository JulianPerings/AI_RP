"""Campaign Creator agent — generates campaign YAML from a high-level prompt."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agents.base_agent import BaseAgent
from app.config import CAMPAIGNS_DIR
from models.campaign import Campaign
from services.llm_service import LLMService


class CampaignCreatorAgent(BaseAgent):
    """Generates a full campaign YAML file from a user description."""

    prompt_file = "campaign_creator.md"

    def __init__(self, llm: LLMService, **kwargs: Any) -> None:
        super().__init__(llm, **kwargs)

    def process(self, input_text: str, **kwargs: Any) -> str:
        """Generate campaign YAML from the user's description.

        Returns the raw YAML string.
        """
        raw = self._chat(
            user_message=input_text,
            temperature=0.9,
            max_tokens=4096,
        )

        # Strip markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        return cleaned

    def create_and_save(
        self,
        description: str,
        filename: str | None = None,
    ) -> Path:
        """Generate a campaign and save it to the campaigns directory.

        Returns the path to the saved YAML file.
        """
        yaml_str = self.process(description)

        # Validate by parsing
        data = yaml.safe_load(yaml_str)
        campaign = Campaign.model_validate(data)

        # Determine filename
        if not filename:
            slug = campaign.name.lower().replace(" ", "_")[:40]
            filename = f"{slug}.yaml"

        path = CAMPAIGNS_DIR / filename
        path.write_text(yaml_str, encoding="utf-8")
        return path
