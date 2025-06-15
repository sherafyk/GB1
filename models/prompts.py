"""Prompt templates used throughout the analysis workflow."""

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
        "Read the following document text and generate a numbered list of 10 important yes/no questions that would help determine the riskiness of the deal and the likelihood of fraud.\n\n{data}"
    ),
    "question_gen_image": (
        "Read the following document image and generate a numbered list of 10 important yes/no questions that would help determine the riskiness of the deal and the likelihood of fraud."
    ),
    "followup_gen": (
        "Given the document text and the user's previous answers, generate a numbered list of 10 additional yes/no questions that further clarify risk or uncertainties.\n\n{data}"
    ),
    "extract": (
        "From the following document text, extract any company details and deal context mentioned."
        " Return JSON with two keys: company and context. The company object may include"
        " name, registration, address, country and directors. The context object may include"
        " transaction_type, description and notes. Use empty strings if information is missing.\n\n{data}"
    ),
    "qa": (
        "Analyze the following Q&A responses for additional risk factors. Return JSON with keys score (0-100), rationale, and next_steps.\n\n{data}"
    ),
}
