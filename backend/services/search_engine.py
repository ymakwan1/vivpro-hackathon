class SearchEngine:
    def __init__(self, es_client):
        self.es = es_client
        self.index = "clinical_trials_es"

    def execute(self, entities):
        must_clauses = []

        #condition search
        if entities.get("condition"):
            must_clauses.append({
                "multi_match": {
                    "query": entities["condition"],
                    "fields": ["brief_title", "conditions", "official_title"]
                }
            })

        #exact filters
        if entities.get("phase"):
            must_clauses.append({"term": {"phase": entities["phase"]}})
        
        if entities.get("overall_status"):
            must_clauses.append({"term": {"overall_status": entities["overall_status"]}})

        #nested search
        if entities.get("city"):
            must_clauses.append({
                "nested": {
                    "path": "facilities",
                    "query": {
                        "match": { "facilities.city": entities["city"] }
                    }
                }
            })

        query = {"query": {"bool": {"must": must_clauses}}}
        return self.es.search(index=self.index, body=query)