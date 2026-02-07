import json
import boto3

class QueryBrain:
    def __init__(self):
        self.bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

    def extract_entities(self, user_query):
        prompt = f"""
        Extract clinical trial search parameters from this query: "{user_query}"
        Return ONLY a JSON object. 
        
        Rules:
        - When a user mentions 'open' or 'active' trials, map the overall_status to RECRUITING. If they mention 'completed' or 'finished', map it to COMPLETED. Always return the status in uppercase to match the dataset. Also match for other synonyms 
        - phase: Map "Phase 1" to "PHASE1", "Phase 2" to "PHASE2", etc.
        - city: Extract the city name if present.
        - condition: Extract the medical condition (e.g., Asthma, Cancer).
        - country: Extract country names (e.g., "USA", "France").
        - sponsor: Extract the name of the organization or agency (e.g., NIH, Pfizer).
        Note: "open" can also be open-ended as overall status in NOT RECRUITING, but some facilities can be recruitng in the trial.
        Example: "open phase 3 trials in Miami for Asthma"
        Output: {{"overall_status": "RECRUITING", "phase": "PHASE3", "city": "Miami", "condition": "Asthma"}}
        """
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}]
        })
        
        try:
            response = self.bedrock.invoke_model(body=body, modelId='anthropic.claude-3-haiku-20240307-v1:0')
            response_body = json.loads(response.get('body').read())
            
            return json.loads(response_body['content'][0]['text'])
        except Exception as e:
            print(f"LLM Error: {e}")
            
            return {"condition": user_query}