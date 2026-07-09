"""Prompt templates for AI-generated concept paper content."""


def concept_paper_body(subject: str, formatted_start: str, formatted_end: str, location: str) -> str:
    return f"""Generate a formal body text for a concept paper with the following details:
    Event: {subject}
    Date and Time: From {formatted_start} to {formatted_end}
    Location: {location}

    Requirements:
    1. Use formal and professional language
    2. Explain the purpose and significance of the event
    3. Highlight key activities or components
    4. Keep it concise but informative
    5. Include relevant details about timing and location
    6. Make it engaging and well-structured
    7. Avoid any unnecessary jargon
    8. Format as a single cohesive paragraph"""


def concept_paper_description(subject: str) -> str:
    return f"""Generate a detailed description for a concept paper about {subject}.

    Requirements:
    1. Write as a single cohesive paragraph
    2. Provide a comprehensive overview of the event/activity
    3. Include the rationale and importance
    4. Describe the target audience and potential impact
    5. Keep language formal but accessible
    6. Focus on practical and measurable aspects
    7. Do not use any text formatting or special characters
    8. Do not use bullet points or line breaks
    9. Include potential benefits to participants
    10. Keep it concise but informative"""


def concept_paper_objectives(subject: str) -> str:
    return f"""Generate specific objectives for {subject}.

    Requirements:
    1. Create 3-5 SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
    2. Focus on concrete outcomes
    3. Use action verbs
    4. Make them relevant to the event purpose
    5. Ensure they are realistic and achievable
    6. Format as a bullet-point list
    7. Keep each objective concise
    8. Align with academic/educational goals"""


def concept_paper_learning_outcomes(subject: str) -> str:
    return f"""Generate learning outcomes for {subject}.

    Requirements:
    1. Create 3-5 specific learning outcomes
    2. Use Bloom's Taxonomy verbs
    3. Focus on knowledge, skills, and attitudes
    4. Make them measurable and observable
    5. Align with event objectives
    6. Keep language clear and specific
    7. Format as a bullet-point list
    8. Consider both immediate and long-term learning"""


def concept_paper_participants(subject: str) -> str:
    return f"""Suggest a reasonable number of expected participants for {subject}.

    Requirements:
    1. Consider the type of event
    2. Account for venue capacity
    3. Think about resource management
    4. Ensure meaningful participation
    5. Consider typical attendance patterns
    6. Return only a number between 20 and 200"""


def concept_paper_consent(subject: str, formatted_start: str, formatted_end: str, location: str) -> str:
    return f"""Generate a parent/guardian consent form content for {subject}.

    Event Details:
    - Event: {subject}
    - Date and Time: From {formatted_start} to {formatted_end}
    - Location: {location}

    Requirements:
    1. Use formal and professional language
    2. Include clear permission statement
    3. Specify event details and purpose
    4. Mention safety measures and supervision
    5. Include contact information section
    6. Add emergency contact section
    7. Include medical information section
    8. Add signature lines for parent/guardian
    9. Keep it concise but comprehensive
    10. Include any relevant waivers or disclaimers"""
