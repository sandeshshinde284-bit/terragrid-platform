"""
Shared parsing for "Label:value" comma-separated recipient lists.

Used by both WhatsApp (WHATSAPP_RECIPIENTS) and email
(EMAIL_ALERT_RECIPIENTS) pre-approved demo recipient lists for Agency
Alerts - same format, same reason: a fixed, reviewed list an operator
picks from, rather than an open relay to arbitrary input typed on the
frontend.
"""
from typing import Dict, List


class LabeledRecipient:
    def __init__(self, label: str, value: str):
        self.label = label
        self.value = value

    def to_dict(self) -> Dict[str, str]:
        return {"label": self.label, "value": self.value}


def parse_labeled_recipients(raw: str) -> List[LabeledRecipient]:
    """
    Parses "Label:value,Label2:value2" into a list of LabeledRecipient.
    Silently skips malformed entries rather than crashing service startup
    over a typo in .env.
    """
    recipients: List[LabeledRecipient] = []
    if not raw:
        return recipients

    for entry in raw.split(","):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        label, value = entry.split(":", 1)
        label = label.strip()
        value = value.strip()
        if label and value:
            recipients.append(LabeledRecipient(label, value))

    return recipients
