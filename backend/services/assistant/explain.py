"""Plain-language rendering of stored predictions and SHAP factors.

The stored factors come from ml_service.explain_frame. Categorical features are
one-hot encoded, so a factor names one *category* of a feature and the lead's
actual *value*. When they differ, the factor is about the lead NOT having that
category (e.g. City category "Mumbai" with value "Select" means "not Mumbai").
Getting this wrong would invert the explanation, so it is handled explicitly.
"""
from __future__ import annotations

import math

FEATURE_LABELS = {
    "TotalVisits": "Website visits",
    "Total Time Spent on Website": "Time on the website",
    "Page Views Per Visit": "Pages viewed per visit",
    "Lead Origin": "Lead origin",
    "Lead Source": "Lead source",
    "Do Not Email": "Email opt-out",
    "Do Not Call": "Call opt-out",
    "Last Activity": "Last activity",
    "Last Notable Activity": "Last notable activity",
    "Country": "Country",
    "City": "City",
    "Specialization": "Specialization",
    "How did you hear about X Education": "How they heard about the institution",
    "What is your current occupation": "Current occupation",
    "What matters most to you in choosing a course": "What matters most in choosing a course",
    "A free copy of Mastering The Interview": "Requested the free interview guide",
    "Search": "Saw a search advertisement",
    "Newspaper Article": "Saw a newspaper article",
    "X Education Forums": "Saw the education forums",
    "Newspaper": "Saw a newspaper advertisement",
    "Digital Advertisement": "Saw a digital advertisement",
    "Through Recommendations": "Came through a recommendation",
}
UNSPECIFIED = {"", "select", "nan", "none", "null"}


def label(feature: str) -> str:
    return FEATURE_LABELS.get(feature, feature)


def is_unspecified(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip().lower() in UNSPECIFIED


def format_value(feature: str, value) -> str:
    if is_unspecified(value):
        return "not specified"
    if isinstance(value, (int, float)):
        number = float(value)
        if feature == "Total Time Spent on Website":
            seconds = int(round(number))
            return f"{seconds} seconds" if seconds < 60 else f"{seconds} seconds (about {seconds / 60:.0f} min)"
        if feature == "TotalVisits":
            return f"{int(round(number))}"
        return f"{number:.2f}".rstrip("0").rstrip(".")
    return f"“{value}”"


def describe(factor: dict) -> str:
    """One factor as a short phrase, without direction."""
    feature = factor.get("feature", "")
    name = label(feature)
    category = factor.get("category")
    value = factor.get("value")
    if category is None:  # numeric feature
        return f"{name}: {format_value(feature, value)}"
    if is_unspecified(category):
        if is_unspecified(value):
            return f"{name} not specified"
        return f"{name} is specified ({format_value(feature, value)})"
    if not is_unspecified(value) and str(category) == str(value):
        return f"{name} is “{category}”"
    actual = "not specified" if is_unspecified(value) else f"it is {format_value(feature, value)}"
    return f"{name} is not “{category}” ({actual})"


def strength(shap_value: float) -> str:
    size = abs(shap_value)
    if size >= 0.5:
        return "strongly"
    if size >= 0.2:
        return "moderately"
    return "slightly"


def factor_sentence(factor: dict) -> str:
    shap_value = float(factor.get("shap_value") or 0.0)
    verb = "raised" if shap_value > 0 else "lowered"
    return f"{describe(factor)} — {strength(shap_value)} {verb} the score"


def factor_card(factor: dict) -> dict:
    shap_value = float(factor.get("shap_value") or 0.0)
    return {"text": describe(factor), "impact": round(shap_value, 3),
            "direction": "up" if shap_value > 0 else "down", "strength": strength(shap_value)}


def _value_of(factors: list[dict], feature: str):
    for factor in factors:
        if factor.get("feature") == feature:
            return factor.get("value")
    return None


def follow_up_actions(band: str, positive: list[dict], negative: list[dict], lead: dict) -> list[str]:
    """Suggested next steps.

    These are rule-based suggestions derived from the stored score band and
    SHAP factors, not model outputs; the reply labels them that way.
    """
    actions: list[str] = []
    if band == "High":
        actions.append("Prioritise this lead: it is in the High band, so a counselling call soon is "
                       "likely to be the best use of time.")
    elif band == "Medium":
        actions.append("Send programme information that matches the lead's interest, then schedule "
                       "a counselling call.")
    else:
        actions.append("Keep this lead in a lower-priority nurture sequence (periodic updates) rather "
                       "than calling first, and re-check the score if their activity changes.")

    if str(lead.get("follow_up_status") or "").lower() == "pending":
        actions.append("Follow-up is still marked Pending in the lead record.")

    factors = positive + negative
    time_on_site = _value_of(factors, "Total Time Spent on Website")
    if any(f.get("feature") == "Total Time Spent on Website" for f in negative) \
            and isinstance(time_on_site, (int, float)) and time_on_site < 300:
        actions.append("Low time on the website is pulling the score down; share a direct link to the "
                       "relevant programme page to encourage engagement.")

    do_not_email = _value_of(factors, "Do Not Email")
    if isinstance(do_not_email, str) and do_not_email.strip().lower() == "yes":
        actions.append("The lead has opted out of email, so use another channel they have agreed to.")

    last_activity = " ".join(str(_value_of(factors, name) or "")
                             for name in ("Last Activity", "Last Notable Activity")).lower()
    if "bounced" in last_activity:
        actions.append("Their last email bounced; verify the email address before the next contact.")
    elif "unreachable" in last_activity:
        actions.append("They were recently unreachable; try a different time or contact channel.")
    elif "unsubscribed" in last_activity:
        actions.append("They unsubscribed from emails; respect that and use a channel they accept.")

    source = _value_of(factors, "Lead Source")
    if isinstance(source, str) and source.strip().lower() in ("reference", "welingak website"):
        actions.append(f"The lead came through “{source}”, a source that historically converts well; "
                       "a personal follow-up is worthwhile.")

    return actions[:4]
