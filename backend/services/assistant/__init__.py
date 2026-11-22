"""Decision-Intel Admission Assistant.

A grounded chatbot: every fact it states comes from the project's database,
the trained model's metadata, the stored SHAP explanations, or the curated
knowledge base in knowledge.py. An optional LLM layer (llm.py) may rephrase a
grounded answer but is never allowed to add facts.

This package deliberately imports nothing at package level, so that importing
it (for example during test discovery) never opens the application database.
"""
