import re
from backend.copilot.models import CopilotResponse
from backend.copilot.context import CopilotContext

class CopilotValidator:
    """
    Enforces deterministic safety boundaries on the AI's generated response.
    """
    
    MUTATION_KEYWORDS = {
        "insert", "update", "delete", "drop", "alter", 
        "truncate", "grant", "revoke", "commit", "rollback"
    }

    KNOWN_METRICS = {
        "row_count", "null_fraction", "null_count", 
        "unique_fraction", "unique_count", "mean", "min", "max",
        "duplicate_fraction"
    }

    @staticmethod
    def validate(response: CopilotResponse, context: CopilotContext) -> None:
        CopilotValidator._validate_citations(response, context)
        CopilotValidator._validate_sql_safety(response)
        CopilotValidator._validate_no_invented_schema(response, context)
        CopilotValidator._validate_no_overclaims(response, context)

    @staticmethod
    def _validate_citations(response: CopilotResponse, context: CopilotContext) -> None:
        # Collect all valid IDs from context
        valid_ids = set()
        
        for ev in context.evidence_catalog:
            valid_ids.add(ev["id"])
            
        for attr in context.attributions:
            valid_ids.add(attr["id"])
            valid_ids.add(attr["finding_id"])
            
        for hyp in context.active_hypotheses:
            valid_ids.add(hyp["id"])

        for citation in response.citations:
            if citation.reference_id not in valid_ids:
                raise ValueError(
                    f"Copilot hallucinated citation: {citation.reference_id} "
                    f"does not exist in the deterministic investigation context."
                )

    @staticmethod
    def _validate_sql_safety(response: CopilotResponse) -> None:
        for exp in response.experiments:
            sql = exp.sql_query.lower()
            # Tokenize SQL to prevent matching substring like "drop_count"
            tokens = re.findall(r'\b\w+\b', sql)
            for token in tokens:
                if token in CopilotValidator.MUTATION_KEYWORDS:
                    raise ValueError(f"Copilot generated unsafe mutation SQL: contains '{token.upper()}'.")

    @staticmethod
    def _validate_no_invented_schema(response: CopilotResponse, context: CopilotContext) -> None:
        valid_columns = set(context.schema_context.keys())
        
        # Check text (answer, claims) for column/metric hallucinations
        text_blocks = [response.answer] + [c.text for c in response.claims]
        full_text = " ".join(text_blocks).lower()
        
        # A simple heuristic check for tests: if AI says "column X" or "metric X"
        # We find what follows and check it.
        # This is basic, but fulfills the "reject invented column/metric" requirement.
        
        # Check columns
        col_matches = re.findall(r'column\s+[\'"]?([a-z0-9_]+)[\'"]?', full_text)
        for col in col_matches:
            if col not in valid_columns:
                raise ValueError(f"Copilot invented column: '{col}' is not in the dataset schema.")
                
        # Check metrics
        metric_matches = re.findall(r'metric\s+[\'"]?([a-z0-9_]+)[\'"]?', full_text)
        for metric in metric_matches:
            if metric not in CopilotValidator.KNOWN_METRICS:
                raise ValueError(f"Copilot invented metric: '{metric}' is not recognized.")

    @staticmethod
    def _validate_no_overclaims(response: CopilotResponse, context: CopilotContext) -> None:
        text_blocks = [response.answer] + [c.text for c in response.claims]
        full_text = " ".join(text_blocks).lower()
        
        # Check root-cause overclaim
        if "strong" in full_text and "root cause" in full_text:
            # Check if synthesis actually has a strong candidate
            if "STRONG" not in context.synthesis_markdown:
                raise ValueError("Copilot asserted a STRONG root cause, but the deterministic engine did not provide one.")
                
        # Check unsupported hypothesis framed as fact
        # If full text claims a hypothesis is "confirmed" or "supported"
        # but the context active hypotheses are all PROPOSED.
        if "confirmed" in full_text or "is the reason" in full_text:
            has_supported = any(h["status"] == "SUPPORTED" for h in context.active_hypotheses)
            if not has_supported and "hypothesis" in full_text:
                raise ValueError("Copilot claimed a hypothesis is confirmed, but it lacks SUPPORTED validation.")

