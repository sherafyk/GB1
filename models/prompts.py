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
}
