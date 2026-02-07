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
        
        if entities.get("state"):
            must_clauses.append({
                "nested": {
                    "path": "facilities",
                    "score_mode": "max",
                    "query": {
                        "match": { "facilities.state": {
                            "query": entities["state"], 
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

        if entities.get("study_type"):
            must_clauses.append({
                "term": { "study_type": entities["study_type"].upper() }
            })

        if entities.get("intervention_type"):
            must_clauses.append({
                "nested": {
                    "path": "interventions",
                    "query": {
                        "term": { "interventions.intervention_type": entities["intervention_type"].upper() }
                    }
                }
            })

        if entities.get("primary_purpose"):
            must_clauses.append({
                "term": { "primary_purpose": entities["primary_purpose"].upper() }
            })

       
        if entities.get("masking"):
            must_clauses.append({
                "term": { "masking": entities["masking"].upper() }
            })

        if entities.get("min_age"):
            try:
                min_age = int(entities["min_age"])
                must_clauses.append({
                    "range": {
                        "maximum_age": { "gte": min_age }
                    }
                })
            except (ValueError, TypeError):
                pass

        if entities.get("max_age"):
            try:
                max_age = int(entities["max_age"])
                must_clauses.append({
                    "range": {
                        "minimum_age": { "lte": max_age }
                    }
                })
            except (ValueError, TypeError):
                pass

        if "healthy_volunteers" in entities:
            must_clauses.append({
                "term": { "healthy_volunteers": entities["healthy_volunteers"] }
            })

        if entities.get("enrollment_size"):
            enrollment_ranges = {
                "small": {"to": 50},
                "medium": {"gte": 50, "lte": 200},
                "large": {"gte": 200}
            }
            size = entities["enrollment_size"].lower()
            if size in enrollment_ranges:
                must_clauses.append({
                    "range": {
                        "enrollment": enrollment_ranges[size]
                    }
                })

        query = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            },
            "size": 1000
        }
        
        return self.es.search(index=self.index, body=query)