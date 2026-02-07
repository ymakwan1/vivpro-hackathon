# class SearchEngine:
#     def __init__(self, es_client):
#         self.es = es_client
#         self.index = "clinical_trials_es"

#     def execute(self, entities):
#         must_clauses = []

#         #condition search
#         if entities.get("condition"):
#             must_clauses.append({
#                 "multi_match": {
#                     "query": entities["condition"],
#                     "fields": ["brief_title", "conditions", "official_title"]
#                 }
#             })

#         #exact filters
#         if entities.get("phase"):
#             must_clauses.append({"term": {"phase": entities["phase"]}})
        
#         if entities.get("overall_status"):
#             must_clauses.append({"term": {"overall_status": entities["overall_status"]}})

#         #nested search
#         if entities.get("city"):
#             must_clauses.append({
#                 "nested": {
#                     "path": "facilities",
#                     "query": {
#                         "match": { "facilities.city": entities["city"] }
#                     }
#                 }
#             })

#         query = {"query": {"bool": {"must": must_clauses}}}
#         print(query)
#         return self.es.search(index=self.index, body=query)
class SearchEngine:
    def __init__(self, es_client):
        self.es = es_client
        self.index = "clinical_trials_es"

    def execute(self, entities):
        must_clauses = []

        if entities.get("condition"):
            must_clauses.append({
                "multi_match": {
                    "query": entities["condition"],
                    "fields": ["brief_title", "conditions", "conditions.name", "official_title"],
                    "fuzziness": "AUTO" 
                }
            })

        if entities.get("phase"):
            must_clauses.append({
                "query_string": {
                    "default_field": "phase",
                    "query": f"*{entities['phase']}*",
                    "analyze_wildcard": True
                }
            })
        
        if entities.get("overall_status"):
            must_clauses.append({
                "query_string": {
                    "default_field": "overall_status",
                    "query": f"*{entities['overall_status']}*"
                }
            })

        if entities.get("city"):
            must_clauses.append({
                "nested": {
                    "path": "facilities",
                    "score_mode": "max",
                    "query": {
                        "match": { "facilities.city": entities["city"] }
                    }
                }
            })
        
        if entities.get("condition") or entities.get("keyword"):
            must_clauses.append({
                "multi_match": {
                    "query": entities.get("condition") or entities.get("keyword"),
                    "fields": [
                        "brief_title", 
                        "official_title", 
                        "conditions", 
                        "sponsors.name"
                    ],
                    "fuzziness": "AUTO"
                }
            })

        if entities.get("sponsor"):
            must_clauses.append({
                "multi_match": {
                    "query": entities["sponsor"],
                    "fields": [
                        "sponsors.name",         
                        "sponsors.agency_class"
                    ],
                    "operator": "and"
                }
            })

        query = {"query": {"bool": {"must": must_clauses}}}
        return self.es.search(index=self.index, body=query)