PROMPTS = {
    "company": (
        "Analyze the following company information for fraud and business risk. "
        "Return JSON with keys score (0-100), rationale, and next_steps.\n\n{data}"
    ),
    "context": (
        "Analyze the following deal context for potential risk. "
        "Return JSON with keys score (0-100), rationale, and next_steps.\n\n{data}"
    ),
    "documents": (
        "Analyze the following extracted document text for risk factors. "
        "Return JSON with keys score (0-100), rationale, and next_steps.\n\n{data}"
    ),
    "web": (
        "Analyze the following public data for additional risk signals. "
        "Return JSON with keys score (0-100), rationale, and next_steps.\n\n{data}"
    ),
    "question_gen": (
        "Based on your analysis of the following company data and context, generate a numbered list of 10 important yes/no questions for the user.\n\n{data}"
    ),
    "followup_gen": (
        "Given the company information and the user's previous answers, generate a numbered list of 10 additional yes/no questions to clarify remaining risk.\n\n{data}"
    ),
    "qa": (
        "Analyze the following Q&A responses for additional risk factors. Return JSON with keys score (0-100), rationale, and next_steps.\n\n{data}"
    ),
}
