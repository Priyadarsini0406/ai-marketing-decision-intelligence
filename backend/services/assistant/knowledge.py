"""Curated knowledge for the Admission Assistant.

Every answer here describes something Decision-Intel actually does, as
implemented in this repository. Values that can change (model metrics, score
bands, the conversion threshold, the programme catalogue) are read at answer
time instead of being written into the text. Information the system does not
hold (fees, eligibility rules, deadlines, seats, scholarships) is answered with
an explicit "not available" reply rather than a guess.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
PROGRAM_CATALOG = ROOT / "frontend" / "src" / "lib" / "additional-programs.json"

MANAGER_ROLES = ("admission_manager", "marketing_manager")
STAFF_ROLES = ("admission_manager", "marketing_manager", "admin")
ALL_ROLES = ("student", "admission_manager", "marketing_manager", "admin")

CONVERSION_NOTICE = (
    "Lead scores estimate whether an enquiry is likely to convert, based on past "
    "marketing data. They do not measure academic eligibility or merit, and they "
    "are not admission decisions."
)

# Statuses an admission or marketing manager can set on a student enquiry
# (backend/api/workspace.py, StudentEnquiryUpdate).
ENQUIRY_STATUSES = {
    "Submitted": "your enquiry has been received and is waiting for the admission team.",
    "Under Review": "the admission team is reviewing your enquiry.",
    "Counselling": "your enquiry has reached the counselling stage.",
    "Application": "your enquiry has moved to the application stage.",
    "Admitted": "the admission team has marked this enquiry as admitted.",
    "Not Converted": "the admission team has closed this enquiry without an admission.",
}


@dataclass
class Context:
    """What an answer function may read. Built per request by the engine."""
    role: str
    db: object
    metadata: dict
    configuration: dict


@dataclass
class Topic:
    id: str
    title: str
    patterns: list[str]
    answer: Callable[[Context], str]
    roles: tuple[str, ...] = ALL_ROLES
    links: dict[str, list[tuple[str, str]]] = field(default_factory=dict)  # role -> [(label, href)]
    notice: bool = False  # attach the conversion-vs-eligibility notice

    def links_for(self, role: str) -> list[dict]:
        group = "manager" if role in MANAGER_ROLES else role
        return [{"label": label, "href": href} for label, href in self.links.get(group, [])]


def _pct(value: float | None) -> str:
    return "not recorded" if value is None else f"{value * 100:.1f}%"


def load_programs() -> list[dict]:
    try:
        data = json.loads(PROGRAM_CATALOG.read_text(encoding="utf-8"))
        return [item for item in data if item.get("program")]
    except (OSError, ValueError):
        return []


# ---------------------------------------------------------------- answers
def a_about(ctx: Context) -> str:
    return ("Decision-Intel is an admission marketing decision-support platform. It scores "
            "prospective-student enquiries (leads) by how likely they are to convert, explains "
            "each score with SHAP, groups leads into engagement segments, summarises marketing "
            "channels and helps plan budgets. Students use it to submit and track enquiries.\n\n"
            "Staff always make the final decisions; the platform only supports them.")


def a_conversion_vs_eligibility(ctx: Context) -> str:
    text = ("The lead score is a marketing estimate: the probability that an enquiry turns into "
            "a converted lead, learned from past enquiry and website-activity data. It does not "
            "check marks, qualifications or entrance criteria, and it never decides who is "
            "admitted.")
    if ctx.role == "student":
        text += ("\n\nDecision-Intel does not predict your chance of admission. For eligibility "
                 "questions, submit an enquiry and the admission team will reply.")
    return text


def a_model(ctx: Context) -> str:
    m = ctx.metadata.get("held_out_metrics") or {}
    features = ctx.metadata.get("approved_features") or []
    rows = ctx.metadata.get("rows")
    text = ("Lead scores come from an XGBoost classifier trained on the Leads X Education "
            f"dataset ({rows:,} historical enquiries). " if rows else
            "Lead scores come from an XGBoost classifier trained on historical enquiries. ")
    if features:
        text += (f"It uses {len(features)} inputs that are known when an enquiry arrives, such as "
                 "lead source, lead origin, website visits, time on the website and last activity. "
                 "Columns that the sales team fills in after contacting a lead are excluded, "
                 "because they would leak the outcome.")
    if m:
        text += (f"\n\nOn a held-out test set it reached ROC-AUC {m.get('roc_auc', 0):.3f}, "
                 f"accuracy {_pct(m.get('accuracy'))} and F1 {m.get('f1', 0):.3f}.")
    return text


def a_score_bands(ctx: Context) -> str:
    bands = ctx.metadata.get("score_bands") or {"high_min": 0.7, "medium_min": 0.4}
    threshold = ctx.configuration.get("conversion_threshold", 0.5)
    return (f"Each lead gets a conversion probability and a band: High from "
            f"{bands['high_min'] * 100:.0f}%, Medium from {bands['medium_min'] * 100:.0f}%, and Low "
            f"below that.\n\nSeparately, the administrator's conversion threshold is currently "
            f"{threshold * 100:.0f}%; dashboards count a lead as high-probability at or above it.")


def a_shap(ctx: Context) -> str:
    return ("SHAP shows how much each input pushed one lead's score up or down compared with the "
            "average lead. Positive factors raised the score; negative factors lowered it.\n\n"
            "SHAP describes what the model learned from past data. It does not prove that a "
            "factor causes a student to enrol, so treat it as context for a conversation, not "
            "as a rule.")


def a_segments(ctx: Context) -> str:
    return ("Leads are grouped into four segments with K-Means clustering on website engagement "
            "(visits, time on the website and pages per visit, log-scaled): Low Engagement, "
            "Casual Browsers, Engaged Prospects and High Intent, in order of engagement.\n\n"
            "Segments describe behaviour. They are not predictions, and a low-engagement lead "
            "can still convert well, for example when it comes through a referral.")


def a_budget(ctx: Context) -> str:
    return ("The budget planner splits a campaign budget across channels in four ways: equal, "
            "efficiency-weighted, custom, or optimised. The optimised mode solves a linear "
            "program that maximises projected conversions, with a cap on any single channel's "
            "share.\n\nProjections assume each channel keeps its historical conversions per unit "
            "of spend, so they are planning estimates, not forecasts.")


def a_channels(ctx: Context) -> str:
    return ("Channel analytics summarise leads, conversions, spend and cost per conversion for "
            "each marketing channel, using the lead records stored in Decision-Intel.")


def a_threshold(ctx: Context) -> str:
    threshold = ctx.configuration.get("conversion_threshold", 0.5)
    return (f"The conversion threshold is currently {threshold * 100:.0f}%. Leads at or above it "
            "count as high-probability on the dashboards. An administrator can change it under "
            "Platform Settings; lowering it finds more likely students but adds more calls that "
            "do not convert.")


def a_programs(ctx: Context) -> str:
    programs = load_programs()
    if not programs:
        return ("The programme catalogue is not available right now. Please submit an enquiry "
                "and the admission team will share the current programme list.")
    lines = "\n".join(f"- {p['program']}" for p in programs)
    return (f"These programmes are listed in the Decision-Intel catalogue:\n{lines}\n\n"
            "Intakes, seats and fees are not stored here; the admission team confirms them when "
            "you enquire.")


def a_not_available(ctx: Context) -> str:
    text = ("Decision-Intel does not store fees, eligibility rules, entrance requirements, "
            "deadlines, seat availability, scholarships or hostel details, so I can't answer that "
            "without guessing.")
    if ctx.role == "student":
        text += ("\n\nThe quickest way to get an accurate answer is to submit an enquiry with your "
                 "question in the remarks; the admission team replies through your enquiry.")
    else:
        text += "\n\nPlease refer to the institution's official admission documents."
    return text


def a_submit_enquiry(ctx: Context) -> str:
    return ("To submit an enquiry, open New Enquiry, choose the course you are interested in and "
            "fill in your preferred intake, study mode, qualification and contact preference. "
            "Add any questions in the remarks. You can track it afterwards under Enquiry Status.")


def a_enquiry_statuses(ctx: Context) -> str:
    lines = "\n".join(f"- {name}: {meaning}" for name, meaning in ENQUIRY_STATUSES.items())
    return ("An enquiry moves through these statuses, which the admission team updates:\n" + lines)


def a_profile(ctx: Context) -> str:
    return ("You can update your name, contact details, address and academic details on the My "
            "Profile page. Keeping your mobile number and qualification current helps the "
            "admission team respond.")


def a_privacy(ctx: Context) -> str:
    return ("Decision-Intel stores your account, profile and enquiry details so the admission "
            "team can respond. Passwords are stored as salted hashes, and pages are only "
            "available after sign-in according to your role. Assistant conversations are saved "
            "to your account so you can see your history, and you can clear them at any time.")


def a_datasets(ctx: Context) -> str:
    return ("Lead data is uploaded as a CSV file, or a ZIP containing exactly one CSV, of at most "
            "5 MB. The schema is checked before any record is stored. Administrators manage "
            "datasets under Datasets and Data Import.")


def a_roles(ctx: Context) -> str:
    return ("Decision-Intel has four roles. Students submit and track enquiries. Admission and "
            "marketing managers work with leads, predictions, explanations, segments, channel "
            "analytics and budgets. Administrators manage users, programmes, datasets and "
            "platform settings.")


def a_how_to_use_assistant(ctx: Context) -> str:
    if ctx.role in MANAGER_ROLES:
        return ("I can explain any lead's score and its SHAP factors, suggest follow-up actions, "
                "summarise how many leads are in each score band, and answer questions about "
                "Decision-Intel. Paste a lead's ID or Prospect ID, for example \"Explain lead "
                "<ID>\", or open a lead and ask \"Why did this lead get its score?\".")
    if ctx.role == "admin":
        return ("I can summarise the stored predictions, explain how the model, segments, "
                "threshold and budget planner work, and point you to the right admin pages.")
    return ("I can show the status of your enquiries, explain what each status means, list the "
            "programmes in the catalogue, and help you submit an enquiry. I can't predict "
            "admission outcomes.")


STUDENT_LINKS = {"student": [("New Enquiry", "/student/enquiries/new"),
                             ("Enquiry Status", "/student/enquiries/status")]}

TOPICS: list[Topic] = [
    Topic("about", "What is Decision-Intel?",
          ["what is decision intel", "what does this system do", "what is this platform",
           "tell me about decision-intel", "what is this website for", "what can this app do",
           "what is this site", "what is this portal", "purpose of this application"],
          a_about),
    Topic("assistant_help", "What can the assistant do?",
          ["what can you do", "how can you help me", "help", "what questions can i ask",
           "how do i use the assistant", "what can the chatbot do"],
          a_how_to_use_assistant),
    Topic("conversion_vs_eligibility", "Lead score vs admission eligibility",
          ["is the lead score my admission chance", "will i get admission", "am i eligible",
           "what is my chance of admission", "does the score mean the student is eligible",
           "does the model decide admission", "predict my admission", "will i be selected",
           "is conversion probability the same as admission probability"],
          a_conversion_vs_eligibility, notice=True,
          links={"student": [("New Enquiry", "/student/enquiries/new")]}),
    Topic("model", "How are lead scores predicted?",
          ["how does the prediction model work", "which model is used", "how accurate is the model",
           "what is the model accuracy", "how is the lead score calculated", "what features does the model use",
           "what is roc auc of the model", "how reliable are the predictions", "xgboost model details",
           "what data is the model trained on",
           "what features are used for prediction", "which inputs does the model use", "model inputs"],
          a_model, roles=STAFF_ROLES, notice=True,
          links={"manager": [("Admission Prediction", "/admission-prediction")]}),
    Topic("score_bands", "What do High, Medium and Low mean?",
          ["what does high medium low score mean", "what are the score bands", "what is a high score lead",
           "lead score band meaning", "what probability counts as high"],
          a_score_bands, roles=STAFF_ROLES),
    Topic("shap", "What is SHAP?",
          ["what is shap", "how do explanations work", "what are positive and negative factors",
           "what does a shap value mean", "explainable ai", "how do i read the explanation"],
          a_shap, roles=STAFF_ROLES,
          links={"manager": [("Explainable AI", "/explainable-ai")]}),
    Topic("segments", "What are the lead segments?",
          ["what are the lead segments", "what is high intent segment", "how are leads segmented",
           "what is low engagement", "student segmentation", "what does engaged prospects mean",
           "kmeans clusters", "what is casual browsers", "casual browsers segment", "engaged prospects segment",
           "high intent segment meaning", "engagement segments"],
          a_segments, roles=STAFF_ROLES,
          links={"manager": [("Student Segmentation", "/student-segmentation")]}),
    Topic("budget", "How does budget planning work?",
          ["how does budget optimization work", "how do budget scenarios work", "what is the what if simulator",
           "how is the budget allocated", "linear program budget", "how do i plan the campaign budget"],
          a_budget, roles=STAFF_ROLES,
          links={"manager": [("Budget Optimization", "/budget-optimization"), ("What-If Simulator", "/what-if")]}),
    Topic("channels", "What are channel analytics?",
          ["what is channel attribution", "which channel performs best", "channel analytics",
           "campaign analytics", "cost per conversion by channel"],
          a_channels, roles=STAFF_ROLES,
          links={"manager": [("Channel Attribution", "/channel-attribution"), ("Campaign Analytics", "/campaign-analytics")]}),
    Topic("threshold", "What is the conversion threshold?",
          ["what is the conversion threshold", "how do i change the threshold", "decision threshold",
           "what threshold is used for high probability leads"],
          a_threshold, roles=STAFF_ROLES,
          links={"admin": [("Platform Settings", "/admin/configuration")]}),
    Topic("programs", "Which programmes are offered?",
          ["which courses are offered", "what programs are available", "list of courses",
           "do you have mba", "is bca available", "what courses can i apply for", "course list",
           "programmes offered"],
          a_programs,
          links={"student": [("New Enquiry", "/student/enquiries/new")], "admin": [("Courses / Programs", "/admin/courses")]}),
    Topic("not_available", "Fees, eligibility and deadlines",
          ["what is the fee", "fees structure", "how much does the course cost", "tuition fee",
           "eligibility criteria", "minimum marks required", "what is the cutoff", "last date to apply",
           "application deadline", "when does admission close", "scholarship available", "hostel facility",
           "how many seats", "entrance exam required", "placement record", "documents required for admission"],
          a_not_available, links=STUDENT_LINKS),
    Topic("submit_enquiry", "How do I submit an enquiry?",
          ["how do i submit an enquiry", "how to apply", "how do i enquire about a course",
           "where do i register interest", "new enquiry", "how to contact admission team",
           "how can i apply", "how do i apply for a course", "apply for admission", "application process",
           "how to join a course", "register for a course"],
          a_submit_enquiry, roles=("student",), links=STUDENT_LINKS),
    Topic("enquiry_statuses", "What do the enquiry statuses mean?",
          ["what does under review mean", "what does counselling status mean", "what are the enquiry statuses",
           "what does not converted mean", "meaning of application status", "what does submitted mean",
           "what happens after i submit an enquiry", "what happens next after my enquiry", "enquiry process steps"],
          a_enquiry_statuses,
          links={"student": [("Enquiry Status", "/student/enquiries/status")]}),
    Topic("profile", "How do I update my profile?",
          ["how do i update my profile", "change my phone number", "edit my details", "update address"],
          a_profile, roles=("student",), links={"student": [("My Profile", "/student/profile")]}),
    Topic("privacy", "What happens to my data?",
          ["is my data safe", "what data do you store", "privacy", "who can see my information",
           "do you store my chats"],
          a_privacy),
    Topic("datasets", "How do I upload lead data?",
          ["how do i upload a dataset", "import leads", "upload csv", "data import format",
           "what file format can i upload"],
          a_datasets, roles=STAFF_ROLES,
          links={"admin": [("Datasets", "/admin/datasets"), ("Data Import", "/admin/data-import")]}),
    Topic("roles", "Who can do what?",
          ["what are the user roles", "what can a manager do", "what can an admin do", "user permissions"],
          a_roles),
]

TOPIC_BY_ID = {topic.id: topic for topic in TOPICS}
