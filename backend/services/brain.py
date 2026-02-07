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
        - overall_status: Map "open" or "available" to "RECRUITING". 
        - phase: Map "Phase 1" to "PHASE1", "Phase 2" to "PHASE2", etc.
        - city: Extract the city name if present.
        - condition: Extract the medical condition (e.g., Asthma, Cancer).

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