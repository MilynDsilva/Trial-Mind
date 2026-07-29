import json
import os
import urllib.request
from typing import Dict, Any, Optional
from src.models.trial import TrialProtocol, Criterion


class TrialFetcher:
    """Fetcher for ClinicalTrials.gov protocols or local JSON protocol files."""

    @staticmethod
    def load_from_file(file_path: str) -> TrialProtocol:
        """Loads a TrialProtocol from a local JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Trial file not found at path: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return TrialProtocol.model_validate(data)

    @staticmethod
    def fetch_from_clinicaltrials_gov(nct_id: str) -> TrialProtocol:
        """Fetches live trial protocol data from ClinicalTrials.gov REST API v2."""
        url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "TrialMind/0.1.0"})
        try:
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    raise ValueError(f"ClinicalTrials.gov returned HTTP status {response.status}")
                raw_data = json.loads(response.read().decode())
        except Exception as e:
            raise RuntimeError(f"Failed to fetch trial {nct_id} from ClinicalTrials.gov API: {e}")

        protocol_section = raw_data.get("protocolSection", {})
        identification = protocol_section.get("identificationModule", {})
        eligibility = protocol_section.get("eligibilityModule", {})
        design = protocol_section.get("designModule", {})

        title = identification.get("officialTitle") or identification.get("briefTitle") or f"Trial {nct_id}"
        conditions = protocol_section.get("conditionsModule", {}).get("conditions", ["Oncology"])
        primary_condition = conditions[0] if conditions else "Oncology"
        
        phases = design.get("phases", ["Phase 2"])
        phase_str = phases[0] if phases else "Phase 2"

        raw_criteria_text = eligibility.get("eligibilityCriteria", "")
        inclusion_criteria, exclusion_criteria = TrialFetcher._parse_criteria_text(raw_criteria_text)

        return TrialProtocol(
            nct_id=nct_id,
            title=title,
            phase=phase_str,
            target_condition=primary_condition,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
        )

    @staticmethod
    def _parse_criteria_text(text: str) -> tuple[list[Criterion], list[Criterion]]:
        """Parses raw ClinicalTrials.gov eligibility criteria text block into inclusion and exclusion Criterion lists."""
        inclusion = []
        exclusion = []
        current_section = "inclusion"

        lines = text.split("\n")
        inc_counter = 1
        exc_counter = 1

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            lower_line = cleaned.lower()
            if "inclusion criteria" in lower_line:
                current_section = "inclusion"
                continue
            elif "exclusion criteria" in lower_line:
                current_section = "exclusion"
                continue

            if cleaned.startswith("-") or cleaned.startswith("*") or (cleaned[0].isdigit() and cleaned[1:3] in [". ", ") "]):
                rule_text = cleaned.lstrip("-*0123456789. )").strip()
                if not rule_text:
                    continue

                if current_section == "inclusion":
                    inclusion.append(
                        Criterion(
                            id=f"INC-{inc_counter:02d}",
                            rule_type="INCLUSION",
                            description=rule_text,
                        )
                    )
                    inc_counter += 1
                else:
                    exclusion.append(
                        Criterion(
                            id=f"EXC-{exc_counter:02d}",
                            rule_type="EXCLUSION",
                            description=rule_text,
                        )
                    )
                    exc_counter += 1

        return inclusion, exclusion
