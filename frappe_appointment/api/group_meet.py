import json

import frappe
import frappe.utils
from frappe import _

from frappe_appointment.frappe_appointment.doctype.appointment_group.appointment_group import _get_time_slots_for_day
from frappe_appointment.helpers.overrides import add_response_code
from frappe_appointment.helpers.utils import utc_to_sys_time
from frappe_appointment.overrides.event_override import APPOINTMENT_GROUP, _create_event_for_appointment_group


def _resolve_appointment_group(appointment_group_id: str):
    """Resolve Appointment Group by docname, then fall back to legacy/display-name links."""
    lookup_candidates = [appointment_group_id]

    scrubbed_candidate = frappe.scrub(appointment_group_id).replace("_", "-")
    if scrubbed_candidate not in lookup_candidates:
        lookup_candidates.append(scrubbed_candidate)

    for candidate in lookup_candidates:
        if frappe.db.exists(APPOINTMENT_GROUP, candidate):
            return frappe.get_doc(APPOINTMENT_GROUP, candidate)

    # Legacy links may pass the display name instead of docname.
    group_name_candidates = [appointment_group_id, appointment_group_id.replace("+", " ")]
    for group_name in group_name_candidates:
        docname = frappe.db.get_value(APPOINTMENT_GROUP, {"group_name": group_name}, "name")
        if docname:
            return frappe.get_doc(APPOINTMENT_GROUP, docname)

    frappe.throw(_("Invalid Appointment Group link"))


@frappe.whitelist(allow_guest=True)
@add_response_code
def get_time_slots(appointment_group_id: str, date: str, user_timezone_offset: str, **args):
    if not appointment_group_id:
        frappe.throw(_("Appointment Group ID is required"))

    if not date:
        frappe.throw(_("Date is required"))

    appointment_group = _resolve_appointment_group(appointment_group_id)

    time_slots = _get_time_slots_for_day(appointment_group, date, user_timezone_offset)
    if time_slots and isinstance(time_slots, dict):
        time_slots["title"] = appointment_group.group_name
        time_slots["rescheduling_allowed"] = bool(appointment_group.allow_rescheduling)
    return time_slots


@frappe.whitelist(allow_guest=True)
@add_response_code
def lookup_contact(email: str = None, phone: str = None):
    """Prefill helper for the booking contact form. Matches an existing
    contact by email or phone via whichever product app is installed on
    this site; returns not-found when none is (e.g. no CRM app installed)."""
    if "vmator_fe" not in frappe.get_installed_apps():
        return {"found": False}

    from vmator_fe.api import lookup_lead_contact

    contact = lookup_lead_contact(email=email, phone=phone)
    if not contact:
        return {"found": False}

    return {"found": True, **contact}


@frappe.whitelist(allow_guest=True)
@add_response_code
def get_company_options(appointment_group_id: str = None):
    """Location dropdown options for the booking form. Empty options means
    the frontend should skip the dropdown and just use the default."""
    if "vmator_fe" not in frappe.get_installed_apps():
        return {"options": [], "default": None}

    from vmator_fe.api import get_shop_company_options

    return get_shop_company_options()


@frappe.whitelist(allow_guest=True)
@add_response_code
def book_time_slot(
    appointment_group_id: str,
    date: str,
    start_time: str,
    end_time: str,
    user_timezone_offset: str,
    user_name: str = None,
    user_email: str = None,
    user_phone: str = None,
    company: str = None,
    **args,
):
    appointment_group = _resolve_appointment_group(appointment_group_id)

    # A reschedule is authorized by its event_token alone, same as before
    # this feature -- don't force a returning visitor to re-enter contact
    # info just to move an existing booking.
    is_reschedule = bool(args.get("reschedule"))

    if not is_reschedule and not (user_name and user_email):
        frappe.throw(_("Name and email are required to book an appointment."))

    if not is_reschedule:
        if not args.get("subject"):
            args["subject"] = f"{appointment_group.group_name}: {user_name}"

        contact_lines = [f"Name: {user_name}", f"Email: {user_email}"]
        if user_phone:
            contact_lines.append(f"Phone: {user_phone}")
        existing_description = args.get("description") or ""
        args["description"] = "\n".join(contact_lines) + (
            f"\n\n{existing_description}" if existing_description else ""
        )

        if "vmator_fe" in frappe.get_installed_apps():
            from vmator_fe.api import book_scheduler_appointment

            result = book_scheduler_appointment(
                full_name=user_name,
                email=user_email,
                phone=user_phone,
                start_datetime=utc_to_sys_time(start_time),
                end_datetime=utc_to_sys_time(end_time),
                company=company,
            )
            links = []
            if result.get("crm_lead"):
                links.append({"reference_doctype": "CRM Lead", "reference_docname": result["crm_lead"], "value": user_email})
            if result.get("vmator_appointment"):
                # Ties the Event to its Vmator Appointment so feeds show one row per booking.
                links.append(
                    {
                        "reference_doctype": "Vmator Appointment",
                        "reference_docname": result["vmator_appointment"],
                        "value": user_email,
                    }
                )
            if links:
                args["custom_doctype_link_with_event"] = json.dumps(links)

    resp = _create_event_for_appointment_group(
        appointment_group=appointment_group,
        date=date,
        start_time=start_time,
        end_time=end_time,
        user_timezone_offset=user_timezone_offset,
        event_participants=json.dumps([{"email": user_email}] if user_email else []),
        return_event_id=True,
        **args,
    )
    return resp
