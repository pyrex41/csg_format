import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import os
import copy
from routing_number import lookup_routing_number
from rapidfuzz import fuzz

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

def get_plan_switch_reason(target_plan: str, current_plan: str, isUHC: bool = False) -> str:
    print(f'target_plan: {target_plan}, current_plan: {current_plan}')
    """Determine the reason for switching plans."""
    if not current_plan:
        return "other"
    
    if target_plan == current_plan:
        return 'lower_premiums' #if not isUHC else 'SameBenefits'

    # Standardize the plan code
    current_plan = current_plan.replace("Select Plan ", "") if isinstance(current_plan, str) else ""
    
    comprehensive_plans = ['A', 'B', 'C', 'D', 'F', 'G', 'High Deductible Plan F', 'Extended']
    basic_plans = ['K', 'L', 'M', 'Basic', '50% Part A Deductible']
    legacy_plans = ['E', 'H', 'I', 'J', 'Pre-Standardized']

    if target_plan == 'N':
        if current_plan in comprehensive_plans:
            return 'fewer_benefits_lower_premiums' #if not isUHC else 'FewerBenefits'
        if current_plan in basic_plans:
            return 'additional_benefits' #if not isUHC else 'ReplaceAdditionalBenefits'
        if current_plan in legacy_plans:
            return 'other' #if not isUHC else 'OtherReason'
    
    if target_plan == 'G':
        if current_plan in basic_plans + ['N']:
            return 'additional_benefits' #if not isUHC else 'ReplaceAdditionalBenefits'
        if current_plan in ['C', 'F', 'High Deductible Plan F', 'Extended']:
            return 'fewer_benefits_lower_premiums' #if not isUHC else 'FewerBenefits'
        if current_plan in legacy_plans:
            return 'other' #if not isUHC else 'OtherReason'
    
    return 'other' #if not isUHC else 'OtherReason'


def get_naic_code(company: str) -> str:
    """Look up NAIC code for insurance company name using fuzzy matching.
    
    Args:
        company: Company name to look up
        
    Returns:
        NAIC code string if found, empty string if not found
    """
    if not company:
        return ''
        
    try:
        with open('supp_companies_full.json', 'r') as f:
            companies = json.load(f)
            
        # Try exact match first
        for c in companies:
            if c['name_full'].lower() == company.lower():
                return c['naic']
        
        # Common abbreviations and aliases
        company_aliases = {
            'UHC': 'UnitedHealthcare',
            'United Healthcare': 'UnitedHealthcare',
            'United Health Care': 'UnitedHealthcare',
            'BC': 'Blue Cross',
            'BCBS': 'Blue Cross Blue Shield',
            'Aflac': 'American Family Life Assur Co',

        }
        
        # Normalize input company name
        search_company = company_aliases.get(company, company)
        
        # Try fuzzy matching with a threshold
        best_match_score = 0
        best_match_naic = ''
        
        for c in companies:
            # Try both token sort ratio (handles word reordering) and partial ratio
            token_sort_score = fuzz.token_sort_ratio(search_company.lower(), c['name_full'].lower())
            partial_score = fuzz.partial_ratio(search_company.lower(), c['name_full'].lower())
            
            # Take the higher of the two scores
            score = max(token_sort_score, partial_score)
            
            if score > best_match_score:
                best_match_score = score
                best_match_naic = c['naic']
        
        # Only return a match if we're reasonably confident
        return best_match_naic if best_match_score >= 80 else ''
        
    except Exception as e:
        print(f"Error in get_naic_code: {str(e)}")
        return ''

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
    payment_info = data.get("payment", {})
    # Calculate Medicare dates
    medicare_dates = calculate_medicare_dates(
        applicant_info.get("applicant_dob"),
        applicant_info.get("effective_date"),
        medicare_info.get("medicare_part_a"),
        medicare_info.get("medicare_part_b")
    )

    # Get phone from either field
    phone = applicant_info.get('phone') or applicant_info.get('applicant_phone')

    formatted_data = {
        "applicant_info": {
            "f_name": applicant_info.get("f_name"),
            "l_name": applicant_info.get("l_name"),
            "address_line1": applicant_info.get("address_line1"),
            "zip5": applicant_info.get("zip5"),
            "applicant_phone": format_phone_number(phone),
            "applicant_dob": format_date(applicant_info.get("applicant_dob")),
            "gender": applicant_info.get("gender"),
            "effective_date": format_date(applicant_info.get("effective_date")),
            "tobacco_usage": applicant_info.get("tobacco_usage") or applicant_info.get("tobacco") or False,
            "applicant_plan": applicant_info.get("applicant_plan")
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
            "Electronic_Combined": False,
            "apply_guaranteed_issue": False
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
            "replacement_notice_copy": True,
            "Electronic_Combined": False
        },
        "payment": payment_info
    }
    if 'hhd_information' not in data:
        formatted_data["hhd_information"] = {"hhd": False}
    
    return formatted_data

def format_aetna_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format application data specifically for Aetna."""
    producer_config = load_producer_config()
    
    data = parse_json_data(application_data.get("data"))
    applicant_info = data.get("applicant_info", {})
    medicare_info = data.get("medicare_information", {})
    payment_info = data.get("payment", {})
    physician_info = data.get("physician_information", {})
    physician_zip = physician_info.get("physician_zip")
    if physician_zip:
        # Look up city and state from zip code
        with open('zipData.json') as f:
            zip_data = json.load(f).get(physician_zip, {})
        print(f"zip_data: {zip_data}")
        physician_city = zip_data.get("cities", [""])[0] if zip_data.get("cities") else ""
        physician_state = zip_data.get("state", "")
        physician_info["physician_city"] = physician_city
        physician_info["physician_state"] = physician_state

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
            "applicant_phone": format_phone_number(applicant_info.get("applicant_phone")),
            "applicant_dob": format_date(applicant_info.get("applicant_dob")),
            "gender": applicant_info.get("gender"),
            "effective_date": format_date(applicant_info.get("effective_date")),
            "tobacco_usage": applicant_info.get("tobacco_usage") or applicant_info.get("tobacco") or False,
            "height": applicant_info.get("height"),
            "weight": applicant_info.get("weight"),
            "legal_resident": True,
            "applicant_plan": applicant_info.get("applicant_plan")
        },
        "physician_information": physician_info,
        "medicare_information": {
            "medicare_information_claim_number": medicare_info.get("medicareNumber"),
            "medicare_information_ssn": medicare_info.get("max_ssn"),
            "medicare_part_a_coverage": True if medicare_info.get("medicare_part_a") else False,
            "medicare_part_b_coverage": True if medicare_info.get("medicare_part_b") else False,
            "medicare_part_a_eff_date": format_date(medicare_info.get("medicare_part_a")),
            "medicare_part_b_eff_date": format_date(medicare_info.get("medicare_part_b")),
            "did_turn_65_in_last_six_mo": medicare_dates["t65_six_months"],
            "enroll_part_b_last_6_mo": medicare_dates["part_b_six_months"],
            "apply_guaranteed_issue": False
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
            "replacement_notice_copy": True,
            "agent_requests_split_commissions": False
        },
        "payment": payment_info
    }
    if "health_history" in data:
        out = copy.deepcopy(data["health_history"])
        prescription_drug_list = out.pop("prescription_drug_list", [])
        if prescription_drug_list:
            prescribed_medications = {}
            med_name_upper = ""
            for i,dic in enumerate(prescription_drug_list):
                full_name = dic.get("drug", {}).get("drugName")
                if full_name:
                    parts = full_name.split()
                    med_name = []
                    found_upper = False
                    for part in parts:
                        if part.isupper():
                            found_upper = True
                        elif not found_upper:
                            med_name.append(part)
                    med_name = " ".join(med_name)   
                    med_name_upper = med_name
                    prescribed_medications[str(i)] = {
                        "med_name": med_name,
                        "diagnosis": dic.get("diagnosis"),
                    }
            out["med_name"] = med_name_upper
            out["prescribed_medications"] = prescribed_medications
            data["health_history"] = out
    
    if 'hhd_information' not in data:
        formatted_data['hhd_information'] = {
            "household_resident": False,
            "household_resident_has_carrier": False
        }

    return formatted_data

def format_allstate_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format application data specifically for Allstate."""
    producer_config = load_producer_config()
    
    data = parse_json_data(application_data.get("data"))
    applicant_info = data.get("applicant_info", {})
    medicare_info = data.get("medicare_information", {})
    payment_info = data.get("payment", {})
    
    medicare_dates = calculate_medicare_dates(
        applicant_info.get("applicant_dob"),
        applicant_info.get("effective_date"),
        medicare_info.get("medicare_part_a"),
        medicare_info.get("medicare_part_b")
    )
    applicant_info["applicant_phone"] = format_phone_number(applicant_info.get("applicant_phone"))
    applicant_info["tobacco_usage"] = applicant_info.get("tobacco_usage") or applicant_info.get("tobacco") or False
    if not applicant_info["tobacco_usage"] and "tobacco_last_date" in applicant_info:
        del applicant_info["tobacco_last_date"]

    formatted_data = {
        "applicant_info": applicant_info,
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
            "received_outline": True,
            "apply_guaranteed_issue": False
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
            "applicant_reviewed": True,
            "replacement_notice_copy": True
        },
        "payment": payment_info
    }
    formatted_data["payment"]["payment_mode"] = "monthly"

    if "hhd_information" not in data:
        formatted_data["hhd_information"] = {"hhd": False}
    formatted_data["hhd_information"]["activity_tracker"] = False
    formatted_data["hhd_information"]["activity_tacker"] = False

    if "medication_information" in data:
        out = copy.deepcopy(data["medication_information"])
        prescription_drug_list = out.pop("prescription_drug_list", [])
        if prescription_drug_list:
            prescribed_medications = {}
            med_name_upper = ""
            dosage_upper = ""
            for i,dic in enumerate(prescription_drug_list):
                full_name = dic.get("drug", {}).get("drugName")
                if full_name:
                    # Split on uppercase word (SOL, TAB, etc)
                    parts = full_name.split()
                    print(f"parts: {parts}")
                    med_name = []
                    dosage = []
                    found_upper = False
                    
                    for part in parts:
                        if not found_upper and part.isupper():
                            found_upper = True
                        elif found_upper:
                            # Include all remaining parts in dosage
                            dosage.append(part)
                        else:
                            med_name.append(part)
                            
                    med_name = " ".join(med_name)
                    dosage = " ".join(dosage)
                else:
                    med_name = ""
                    dosage = ""
                dosage = dosage.replace("/", ";")
                d = {
                    "med_name": med_name,
                    "diagnosis": dic.get("diagnosis"),
                    "dosage": dosage,
                    "frequency": dic.get("frequency"),
                    "prescription_freq_other": dic.get("quantity"),
                    "using": True,
                }
                prescribed_medications[str(i)] = d 
                med_name_upper = med_name
                dosage_upper = dosage
            out["med_name"] = med_name_upper
            out["dosage"] = dosage_upper
            out["prescribed_medications"] = prescribed_medications
            data["medication_information"] = out

    return formatted_data

def format_uhc_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format application data specifically for UnitedHealthcare."""
    producer_config = load_producer_config()
    
    data = parse_json_data(application_data.get("data"))
    applicant_info = data.get("applicant_info", {})
    medicare_info = data.get("medicare_information", {})
    payment_info = data.get("payment", {})
    payment_info["eft_confirm"] = "ongoing"
    
    medicare_dates = calculate_medicare_dates(
        applicant_info.get("applicant_dob"),
        applicant_info.get("effective_date"),
        medicare_info.get("medicare_part_a"),
        medicare_info.get("medicare_part_b")
    )

    with open('zipData.json') as f:
        zipData = json.load(f)

    zip5 = applicant_info.get("zip5")
    if zip5:
        zip_data = zipData.get(zip5, {})
        address_city = zip_data.get("cities", [""])[0]
        address_state = zip_data.get("state", "")
    else:
        address_city = ""
        address_state = ""

    formatted_data = {
        "applicant_info": {
            **applicant_info,
            "poa": True,
            "enroll_kit": True,
            "applicant_plan": applicant_info.get("plan") or applicant_info.get("applicant_plan"),
            "effective_date": format_date(applicant_info.get("effective_date")),
            "applicant_phone": format_phone_number(applicant_info.get("applicant_phone") or applicant_info.get("phone")),
            "applicant_dob": format_date(applicant_info.get("applicant_dob")),
            "tobacco_usage": applicant_info.get("tobacco_usage") or applicant_info.get("tobacco") or False,
            "address_city": address_city,
            "address_state": address_state,
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
            "apply_guaranteed_issue": False,
            "medicare_active": True
        },
        "producer": {
            "agent_first_name": producer_config.get("first_name"),
            "agent_last_name": producer_config.get("last_name"),
            "producer_phone": format_phone_number(producer_config.get("phone")),
            "producer_email": producer_config.get("email"),
            "producer_writing_number": producer_config.get("writing_numbers", {}).get("uhc"),
            "policy_delivery_type": "Mail"
        },
        "plan_documents": {
            "policy_delivery_type": "Mail"
        },
        "payment": payment_info
    }

    
    return formatted_data

def truncate_json(data: Dict, max_length: int = 500) -> str:
    """Truncate JSON string representation for logging."""
    json_str = json.dumps(data)
    if len(json_str) <= max_length:
        return json_str
    return json_str[:max_length] + "..."

def format_application(application_data: Dict[str, Any], carrier: str) -> Dict[str, Any]:
    """Main formatting function that handles different carriers."""
    print(f"Starting format_application for carrier: {carrier}")
    print(f"Input application_data (truncated): {truncate_json(application_data)}")
    
    carrier_formatters = {
        "UnitedHealthcare": format_uhc_application,
        "Aetna": format_aetna_application,
        "Allstate": format_allstate_application,
        "Chubb": format_ace_application,
        "ACE": format_ace_application
    }
    
    formatter = carrier_formatters.get(carrier)
    if not formatter:
        error_msg = f"Unsupported carrier: {carrier}"
        print(f"Error: {error_msg}")
        raise ValueError(error_msg)
    
    try:
        formatted_data = formatter(application_data)
        print(f"Base formatted data (truncated): {truncate_json(formatted_data)}")
        
        data = parse_json_data(application_data.get("data", "{}"))
        print(f"Parsed application data (truncated): {truncate_json(data)}")
        
        medicare_status = application_data.get("onboarding_data", {}).get("medicare_status")
        print(f"Medicare status: {medicare_status}")
        
        if "existing_coverage" in data:
            print("Processing existing coverage data")
            existing_coverage = data["existing_coverage"]
            applicant_info = data.get("applicant_info", {})
            
            try:
                effective_date = datetime.strptime(applicant_info.get("effective_date", ""), "%Y-%m-%d")
                term_date = effective_date - timedelta(days=1)
                print(f"Calculated term_date: {term_date}")
            except ValueError as e:
                print(f"Error parsing effective_date: {e}")
                print(f"Raw effective_date value: {applicant_info.get('effective_date')}")
                raise
            
            if medicare_status == "advantage-plan":
                formatted_data["existing_coverage"] = {
                    "existing_coverage_medicare_plan": True,
                    "existing_ms_inforce_policy": False,
                    "other_health_ins_past_x_days": False,
                    "existing_coverage_medicare_plan_is_active": True,
                    "existing_coverage_medicare_plan_start_date": format_date(existing_coverage.get("advantage_start_date")),
                    "existing_coverage_medicare_plan_end_date": format_date(term_date.strftime("%Y-%m-%d")),
                    "existing_coverage_medicare_plan_replacement_indicator": True,
                    "existing_coverage_medicare_plan_repl_notice_copy": True,
                    "existing_coverage_medicare_plan_company": existing_coverage.get("advantage_company"),
                    "existing_coverage_medicare_plan_policy_number": "Advantage Plan" if existing_coverage.get('advantage_company') is None else f"{existing_coverage.get('advantage_company')} Advantage Plan",
                    "existing_coverage_medicare_plan_planned_term_date": format_date(term_date.strftime("%Y-%m-%d")),
                    "existing_coverage_medicare_plan_was_first_enrollment": True,
                    "existing_coverage_medicare_plan_was_dropped": False,
                    "existing_coverage_medicare_plan_reason": {
                        "0": "o",
                        "1": "t",
                        "2": "h",
                        "3": "e",
                        "4": "r",
                        "other": True,
                    }
                }
            elif medicare_status == "supplemental-plan":
                formatted_data["existing_coverage"] = {
                    "existing_coverage_medicare_plan": False,
                    "other_health_ins_past_x_days": False,
                    "existing_ms_inforce_policy": True,
                    "intend_to_replace_existing_ms_inforce_policy": True,
                    "existing_ms_inforce_repl_notice_copy": True,
                    "replacement_reason": get_plan_switch_reason(
                        applicant_info.get("applicant_plan"),
                        existing_coverage.get("other_ms_carrier_product_code") or existing_coverage.get("supplemental_other_ms_carrier_product_code"),
                        True
                    ),
                    "replacement_reason_other": "More Comprehensive Coverage",
                    "other_ms_carrier_start_date": format_date(existing_coverage.get("supplemental_start_date")),
                    "other_ms_carrier_term": format_date(term_date.strftime("%Y-%m-%d")),
                    "other_health_ins_carrier_end_date": format_date(term_date.strftime("%Y-%m-%d")),
                    "other_ms_carrier": existing_coverage.get("supplemental_company"),
                    "other_ms_carrier_product_code": existing_coverage.get("supplemental_other_ms_carrier_product_code"),
                    "other_ms_carrier_policy_number": "Supplemental Plan" if existing_coverage.get('supplemental_company') is None else f"{existing_coverage.get('supplemental_other_ms_carrier_product_code')} {existing_coverage.get('supplemental_company')}",
                    "other_ms_carrer_naic": get_naic_code(existing_coverage.get("supplemental_company"))
                }
            elif medicare_status == "no-plan":
                formatted_data["existing_coverage"] = {
                    "existing_ms_inforce_policy": False,
                    "existing_coverage_medicare_plan": False,
                    "other_health_ins_past_x_days": existing_coverage.get("other_insurance"),
                    "other_health_ins_coverage_active": existing_coverage.get("other_insurance_coverage_active"),
                    "other_health_ins_carrier_eff_date": format_date(existing_coverage.get("other_insurance_start_date")),
                    "other_health_ins_carrier_end_date": format_date(term_date.strftime("%Y-%m-%d")),
                    "other_health_ins_carrier_company": existing_coverage.get("other_insurance_company"),
                    "other_health_ins_carrier_phone_number": format_phone_number("1234567890"),
                    "other_health_ins_carrier_product_code": existing_coverage.get("other_insurance_plan_type"),
                    "other_health_ins_carrier_policy_number": "Other Plan" if existing_coverage.get('other_insurance_plan_type') is None and existing_coverage.get('other_insurance_company') is None else f"{existing_coverage.get('other_insurance_plan_type')} {existing_coverage.get('other_insurance_company')}",
                    "other_health_ins_carrier_disenrollment_reason": "Now covered by Medicare",
                    "other_health_ins_carrier_term_date": format_date(term_date.strftime("%Y-%m-%d"))
                }

            formatted_data["existing_coverage"]["state_covered_medical_assistance"] = existing_coverage.get("state_covered_medical_assistance")
            if existing_coverage.get("medicaid_pay_premiums"):
                formatted_data["existing_coverage"]["medicaid_pay_premiums"] = existing_coverage.get("medicaid_pay_premiums")
            if existing_coverage.get("received_medicaid_benefits"):
                formatted_data["existing_coverage"]["received_medicaid_benefits"] = existing_coverage.get("received_medicaid_benefits")
            formatted_data["existing_coverage"]["apply_guaranteed_issue"] = False
         
        # Remove any None or empty values recursively
        def remove_empty_values(d):
            if not isinstance(d, dict):
                return d
            return {
                k: remove_empty_values(v)
                for k, v in d.items()
                if v is not None and (not isinstance(v, dict) or v)
            }
            
        formatted_data = remove_empty_values(formatted_data)
        
        if "payment" in formatted_data:
            payment_info = formatted_data["payment"]
            routing_number = payment_info.get("eft_routing_number")
            existing_bank_name = payment_info.get("eft_financial_institution_name")
            print(f"existing_bank_name: {existing_bank_name}")
            existing_bank_name = None if existing_bank_name == "" else existing_bank_name
            if routing_number and not existing_bank_name:
                bank_info = lookup_routing_number(routing_number)
                if bank_info.get("code") == 200:
                    payment_info["eft_financial_institution_name"] = bank_info.get("name")
        
        print(f"Final formatted data (truncated): {truncate_json(formatted_data)}")
        print(f'sections: {formatted_data.keys()}')
        return formatted_data
    except Exception as e:
        print(f"Error in format_application: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise
