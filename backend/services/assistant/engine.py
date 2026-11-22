"""Grounded answer engine for the Admission Assistant.

Routing order: greetings and thanks -> lead questions (staff only) -> the
student's own enquiries -> prediction statistics -> fixed safety rules
(admission chance, fees/eligibility) -> TF-IDF retrieval over the knowledge
base -> an honest "I don't know" with suggestions.

Lead predictions are never computed here. They come from the existing
endpoints: the stored out-of-fold prediction (api.leads.get_lead_prediction)
or, when none is stored, live inference (api.workspace.prediction).
"""
from __future__ import annotations

import logging
import re
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from difflib import SequenceMatcher

from fastapi import HTTPException
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import func, or_

from database.models import Lead, MLPrediction, StudentEnquiry
from services.assistant import explain
from services.assistant.knowledge import (
    CONVERSION_NOTICE, ENQUIRY_STATUSES, MANAGER_ROLES, STAFF_ROLES, TOPIC_BY_ID, TOPICS,
    Context, Topic,
)

log = logging.getLogger("assistant")

ROLE_NAMES = {"student": "student", "admission_manager": "admission manager",
              "marketing_manager": "marketing manager", "admin": "administrator"}
ANSWER_THRESHOLD = 0.40   # confident enough to answer
CLARIFY_THRESHOLD = 0.24  # close enough to offer "Did you mean ...?"

ID_PATTERN = re.compile(
    r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|MANUAL-[0-9a-f]{8})\b", re.I)
GREETING = re.compile(r"^\s*(hi|hello|hey|hai|hii+|good\s+(morning|afternoon|evening)|namaste|vanakkam)\b[\s!.,]*$", re.I)
IDENTITY = re.compile(r"\b(who|what) are you\b|\byour name\b|\bare you (a )?(bot|robot|human|ai)\b", re.I)
THANKS = re.compile(r"\b(thanks|thank you|thank u|thx|ty)\b", re.I)
LEAD_WORDS = re.compile(r"\b(lead|prospect|enquir(y|er)|score|prediction|probability|shap|factor)\b", re.I)
EXPLAIN_WORDS = re.compile(r"\b(why|explain|reason|factors?|shap|because|driv\w*|contribut\w*)\b", re.I)
FOLLOWUP_WORDS = re.compile(r"\b(follow[\s-]?up|next steps?|what should (i|we)|suggest\w*|recommend\w*|action|approach|how (to|do i|should i) (contact|reach|convert))\b", re.I)
IMPLICIT_LEAD = re.compile(r"\b(this|that|the|current|same) (lead|prospect|enquiry)\b|\b(it|its|this one)\b|^\s*(why|explain|suggest)", re.I)
MY_ENQUIRY = re.compile(r"\b(status|track\w*|progress|show|list|see|check|view)\b.{0,30}\b(my|mine)\b.{0,20}\b(enquir\w*|applications?)\b"
                        r"|\bmy (enquir\w*|applications?)\b.{0,30}\b(status|progress|update\w*)\b|^\s*(my|show my) (enquir\w*|applications?)\s*\??\s*$", re.I)
STATS = re.compile(r"\b(how many|count|number of|overview|summar\w*|distribution|breakdown|statistics|stats)\b", re.I)
ADMISSION_CHANCE = re.compile(r"\b(chance|probability|predict\w*|likely|possib\w*)\b.{0,40}\b(admission|admit\w*|selected|get in|seat)\b"
                              r"|\b(will|can) i (get|be) (admission|admitted|selected)\b", re.I)
NOT_AVAILABLE = re.compile(r"\b(fees?|cost|tuition|cut[\s-]?off|deadline|last date|scholarships?|hostel|seats?|"
                           r"eligib\w*|entrance|documents? (required|needed)|placements?|minimum marks)\b", re.I)


@dataclass
class Reply:
    text: str
    kind: str
    suggestions: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    card: dict | None = None
    notice: str | None = None
    sources: list[str] = field(default_factory=list)
    confidence: float = 1.0
    engine: str = "grounded"

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- retrieval index
STOP_WORDS = set("""a an the is are was were be been am do does did i me my mine we our you your it its this that
these those to of for in on at by with about from as and or but if so can could would should will shall may might
must please tell show give let know want need what which who whom whose when where why how there here any some
just get got have has had more most very really much many also too than then into out up down over again""".split())


def content_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    out = []
    for token in tokens:
        if token in STOP_WORDS:
            continue
        for suffix in ("ing", "es", "ed", "s"):
            if len(token) > 4 and token.endswith(suffix):
                token = token[: -len(suffix)]
                break
        out.append(token)
    return out


def _similar(a: str, b: str) -> bool:
    if a == b:
        return True
    if min(len(a), len(b)) < 4:
        return False
    return a.startswith(b[:4]) and SequenceMatcher(None, a, b).ratio() >= 0.75


class _Index:
    """TF-IDF retrieval over content words, with a keyword-overlap gate.

    Word and character n-gram scores are blended so typos ("aply", "cours")
    still match. A topic is only eligible when the query shares at least one
    content word with it, which stops chit-chat ("tell me a joke") from being
    matched on function words alone.
    """

    def __init__(self):
        self.docs: list[tuple[str, str]] = []  # (topic id, normalised text)
        self.vocab: dict[str, set[str]] = {}
        for topic in TOPICS:
            words: set[str] = set()
            for text in [topic.title, *topic.patterns]:
                tokens = content_tokens(text)
                words.update(tokens)
                self.docs.append((topic.id, " ".join(tokens)))
            self.vocab[topic.id] = words
        corpus = [text for _, text in self.docs]
        self.word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(corpus)
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True).fit(corpus)
        self.word_matrix = self.word.transform(corpus)
        self.char_matrix = self.char.transform(corpus)

    def ranked(self, query: str, role: str) -> list[tuple[Topic, float]]:
        tokens = content_tokens(query)
        if not tokens:
            return []
        q = " ".join(tokens)
        word = (self.word_matrix @ self.word.transform([q]).T).toarray().ravel()
        char = (self.char_matrix @ self.char.transform([q]).T).toarray().ravel()
        scores = 0.55 * word + 0.45 * char
        best: dict[str, float] = {}
        for (topic_id, _), score in zip(self.docs, scores):
            best[topic_id] = max(best.get(topic_id, 0.0), float(score))
        ranked = []
        for topic_id, score in best.items():
            topic = TOPIC_BY_ID[topic_id]
            if role not in topic.roles:
                continue
            if not any(_similar(t, v) for t in tokens for v in self.vocab[topic_id]):
                continue
            ranked.append((topic, score))
        return sorted(ranked, key=lambda item: -item[1])

    def best(self, query: str, role: str) -> tuple[Topic | None, float]:
        ranked = self.ranked(query, role)
        return ranked[0] if ranked else (None, 0.0)


_index: _Index | None = None
_index_lock = threading.Lock()


def index() -> _Index:
    global _index
    with _index_lock:
        if _index is None:
            _index = _Index()
    return _index


# ---------------------------------------------------------------- context helpers
def _metadata() -> dict:
    try:
        import ml_service as svc
        return svc.load_metadata()
    except Exception:  # model not trained yet: answers degrade gracefully
        return {}


def _configuration(db) -> dict:
    try:
        from api.admin import configuration
        return configuration(db)
    except Exception:
        return {"conversion_threshold": 0.5}


def suggestions_for(role: str, has_lead: bool = False) -> list[str]:
    if role == "student":
        return ["What is the status of my enquiry?", "Which programmes are offered?",
                "How do I submit an enquiry?", "Does Decision-Intel predict my admission chance?"]
    if role in MANAGER_ROLES:
        base = ["How many leads are in each score band?", "How does the prediction model work?",
                "What is SHAP?", "How does budget optimization work?"]
        return (["Why did this lead get its score?", "Suggest follow-up actions for this lead"] + base[:2]) if has_lead else base
    return ["Summarise the stored predictions", "What is the conversion threshold?",
            "How do I upload lead data?", "How accurate is the model?"]


def welcome(role: str, name: str, has_lead: bool = False) -> dict:
    first = (name or "").split(" ")[0] or "there"
    if role == "student":
        text = (f"Hi {first}! I'm the Decision-Intel Admission Assistant. I can check the status of "
                "your enquiries, explain what each status means and help you find the right page.")
    elif role in MANAGER_ROLES:
        text = (f"Hi {first}! I can explain any lead's conversion score using its stored SHAP "
                "factors, suggest follow-up actions, and answer questions about Decision-Intel.")
    else:
        text = (f"Hi {first}! I can summarise stored predictions and explain how the model, "
                "threshold, segments and budget planner work.")
    return {"text": text, "suggestions": suggestions_for(role, has_lead)}


# ---------------------------------------------------------------- lead answers
def find_lead(db, token: str) -> Lead | None:
    token = token.strip()
    return db.query(Lead).filter(or_(
        Lead.id == token, Lead.id == token.lower(),
        Lead.customer_id == token, Lead.customer_id == token.lower(),
        Lead.student_id == token, Lead.student_id == token.upper(),
    )).first()


def load_prediction(lead: Lead, db) -> tuple[dict | None, str | None]:
    """Reuse the existing prediction APIs; never fabricate a score."""
    from api import leads as leads_api
    try:
        return leads_api.get_lead_prediction(lead.id, db), "stored"
    except HTTPException as error:
        if error.status_code != 404:
            raise
    try:
        from api import workspace as workspace_api
        live = workspace_api.prediction(lead.id, explain=True, db=db)
        return {"conversion_probability": live["probability"], "lead_score": live["score"],
                "segment": live.get("segment"), "model": live.get("model"),
                "top_positive": live.get("top_positive") or [],
                "top_negative": live.get("top_negative") or []}, "live"
    except Exception as error:  # model missing or lead lacks usable features
        log.info("live inference unavailable for lead %s: %s", lead.id, error)
        return None, None


def lead_label(lead: Lead) -> str:
    return lead.customer_id or lead.student_id or lead.id


def lead_reply(lead: Lead, db, mode: str) -> Reply:
    prediction, source = load_prediction(lead, db)
    identifier = lead_label(lead)
    if prediction is None:
        return Reply(
            text=(f"Lead {identifier} has no prediction yet, so I can't explain or score it. "
                  "Predictions are created when lead data is imported and the model is run."),
            kind="lead_missing", suggestions=suggestions_for("admission_manager"),
            sources=["leads table"], confidence=1.0)

    probability = float(prediction.get("conversion_probability") or 0.0)
    band = prediction.get("lead_score") or "Low"
    positive = list(prediction.get("top_positive") or [])
    negative = list(prediction.get("top_negative") or [])
    segment = prediction.get("segment")
    source_text = ("stored out-of-fold prediction" if source == "stored"
                   else "live prediction from the current model")

    header = f"Lead {identifier} has an estimated {probability * 100:.1f}% chance of converting, which puts it in the {band} band."
    lines = [header]
    detail = []
    if segment:
        detail.append(f"Engagement segment: {segment}.")
    if lead.lead_status:
        detail.append(f"Sales-team note: “{lead.lead_status}” (recorded by staff; the model does not use it).")
    if detail:
        lines.append(" ".join(detail))

    if mode == "followup":
        actions = explain.follow_up_actions(band, positive, negative,
                                            {"follow_up_status": lead.follow_up_status})
        lines.append("Suggested next steps (rule-based suggestions from the score and its factors, "
                     "not model outputs):\n" + "\n".join(f"- {a}" for a in actions))
        follow = ["Why did this lead get its score?", "What do the score bands mean?"]
    else:
        count = 3 if mode == "explain" else 2
        if positive:
            lines.append("What raised the score:\n" + "\n".join(f"- {explain.factor_sentence(f)}" for f in positive[:count]))
        if negative:
            lines.append("What lowered the score:\n" + "\n".join(f"- {explain.factor_sentence(f)}" for f in negative[:count]))
        if not positive and not negative:
            lines.append("No SHAP factors are stored for this prediction.")
        if mode == "explain":
            lines.append("These are the strongest SHAP factors. They show what the model associated "
                         "with conversion in past data, not what causes a student to enrol.")
        follow = ["Suggest follow-up actions for this lead", "What is SHAP?"]

    card = {
        "lead_id": lead.id, "display_id": identifier, "name": lead.student_name,
        "probability": round(probability, 4), "band": band, "segment": segment,
        "source": source, "model": prediction.get("model") or "lead_conversion_xgboost",
        "positive": [explain.factor_card(f) for f in positive[:3]],
        "negative": [explain.factor_card(f) for f in negative[:3]],
    }
    return Reply(text="\n\n".join(lines), kind=f"lead_{mode}", suggestions=follow,
                 links=[{"label": "Open lead", "href": f"/student-leads/{lead.id}"},
                        {"label": "Explainable AI", "href": "/explainable-ai"}],
                 card=card, notice=CONVERSION_NOTICE, sources=[source_text, "SHAP TreeExplainer"])


def lead_mode(message: str) -> str:
    if FOLLOWUP_WORDS.search(message):
        return "followup"
    if EXPLAIN_WORDS.search(message):
        return "explain"
    return "summary"


# ---------------------------------------------------------------- other answers
def student_enquiries(user, db) -> Reply:
    rows = (db.query(StudentEnquiry).filter_by(student_user_id=user.id)
            .order_by(StudentEnquiry.created_at.desc()).limit(10).all())
    links = [{"label": "Enquiry Status", "href": "/student/enquiries/status"},
             {"label": "New Enquiry", "href": "/student/enquiries/new"}]
    if not rows:
        return Reply(text="You haven't submitted an enquiry yet. Open New Enquiry to tell the admission "
                          "team which course you're interested in.",
                     kind="student_enquiries", links=links[1:], sources=["your enquiries"],
                     suggestions=["Which programmes are offered?", "How do I submit an enquiry?"])
    items = []
    for row in rows:
        when = datetime.fromtimestamp(row.created_at).strftime("%d %b %Y")
        items.append(f"- {row.course_interested}: {row.status} (submitted {when})")
    latest = rows[0]
    meaning = ENQUIRY_STATUSES.get(latest.status)
    text = (f"You have {len(rows)} enquir{'y' if len(rows) == 1 else 'ies'}:\n" + "\n".join(items))
    if meaning:
        text += f"\n\nYour latest enquiry is “{latest.status}”: {meaning}"
    return Reply(text=text, kind="student_enquiries", links=links, sources=["your enquiries"],
                 suggestions=["What do the enquiry statuses mean?", "Which programmes are offered?"])


def prediction_stats(user, db) -> Reply:
    config = _configuration(db)
    threshold = float(config.get("conversion_threshold", 0.5))
    total = db.query(func.count(MLPrediction.id)).scalar() or 0
    leads = db.query(func.count(Lead.id)).scalar() or 0
    if total == 0:
        return Reply(text=f"There are {leads:,} leads but no stored predictions yet. Predictions are "
                          "created when lead data is imported and the model is run.",
                     kind="stats", sources=["ml_predictions table"])
    bands = dict(db.query(MLPrediction.lead_score, func.count(MLPrediction.id))
                 .group_by(MLPrediction.lead_score).all())
    mean = db.query(func.avg(MLPrediction.conversion_probability)).scalar() or 0.0
    above = db.query(func.count(MLPrediction.id)).filter(MLPrediction.conversion_probability >= threshold).scalar() or 0
    lines = "\n".join(f"- {band}: {bands.get(band, 0):,} ({bands.get(band, 0) / total * 100:.1f}%)"
                      for band in ("High", "Medium", "Low"))
    text = (f"{total:,} of {leads:,} leads have a stored prediction. By score band:\n{lines}\n\n"
            f"The average predicted conversion probability is {mean * 100:.1f}%, and {above:,} leads "
            f"are at or above the current threshold of {threshold * 100:.0f}%.")
    links = ([{"label": "Admission Prediction", "href": "/admission-prediction"}]
             if user.role in MANAGER_ROLES else [{"label": "Platform Settings", "href": "/admin/configuration"}])
    return Reply(text=text, kind="stats", links=links, sources=["ml_predictions table", "platform settings"],
                 suggestions=["What do the score bands mean?", "How accurate is the model?"])


def topic_reply(topic: Topic, ctx: Context, confidence: float) -> Reply:
    return Reply(text=topic.answer(ctx), kind="faq", links=topic.links_for(ctx.role),
                 notice=CONVERSION_NOTICE if topic.notice else None,
                 sources=["Decision-Intel knowledge base"], confidence=round(confidence, 3),
                 suggestions=[s for s in suggestions_for(ctx.role) if s.lower() != topic.title.lower()][:3])


# ---------------------------------------------------------------- entry point
def answer(message: str, user, db, context: dict | None = None) -> Reply:
    context = context or {}
    role = user.role
    text = " ".join(message.split())
    context_lead = context.get("lead_id")

    if GREETING.match(text):
        greeting = welcome(role, user.name, bool(context_lead))
        return Reply(text=greeting["text"], kind="greeting", suggestions=greeting["suggestions"])
    if THANKS.search(text) and len(text) < 40:
        return Reply(text="You're welcome! Ask me anything else about your admissions work.",
                     kind="thanks", suggestions=suggestions_for(role, bool(context_lead)))

    # Lead questions
    explicit = ID_PATTERN.search(text)
    # A lead is used only when the message names one, or clearly refers to the
    # lead in context ("this lead", "why?", "suggest next steps for it").
    refers_to_context = bool(context_lead) and bool(IMPLICIT_LEAD.search(text)) and bool(
        LEAD_WORDS.search(text) or EXPLAIN_WORDS.search(text) or FOLLOWUP_WORDS.search(text))
    if explicit or refers_to_context:
        if role not in MANAGER_ROLES:
            if role == "student":
                return Reply(text="Lead scores and their explanations are only available to the admission "
                                  "team. Decision-Intel also does not predict your own chance of admission; "
                                  "for that, the admission team reviews your enquiry.",
                             kind="forbidden", notice=CONVERSION_NOTICE,
                             suggestions=["What is the status of my enquiry?", "How do I submit an enquiry?"])
            return Reply(text="Individual lead scores and explanations are available to admission and "
                              "marketing managers. As an administrator you can view the overall "
                              "prediction summary.",
                         kind="forbidden", suggestions=["Summarise the stored predictions"])
        token = explicit.group(1) if explicit else context_lead
        lead = find_lead(db, token)
        if lead is None:
            return Reply(text=f"I couldn't find a lead with the ID “{token}”. Check the ID on the Student "
                              "Leads page; both the lead ID and the Prospect ID work.",
                         kind="lead_not_found", links=[{"label": "Student Leads", "href": "/student-leads"}],
                         suggestions=suggestions_for(role))
        return lead_reply(lead, db, lead_mode(text))

    if role in MANAGER_ROLES and LEAD_WORDS.search(text) and (EXPLAIN_WORDS.search(text) or FOLLOWUP_WORDS.search(text)) \
            and not STATS.search(text) and re.search(r"\b(this|that|a|the|my) (lead|prospect)\b", text, re.I):
        return Reply(text="Which lead do you mean? Paste its lead ID or Prospect ID, for example "
                          "“Explain lead 7927b2df-8bba-4d29-b9a2-b6e0beafe620”, or open the lead from "
                          "Student Leads and ask again.",
                     kind="clarify", links=[{"label": "Student Leads", "href": "/student-leads"}],
                     suggestions=suggestions_for(role))

    if role == "student" and MY_ENQUIRY.search(text):
        return student_enquiries(user, db)

    if role in STAFF_ROLES and STATS.search(text) and re.search(r"\b(leads?|predictions?|scores?|bands?)\b", text, re.I):
        return prediction_stats(user, db)

    ctx = _ctx(role, db)
    if ADMISSION_CHANCE.search(text):
        return topic_reply(TOPIC_BY_ID["conversion_vs_eligibility"], ctx, 1.0)
    if NOT_AVAILABLE.search(text) and not LEAD_WORDS.search(text):
        return topic_reply(TOPIC_BY_ID["not_available"], ctx, 1.0)

    if IDENTITY.search(text):
        return topic_reply(TOPIC_BY_ID["assistant_help"], ctx, 1.0)

    ranked = index().ranked(text, role)
    if ranked and ranked[0][1] >= ANSWER_THRESHOLD:
        return topic_reply(ranked[0][0], ctx, ranked[0][1])
    if ranked and ranked[0][1] >= CLARIFY_THRESHOLD:
        options = [topic.title for topic, score in ranked[:2] if score >= CLARIFY_THRESHOLD]
        return Reply(text="I want to make sure I answer the right question. Did you mean one of these?",
                     kind="clarify", suggestions=options, confidence=round(ranked[0][1], 3))

    return Reply(text="I'm not sure I understood that, and I'd rather not guess. Here are things I can "
                      "help with; you can also rephrase your question.",
                 kind="fallback", suggestions=suggestions_for(role, bool(context_lead)), confidence=0.0)


def _ctx(role: str, db) -> Context:
    return Context(role=role, db=db, metadata=_metadata(), configuration=_configuration(db))
