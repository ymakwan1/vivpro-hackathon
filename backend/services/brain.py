import json
import boto3
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryBrain:
    def __init__(self):
        try:
            self.bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
            self.bedrock_available = True
        except Exception as e:
            logger.warning(f"Bedrock client initialization failed: {e}. Falling back to regex extraction.")
            self.bedrock_available = False

    def extract_entities(self, user_query):
        prompt = f"""
        Extract clinical trial search parameters from this query: "{user_query}"
        Return ONLY a JSON object with no additional text.
        
        IMPORTANT RULES:
        
        Status Mapping (use exact uppercase):
        - "open" or "active" or "recruiting" → "RECRUITING"
        - "not yet recruiting" → "NOT_YET_RECRUITING"
        - "active but not recruiting" → "ACTIVE_NOT_RECRUITING"
        - "completed" or "finished" → "COMPLETED"
        - "suspended" → "SUSPENDED"
        - "withdrawn" → "WITHDRAWN"
        Always return status in UPPERCASE.
        
        Phase Mapping:
        - "Phase 1" or "Phase I" or "Phase 1a/1b" → "PHASE1"
        - "Phase 2" or "Phase II" or "Phase 2a/2b" → "PHASE2"
        - "Phase 3" or "Phase III" → "PHASE3"
        - "Phase 4" or "Phase IV" → "PHASE4"
        Always return phase in UPPERCASE.
        
        Study Type:
        - "interventional" or "treatment" or "experimental" → "INTERVENTIONAL"
        - "observational" or "observational study" → "OBSERVATIONAL"
        
        Intervention Type:
        - "drug" or "medication" or "pharmaceutical" → "DRUG"
        - "device" or "medical device" → "DEVICE"
        - "behavioral" or "lifestyle" → "BEHAVIORAL"
        - "procedure" or "surgery" → "PROCEDURE"
        
        Primary Purpose:
        - "treatment" or "therapeutic" → "TREATMENT"
        - "prevention" or "preventive" → "PREVENTION"
        - "diagnostic" or "diagnosis" → "DIAGNOSTIC"
        - "screening" → "SCREENING"
        - "supportive care" → "SUPPORTIVE"
        
        Masking/Blinding:
        - "open-label" or "open label" → "OPEN"
        - "single blind" or "single-blind" → "SINGLE"
        - "double blind" or "double-blind" → "DOUBLE"
        - "triple blind" or "triple-blind" → "TRIPLE"
        - "quadruple blind" or "quadruple-blind" → "QUADRUPLE"
        
        Age:
        - Extract minimum age as a number (e.g., "18 years" → 18)
        - Extract maximum age as a number (e.g., "65 years" → 65)
        
        Enrollment Size:
        - Less than 50 participants → "small"
        - 50 to 200 participants → "medium"
        - More than 200 participants → "large"
        
        Healthy Volunteers:
        - "accept healthy volunteers" or "healthy subjects" → true
        - "patient only" or "no healthy volunteers" → false
        
        FIELDS TO EXTRACT (only if mentioned in query):
        - overall_status: RECRUITING, NOT_YET_RECRUITING, ACTIVE_NOT_RECRUITING, COMPLETED, SUSPENDED, WITHDRAWN
        - phase: PHASE1, PHASE2, PHASE3, PHASE4
        - condition: Medical condition name (e.g., "Asthma", "Cancer", "Diabetes")
        - city: City name
        - state: State/Province name
        - country: Country name
        - sponsor: Organization or agency name
        - study_type: INTERVENTIONAL or OBSERVATIONAL
        - intervention_type: DRUG, DEVICE, BEHAVIORAL, PROCEDURE
        - primary_purpose: TREATMENT, PREVENTION, DIAGNOSTIC, SCREENING, SUPPORTIVE
        - masking: OPEN, SINGLE, DOUBLE, TRIPLE, QUADRUPLE
        - min_age: Minimum age as number
        - max_age: Maximum age as number
        - healthy_volunteers: true or false
        - enrollment_size: small, medium, or large
        
        EXAMPLES:
        
        Input: "open phase 2 drug trials for asthma in Miami"
        Output: {{"overall_status": "RECRUITING", "phase": "PHASE2", "intervention_type": "DRUG", "condition": "Asthma", "city": "Miami"}}
        
        Input: "double-blind phase 3 treatment studies for cancer in California, aged 18-65"
        Output: {{"masking": "DOUBLE", "phase": "PHASE3", "primary_purpose": "TREATMENT", "condition": "Cancer", "state": "California", "min_age": 18, "max_age": 65}}
        
        Input: "completed observational diabetes studies in New York"
        Output: {{"overall_status": "COMPLETED", "study_type": "OBSERVATIONAL", "condition": "Diabetes", "city": "New York"}}
        
        Input: "phase 1 device studies for heart disease accepting healthy volunteers"
        Output: {{"phase": "PHASE1", "intervention_type": "DEVICE", "condition": "Heart disease", "healthy_volunteers": true}}
        
        Input: "behavioral prevention trials with 100-150 participants"
        Output: {{"intervention_type": "BEHAVIORAL", "primary_purpose": "PREVENTION", "enrollment_size": "medium"}}
        """
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}]
        })
        
        try:
            response = self.bedrock.invoke_model(body=body, modelId='anthropic.claude-3-haiku-20240307-v1:0')
            response_body = json.loads(response.get('body').read())
            
            entities = json.loads(response_body['content'][0]['text'])
            
            # Clean up extracted entities - ensure they match expected format
            if "state" in entities and "city" not in entities:
                # If state was extracted, keep it as state (search_engine handles it)
                pass
            
            return entities
            
        except Exception as e:
            print(f"LLM Error: {e}")
            # Return at least the original query as a fallback condition
            return {"condition": user_query}