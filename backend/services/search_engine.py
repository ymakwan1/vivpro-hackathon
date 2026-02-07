class SearchEngine:
    def __init__(self, es_client):
        self.es = es_client
        self.index = "clinical_trials_es"

    def execute(self, entities):
        must_clauses = []
        search_text = entities.get("condition") or entities.get("keyword")
        if search_text:
            must_clauses.append({
                "multi_match": {
                    "query": search_text,
                    "fields": ["brief_title^3", "official_title^2", "conditions"],
                    "fuzziness": "AUTO"
                }
            })

        if entities.get("phase"):
            must_clauses.append({"match": {"phase": {"query": entities["phase"]}}})
        
        if entities.get("overall_status"):
            status_val = entities["overall_status"].upper()
            must_clauses.append({
                "bool": {
                    "should": [
                        {
                            "term": { "overall_status": status_val }
                        },
                        {
                            "nested": {
                                "path": "facilities",
                                "query": {
                                    "term": { "facilities.status": status_val }
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            })

        if entities.get("city"):
            must_clauses.append({
                "nested": {
                    "path": "facilities",
                    "score_mode": "max",
                    "query": {
                        "match": { "facilities.city": {
                            "query": entities["city"], 
                            "fuzziness": "AUTO"} }
                    }
                }
            })
        if entities.get("country"):
            must_clauses.append({
                "nested": {
                    "path": "facilities",
                    "score_mode": "max",
                    "query": {
                        "match": { 
                            "facilities.country": {
                                "query": entities["country"], 
                                "fuzziness": "AUTO"
                            } 
                        }
                    }
                }
            })

        if entities.get("sponsor"):
            must_clauses.append({
                "nested": {
                    "path": "sponsors",
                    "score_mode": "avg",
                    "query": {
                        "bool": {
                            "should": [
                                { "match": { "sponsors.name": { "query": entities["sponsor"], "fuzziness": "AUTO" } } },
                                { "term": { "sponsors.agency_class": entities["sponsor"].upper() } }
                            ]
                        }
                    }
                }
            })

        query = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            }
        }
        
        return self.es.search(index=self.index, body=query)