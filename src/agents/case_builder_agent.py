from agents import Agent, function_tool

from src.tools.case_extraction_tool import extract_consultation_case


@function_tool
def case_extraction_tool(transcript_text: str, doctor_notes: str = "") -> dict:
    """
    Extract structured clinical case data from a consultation transcript
    and optional doctor notes.
    """
    case = extract_consultation_case(
        transcript_text=transcript_text,
        doctor_notes=doctor_notes,
    )
    return case.model_dump()


case_builder_agent = Agent(
    name="case_builder",
    instructions=(
        "Use the provided tool to extract structured, evidence-grounded "
        "clinical case data from consultation inputs."
    ),
    tools=[case_extraction_tool],
    model="gpt-5-nano",
)
