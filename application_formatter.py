import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import os

def format_phone_number(phone: str) -> Dict[str, str]:
    """Format phone number into area code, central office code, and station code."""
    if not phone or len(phone) != 10:
        return {
            "area_code": "",
            "central_office_code": "",
            "station_code": ""
        }
    
    return {
        "area_code": phone[:3],
        "central_office_code": phone[3:6],
        "station_code": phone[6:]
    }

def format_date(date: Optional[str]) -> Optional[str]:
    """Format date string to ISO format."""
    if not date:
        return None
    try:
        return f"{date}T00:00:00"
    except:
        return None

def parse_json_data(json_str: str) -> Dict:
    """Parse JSON string to dictionary."""
    try:
        return json.loads(json_str) if isinstance(json_str, str) else json_str
    except:
        return {}

def get_plan_switch_reason(target_plan: str, current_plan: str) -> str:
    """Determine the reason for switching plans."""
    if not current_plan:
        return "other"

    # Standardize the plan code
    current_plan = current_plan.replace("Select Plan ", "") if isinstance(current_plan, str) else ""
    
    comprehensive_plans = ['A', 'B', 'C', 'D', 'F', 'G', 'High Deductible Plan F', 'Extended']
    basic_plans = ['K', 'L', 'M', 'Basic', '50% Part A Deductible']
    legacy_plans = ['E', 'H', 'I', 'J', 'Pre-Standardized']

    if target_plan == 'N':
        if current_plan in comprehensive_plans:
            return 'fewer_benefits_lower_premiums'
        if current_plan in basic_plans:
            return 'additional_benefits'
        if current_plan in legacy_plans:
            return 'other'
    
    if target_plan == 'G':
        if current_plan in basic_plans + ['N']:
            return 'additional_benefits'
        if current_plan in ['C', 'F', 'High Deductible Plan F', 'Extended']:
            return 'fewer_benefits_lower_premiums'
        if current_plan in legacy_plans:
            return 'other'
    
    return 'other'

def calculate_medicare_dates(birth_date: str, effective_date: str, part_a_date: str, part_b_date: str) -> Dict[str, Any]:
    """Calculate various Medicare-related dates."""
    birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
    effective_date = datetime.strptime(effective_date, '%Y-%m-%d')
    
    # Calculate turning 65 date
    t65_date = birth_date.replace(year=birth_date.year + 65)
    
    # Calculate 6-month windows
    today = datetime.now()
    turn65_upper = effective_date + timedelta(days=180)
    turn65_lower = effective_date - timedelta(days=150)
    
    # Determine if within 6 months of turning 65
    t65_six_months = turn65_lower <= t65_date <= turn65_upper
    
    # Process Part B date if exists
    part_b_six_months = None
    if part_b_date:
        part_b_date = datetime.strptime(part_b_date, '%Y-%m-%d')
        part_b_six_months = turn65_lower <= part_b_date <= turn65_upper

    return {
        "t65_date": t65_date,
        "t65_six_months": t65_six_months,
        "part_b_six_months": part_b_six_months,
        "effective_after_65": effective_date > t65_date
    }

def load_producer_config() -> Dict[str, Any]:
    """Load producer configuration from JSON file."""
    try:
        with open("producer_config.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading producer config: {e}")
        return {}

def format_ace_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format application data specifically for ACE/Chubb."""
    producer_config = load_producer_config()
    
    data = parse_json_data(application_data.get("data"))
    applicant_info = data.get("applicant_info", {})
    medicare_info = data.get("medicare_information", {})
    
    # Calculate Medicare dates
    medicare_dates = calculate_medicare_dates(
        applicant_info.get("applicant_dob"),
        applicant_info.get("effective_date"),
        medicare_info.get("medicare_part_a"),
        medicare_info.get("medicare_part_b")
    )

    formatted_data = {
        "applicant_info": {
            "f_name": applicant_info.get("f_name"),
            "l_name": applicant_info.get("l_name"),
            "address_line1": applicant_info.get("address_line1"),
            "zip5": applicant_info.get("zip5"),
            "applicant_phone": format_phone_number(applicant_info.get("phone")),
            "applicant_dob": format_date(applicant_info.get("applicant_dob")),
            "gender": applicant_info.get("gender"),
            "effective_date": format_date(applicant_info.get("effective_date"))
        },
        "medicare_information": {
            "medicare_information_claim_number": medicare_info.get("medicareNumber"),
            "medicare_information_ssn": medicare_info.get("max_ssn"),
            "medicare_part_a_coverage": True if medicare_info.get("medicare_part_a") else False,
            "medicare_part_b_coverage": True if medicare_info.get("medicare_part_b") else False,
            "medicare_part_a_eff_date": format_date(medicare_info.get("medicare_part_a")),
            "medicare_part_b_eff_date": format_date(medicare_info.get("medicare_part_b")),
            "enroll_part_b_more_than_once": False,
            "did_turn_65_in_last_six_mo": medicare_dates["t65_six_months"],
            "enroll_part_b_last_6_mo": medicare_dates["part_b_six_months"],
            "renal_failure": False,
            "Electronic_Combined": False
        },
        "producer": {
            "producer_first_name": producer_config.get("first_name"),
            "producer_last_name": producer_config.get("last_name"),
            "producer_phone": format_phone_number(producer_config.get("phone")),
            "producer_email": producer_config.get("email"),
            "business_type": "new",
            "has_other_inforce_policies": False,
            "deliver_policy_to": "APP",
            "policy_delivery_type": "paper",
            "agent_address_line1": producer_config.get("address_line1"),
            "agent_zip5": producer_config.get("address_zip5"),
            "agent_address_city": producer_config.get("address_city"),
            "agent_address_state": producer_config.get("address_state"),
            "replacement_notice": True
        }
    }
    
    return formatted_data

def format_aetna_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format application data specifically for Aetna."""
    producer_config = load_producer_config()
    
    data = parse_json_data(application_data.get("data"))
    applicant_info = data.get("applicant_info", {})
    medicare_info = data.get("medicare_information", {})
    
    medicare_dates = calculate_medicare_dates(
        applicant_info.get("applicant_dob"),
        applicant_info.get("effective_date"),
        medicare_info.get("medicare_part_a"),
        medicare_info.get("medicare_part_b")
    )

    formatted_data = {
        "applicant_info": {
            "f_name": applicant_info.get("f_name"),
            "l_name": applicant_info.get("l_name"),
            "address_line1": applicant_info.get("address_line1"),
            "zip5": applicant_info.get("zip5"),
            "applicant_phone": format_phone_number(applicant_info.get("phone")),
            "applicant_dob": format_date(applicant_info.get("applicant_dob")),
            "gender": applicant_info.get("gender"),
            "effective_date": format_date(applicant_info.get("effective_date"))
        },
        "medicare_information": {
            "medicare_information_claim_number": medicare_info.get("medicareNumber"),
            "medicare_information_ssn": medicare_info.get("max_ssn"),
            "medicare_part_a_coverage": True if medicare_info.get("medicare_part_a") else False,
            "medicare_part_b_coverage": True if medicare_info.get("medicare_part_b") else False,
            "medicare_part_a_eff_date": format_date(medicare_info.get("medicare_part_a")),
            "medicare_part_b_eff_date": format_date(medicare_info.get("medicare_part_b")),
            "did_turn_65_in_last_six_mo": medicare_dates["t65_six_months"],
            "enroll_part_b_last_6_mo": medicare_dates["part_b_six_months"]
        },
        "producer": {
            "producer_first_name": producer_config.get("first_name"),
            "producer_last_name": producer_config.get("last_name"),
            "producer_phone": format_phone_number(producer_config.get("phone")),
            "producer_email": producer_config.get("email"),
            "producer_writing_number": producer_config.get("writing_numbers", {}).get("aetna"),
            "deliver_policy_to": "applicant",
            "e_delivery": False,
            "accurate_recording": True,
            "interviewed_applicants": True,
            "application_provided": True,
            "replacement_notice": True,
            "agent_requests_split_commissions": False
        }
    }
    
    return formatted_data

def format_allstate_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format application data specifically for Allstate."""
    producer_config = load_producer_config()
    
    data = parse_json_data(application_data.get("data"))
    applicant_info = data.get("applicant_info", {})
    medicare_info = data.get("medicare_information", {})
    
    medicare_dates = calculate_medicare_dates(
        applicant_info.get("applicant_dob"),
        applicant_info.get("effective_date"),
        medicare_info.get("medicare_part_a"),
        medicare_info.get("medicare_part_b")
    )

    formatted_data = {
        "applicant_info": {
            "f_name": applicant_info.get("f_name"),
            "l_name": applicant_info.get("l_name"),
            "address_line1": applicant_info.get("address_line1"),
            "zip5": applicant_info.get("zip5"),
            "applicant_phone": format_phone_number(applicant_info.get("phone")),
            "applicant_dob": format_date(applicant_info.get("applicant_dob")),
            "gender": applicant_info.get("gender"),
            "effective_date": format_date(applicant_info.get("effective_date"))
        },
        "medicare_information": {
            "medicare_information_claim_number": medicare_info.get("medicareNumber"),
            "medicare_information_ssn": medicare_info.get("max_ssn"),
            "medicare_part_a_coverage": True if medicare_info.get("medicare_part_a") else False,
            "medicare_part_b_coverage": True if medicare_info.get("medicare_part_b") else False,
            "medicare_part_a_eff_date": format_date(medicare_info.get("medicare_part_a")),
            "medicare_part_b_eff_date": format_date(medicare_info.get("medicare_part_b")),
            "enroll_part_b_last_6_mo": medicare_dates["part_b_six_months"],
            "did_turn_65_in_last_six_mo": medicare_dates["t65_six_months"],
            "disabled_esrd": False,
            "received_outline": True
        },
        "producer": {
            "producer_first_name": producer_config.get("first_name"),
            "producer_last_name": producer_config.get("last_name"),
            "producer_phone": format_phone_number(producer_config.get("phone")),
            "producer_email": producer_config.get("email"),
            "producer_writing_number": producer_config.get("writing_numbers", {}).get("allstate"),
            "sale": "internet",
            "other_sale_type_description": "",
            "has_other_inforce_policies": False,
            "deliver_policy_to": "applicant",
            "additional_witness": False,
            "agent_related": False,
            "agent_reviewed": True,
            "applicant_reviewed": True
        }
    }
    
    return formatted_data

def format_uhc_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format application data specifically for UnitedHealthcare."""
    producer_config = load_producer_config()
    
    data = parse_json_data(application_data.get("data"))
    applicant_info = data.get("applicant_info", {})
    medicare_info = data.get("medicare_information", {})
    
    medicare_dates = calculate_medicare_dates(
        applicant_info.get("applicant_dob"),
        applicant_info.get("effective_date"),
        medicare_info.get("medicare_part_a"),
        medicare_info.get("medicare_part_b")
    )

    formatted_data = {
        "applicant_info": {
            "poa": True,
            "enroll_kit": True,
            "applicant_plan": applicant_info.get("plan"),
            "effective_date": format_date(applicant_info.get("effective_date")),
            "f_name": applicant_info.get("f_name"),
            "l_name": applicant_info.get("l_name"),
            "address_line1": applicant_info.get("address_line1"),
            "zip5": applicant_info.get("zip5"),
            "applicant_phone": format_phone_number(applicant_info.get("phone")),
            "applicant_dob": format_date(applicant_info.get("applicant_dob")),
            "gender": applicant_info.get("gender")
        },
        "medicare_information": {
            "medicareNumber": medicare_info.get("medicareNumber"),
            "medicare_part_a": medicare_info.get("medicare_part_a"),
            "medicare_part_b": medicare_info.get("medicare_part_b"),
            "max_ssn": medicare_info.get("max_ssn"),
            "medicare_active": True if (
                medicare_info.get("medicare_part_a") and 
                medicare_info.get("medicare_part_b")
            ) else False
        },
        "producer": {
            "agent_first_name": producer_config.get("first_name"),
            "agent_last_name": producer_config.get("last_name"),
            "producer_phone": format_phone_number(producer_config.get("phone")),
            "producer_email": producer_config.get("email"),
            "producer_writing_number": producer_config.get("writing_numbers", {}).get("uhc")
        },
        "plan_documents": {
            "policy_delivery_type": "Mail"
        }
    }
    
    return formatted_data

def format_application(application_data: Dict[str, Any], carrier: str) -> Dict[str, Any]:
    """Main formatting function that handles different carriers."""
    carrier_formatters = {
        "UnitedHealthcare": format_uhc_application,
        "Aetna": format_aetna_application,
        "Allstate": format_allstate_application,
        "Chubb": format_ace_application,
        "ACE": format_ace_application  # Alias for Chubb
    }
    
    formatter = carrier_formatters.get(carrier)
    if not formatter:
        raise ValueError(f"Unsupported carrier: {carrier}")
    
    formatted_data = formatter(application_data)
    
    # Add existing coverage section if present
    data = parse_json_data(application_data.get("data", "{}"))
    medicare_status = application_data.get("onboarding_data", {}).get("medicare_status")
    print(f'medicare_status: {medicare_status}')
    if "existing_coverage" in data:
        existing_coverage = data["existing_coverage"]
        applicant_info = data.get("applicant_info", {})
        
        # Calculate termination date (day before effective date)
        effective_date = datetime.strptime(applicant_info.get("effective_date", ""), "%Y-%m-%d")
        term_date = effective_date - timedelta(days=1)
                
        if medicare_status == "advantage-plan":
            formatted_data["existing_coverage"] = {
                "existing_coverage_medicare_plan": True,
                "existing_coverage_medicare_plan_is_active": True,
                "existing_coverage_medicare_plan_start_date": format_date(existing_coverage.get("advantage_start_date")),
                "existing_coverage_medicare_plan_end_date": format_date(term_date.strftime("%Y-%m-%d")),
                "existing_coverage_medicare_plan_replacement_indicator": True,
                "existing_coverage_medicare_plan_repl_notice_copy": True,
                "existing_coverage_medicare_plan_company": existing_coverage.get("advantage_company"),
                "existing_coverage_medicare_plan_policy_number": f"{existing_coverage.get('advantage_company')} Advantage Plan",
                "existing_coverage_medicare_plan_planned_term_date": format_date(term_date.strftime("%Y-%m-%d")),
                "existing_coverage_medicare_plan_was_first_enrollment": True,
                "existing_coverage_medicare_plan_was_dropped": False,
                "existing_coverage_medicare_plan_reason": "other",
                "existing_coverage_medicare_plan_reason_other": "More Comprehensive Coverage"
            }
        elif medicare_status == "supplemental-plan":
            formatted_data["existing_coverage"] = {
                "existing_ms_inforce_policy": True,
                "intend_to_replace_existing_ms_inforce_policy": True,
                "existing_ms_inforce_repl_notice_copy": True,
                "replacement_reason": get_plan_switch_reason(
                    applicant_info.get("applicant_plan"),
                    existing_coverage.get("other_ms_carrier_product_code")
                ),
                "replacement_reason_other": "More Comprehensive Coverage",
                "other_ms_carrier_start_date": format_date(existing_coverage.get("supplemental_start_date")),
                "other_ms_carrier_term": format_date(term_date.strftime("%Y-%m-%d")),
                "other_ms_carrier": existing_coverage.get("supplemental_company"),
                "other_ms_carrier_product_code": existing_coverage.get("supplemental_other_ms_carrier_product_code"),
                "other_ms_carrier_policy_number": f"{existing_coverage.get('supplemental_company')} {existing_coverage.get('supplemental_other_ms_carrier_product_code')}"
            }
        elif medicare_status == "no-plan":
            formatted_data["existing_coverage"] = {
                "other_health_ins_past_x_days": existing_coverage.get("other_insurance"),
                "other_health_ins_coverage_active": existing_coverage.get("other_insurance_coverage_active"),
                "other_health_ins_carrier_eff_date": format_date(existing_coverage.get("other_insurance_start_date")),
                "other_health_ins_carrier_end_date": format_date(term_date.strftime("%Y-%m-%d")),
                "other_health_ins_carrier_company": existing_coverage.get("other_insurance_company"),
                "other_health_ins_carrier_phone_number": format_phone_number("1234567890"),
                "other_health_ins_carrier_product_code": existing_coverage.get("other_insurance_plan_type"),
                "other_health_ins_carrier_policy_number": f"{existing_coverage.get('other_insurance_plan_type')} {existing_coverage.get('other_insurance_company')}",
                "other_health_ins_carrier_disenrollment_reason": "Now covered by Medicare",
                "other_health_ins_carrier_term_date": format_date(term_date.strftime("%Y-%m-%d"))
            }
    
    # Remove any None or empty values
    formatted_data = {
        k: v for k, v in formatted_data.items() 
        if v is not None and (not isinstance(v, dict) or v)
    }
    
    return formatted_data
