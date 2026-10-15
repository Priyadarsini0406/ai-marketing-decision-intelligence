"""Shared student directory serialization for administration and managers."""
from database.models import Lead, StudentEnquiry, User


def student_directory(db):
    users = db.query(User).filter(User.role == "student").order_by(User.name, User.email).all()
    records = []
    for user in users:
        profile = user.profile or {}
        enquiries = (db.query(StudentEnquiry)
                     .filter(StudentEnquiry.student_user_id == user.id)
                     .order_by(StudentEnquiry.created_at.desc()).all())
        latest = enquiries[0] if enquiries else None
        records.append({
            "id": user.id,
            "name": user.name,
            "student_name": user.name,
            "email": user.email,
            "active": user.active,
            "profile": profile,
            "enquiry_count": len(enquiries),
            "enquiry_id": latest.id if latest else None,
            "course_interested": profile.get("course_interested") if "course_interested" in profile else (latest.course_interested if latest else None),
            "qualification": profile.get("qualification") if "qualification" in profile else (latest.qualification if latest else None),
            "phone": profile.get("mobile") if "mobile" in profile else (latest.phone if latest else None),
            "location": profile.get("city") if "city" in profile else (latest.location if latest else None),
            "lead_status": latest.status if latest else "Registered",
            "enquiry_source": "Student Portal" if latest else "Registration",
            "enquiry_date": latest.created_at if latest else None,
            "latest_enquiry": ({
                "id": latest.id,
                "course_interested": latest.course_interested,
                "preferred_intake": latest.preferred_intake,
                "qualification": latest.qualification,
                "institution": latest.institution,
                "academic_score": latest.academic_score,
                "location": latest.location,
                "status": latest.status,
                "created_at": latest.created_at,
            } if latest else None),
        })
    account_ids = {user.id for user in users}
    for lead in db.query(Lead).order_by(Lead.enquiry_date.desc()).all():
        if lead.student_id in account_ids:
            continue
        records.append({
            "id": lead.id,
            "name": lead.student_name or lead.customer_id or "Student lead",
            "student_name": lead.student_name or lead.customer_id or "Student lead",
            "email": None,
            "active": True,
            "profile": {},
            "enquiry_count": 0,
            "enquiry_id": None,
            "course_interested": lead.course_interested or lead.program,
            "qualification": lead.qualification,
            "phone": None,
            "location": lead.location,
            "lead_status": lead.lead_status or "New",
            "enquiry_source": lead.enquiry_source or "Imported lead",
            "enquiry_date": lead.enquiry_date,
            "latest_enquiry": {
                "course_interested": lead.course_interested or lead.program,
                "qualification": lead.qualification,
                "location": lead.location,
                "status": lead.lead_status or "New",
            },
        })
    return records
