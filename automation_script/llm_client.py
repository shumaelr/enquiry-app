"""
LLM Client module for communicating with Claude API.
"""
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()


def get_system_prompt_for_category(category: str) -> str:
    """Get the appropriate system prompt based on document category."""
    
    base_prompt = """You are an expert engineering assistant specializing in solar/electrical power systems.
Your task is to extract specific technical data from documents based on user instructions.

CRITICAL OUTPUT RULES:
1. Output ONLY valid JSON - no markdown, no explanations, no conversational text.
2. Do NOT wrap the output in ```json``` code blocks.
3. If a value is not found in the document, use "Not stated" or "NA" rather than null or empty string.
4. Read the ENTIRE document carefully, zooming into all sections.
"""

    if category.upper() == "BOQ":
        return base_prompt + """
FOR BOQ (Bill of Quantities) DOCUMENTS, use these field names:
{
  "project_name": "Project name",
  "engineering_consultant": "Engineering consultant company",
  "epc": "EPC contractor name",
  "9com_numbers": "List of 9COM numbers with equipment descriptions",
  "standards": "Applicable standards (IEC, IEEE, SAES, SAMSS)",
  "number_of_systems": "Total number of systems",
  "wattage": "Load/wattage values",
  "number_of_sites": "Number of sites",
  "battery_type": "Battery type (NiCd, VRLA, etc.)",
  "battery_autonomy": "Battery autonomy time",
  "battery_capacity": "Battery capacity (Ah)",
  "environmental_conditions": "Environmental conditions",
  "temperature_range": "Operating temperature range",
  "support_structure": "Support structure specifications",
  "other_specifications": "Other equipment specifications",
  "other_services": "Additional services required"
}
"""
    
    elif category.upper() == "SIZING":
        return base_prompt + """
FOR SIZING DOCUMENTS, extract data for EACH SYSTEM/SITE separately.
Use this structure - "systems" is an array with one object per site:
{
  "systems": [
    {
      "site_name": "Site/system identifier (e.g., MLIV-1 @ KM 3.40)",
      "solar_panels_config": "1x100% or 2x50%",
      "charge_controllers_config": "1x100% or 2x50%",
      "batteries_config": "1x100% or 2x50%",
      "load_list": "List of loads with power and run-times",
      "future_expansion_factor": "Factor for future expansion (e.g., 1.1 for 10%)",
      "battery_backup_time": "Backup time in hours",
      "ageing_factor": "Battery ageing factor",
      "design_factor": "Battery design factor",
      "temperature_compensation": "Temperature compensation factor",
      "other_battery_factors": "Any other factors considered for battery capacity",
      "computed_battery_capacity": "Computed/required battery capacity at the end",
      "end_of_discharge_voltage": "End of discharge voltage per cell",
      "cells_in_series": "Number of cells in series",
      "proposed_cell_capacity": "Proposed battery cell capacity",
      "parallel_strings": "Number of parallel sets/strings as per proposal",
      "derating_factors": "List of all derating factors for Solar Sizing",
      "sun_hours": "Sun hours considered",
      "solar_future_factor": "Future factor for solar sizing",
      "solar_sizing_formula": "Formula used for solar sizing",
      "total_daily_ah": "Total Daily Required Ah for Solar Array sizing",
      "solar_panels_per_string": "How many solar panels in one string",
      "parallel_solar_panels": "How many parallel solar panels"
    }
  ]
}
"""
    
    elif category.upper() == "SLD":
        return base_prompt + """
FOR SLD (Single Line Diagram) DOCUMENTS, extract data for EACH SYSTEM/SITE separately.
Use this structure - "systems" is an array with one object per site:
{
  "systems": [
    {
      "site_name": "Site/system identifier",
      "solar_panels_config": "1x100% or 2x50%",
      "array_junction_boxes": "Array junction boxes required? Yes/No with details",
      "charge_controller_type": "MPPT or PWM with details",
      "hardwired_signals": "List of hard-wired signals from charge controller to RTU",
      "other_signals": "Any other signals/alarms from charge controller",
      "battery_breaker_box": "Battery breaker box required? Yes/No",
      "num_battery_breaker_boxes": "Number of battery breaker boxes required",
      "battery_config": "Battery configuration 1x100% or 2x50%",
      "battery_type": "NiCd or VRLA",
      "cells_in_series": "How many cells in series",
      "battery_strings": "How many strings/sets of batteries",
      "battery_enclosure_rating": "Required battery enclosure IP/NEMA rating",
      "required_backup": "Required back-up/autonomy in hours",
      "panel_board_required": "Panel board/DB/LOS required? Yes/No",
      "los_enclosure_rating": "Enclosure rating of LOS/power panel",
      "breaker_list": "Number of breakers and their ratings in LOS",
      "pv_notes": "Relevant notes for PV/charge controller",
      "battery_notes": "Relevant notes for batteries/enclosure",
      "other_equipment": "Other equipment not explicitly covered",
      "critical_points": "Any other critical points for system design"
    }
  ]
}
"""
    
    return base_prompt


def process_with_claude(pdf_text: str, prompt_instructions: str, category: str = "BOQ") -> dict | list | None:
    """
    Sends the document and instructions to Claude and expects JSON output.
    
    Args:
        pdf_text: Extracted text from the PDF document.
        prompt_instructions: Instructions from the prompt file.
        category: Document category (BOQ, Sizing, SLD).
        
    Returns:
        Parsed JSON data or None if an error occurs.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        return None
    
    client = anthropic.Anthropic(api_key=api_key)
    
    system_prompt = get_system_prompt_for_category(category)
    
    user_message = f"""### INSTRUCTIONS FROM PROMPT FILE ###
{prompt_instructions}

### DOCUMENT CONTENT TO ANALYZE ###
{pdf_text}

### YOUR TASK ###
Extract the relevant data according to the instructions above.
Format your response as a valid JSON object.
The JSON keys should match column headers suitable for an Excel spreadsheet.
"""
    
    try:
        print(f"Calling Claude model: {model}")
        
        message = client.messages.create(
            model=model,
            max_tokens=8192,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        content = message.content[0].text.strip()
        
        # Clean up if Claude adds markdown code blocks despite instructions
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        result = json.loads(content)
        
        print(f"Successfully parsed JSON response with {len(str(result))} characters")
        return result
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from Claude response: {e}")
        print(f"Raw response: {content[:500]}...")
        return None
        
    except anthropic.APIError as e:
        print(f"Anthropic API error: {e}")
        return None
        
    except Exception as e:
        print(f"Error calling Claude: {e}")
        return None
