SENSITIVE_KEYWORDS = [
    "harassment",
    "sexual harassment",
    "discrimination",
    "bullying",
    "threat",
    "abuse",
    "termination",
    "resignation",
    "salary dispute",
    "pay dispute",
    "grievance",
    "complaint",
    "legal action",
    "misconduct",
    "workplace safety",
    "confidential",
]


def check_escalation(question):
    """
    Identify employee queries that may require direct HR attention.
    Returns (should_escalate, reason).
    """

    question_lower = question.lower()

    matched_keywords = [
        keyword
        for keyword in SENSITIVE_KEYWORDS
        if keyword in question_lower
    ]

    if matched_keywords:
        reason = (
            "Sensitive topic detected: "
            + ", ".join(matched_keywords)
        )
        return True, reason

    return False, None