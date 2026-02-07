import json
import logging
from pathlib import Path
from elasticsearch import Elasticsearch, helpers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ES_HOST = "http://localhost:9200"
INDEX_NAME = "clinical_trials_es"
DATA_PATH = Path(__file__).resolve().parent / "data" / "clinical_trials.json"

es = Elasticsearch(ES_HOST, request_timeout=60)

def get_mapping():
    return {
        "mappings": {
            "properties": {
            
                "nct_id": {"type": "keyword"},
                "acronym": {"type": "keyword"},
                "source": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                
                "brief_title": {"type": "text", "analyzer": "standard"},
                "official_title": {"type": "text", "analyzer": "standard"},
                
                "overall_status": {"type": "keyword"},
                "phase": {"type": "keyword"},
                
                "study_type": {"type": "keyword"},
                "primary_purpose": {"type": "keyword"},
                "allocation": {"type": "keyword"},
                "intervention_model": {"type": "keyword"},
                "intervention_model_description": {"type": "text"},
                
                "masking": {"type": "keyword"},
                "subject_masked": {"type": "boolean"},
                "caregiver_masked": {"type": "boolean"},
                "investigator_masked": {"type": "boolean"},
                "outcomes_assessor_masked": {"type": "boolean"},
                
                "enrollment": {"type": "long"}, 
                "minimum_age": {"type": "integer"},
                "maximum_age": {"type": "integer"},
                "gender": {"type": "keyword"},
                "healthy_volunteers": {"type": "boolean"},
                
                "number_of_arms": {"type": "integer"},
                "number_of_groups": {"type": "integer"},
                
                "start_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd||epoch_millis"},
                "completion_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd||epoch_millis"},
                "primary_completion_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd||epoch_millis"},
                
                "has_results": {"type": "boolean"},
                
                "conditions": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                
                "sponsors": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "agency_class": {"type": "keyword"},
                        "lead_or_collaborator": {"type": "keyword"}
                    }
                },
                
                "facilities": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "text"},
                        "status": {"type": "keyword"},
                        "city": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "state": {"type": "keyword"},
                        "country": {"type": "keyword"}
                    }
                },
                
                "interventions": {
                    "type": "nested",
                    "properties": {
                        "id": {"type": "keyword"},
                        "intervention_type": {"type": "keyword"},
                        "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "description": {"type": "text"}
                    }
                },
                
                "design_outcomes": {
                    "type": "nested",
                    "properties": {
                        "outcome_type": {"type": "keyword"},
                        "measure": {"type": "text"},
                        "time_frame": {"type": "text"},
                        "description": {"type": "text"}
                    }
                },
                
                "design_groups": {
                    "type": "nested",
                    "properties": {
                        "id": {"type": "keyword"},
                        "group_type": {"type": "keyword"},
                        "title": {"type": "text"},
                        "description": {"type": "text"}
                    }
                }
            }
        }
    }

def generate_actions():
    if not DATA_PATH.exists():
        logger.error(f"File not found at {DATA_PATH}")
        return

    with DATA_PATH.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    for trial in raw_data:
        source = trial.copy()

        hv_val = str(source.get("healthy_volunteers", "")).upper()
        if "ACCEPT" in hv_val or hv_val == "YES" or hv_val == "TRUE":
            source["healthy_volunteers"] = True
        elif "NA" in hv_val or not hv_val:
            source.pop("healthy_volunteers", None)
        else:
            source["healthy_volunteers"] = False
        e_val = source.get("enrollment")
        if e_val is not None:
            try:
                source["enrollment"] = int(float(str(e_val).replace(',', '')))
            except (ValueError, TypeError):
                source["enrollment"] = None

        for age_field in ["minimum_age", "maximum_age"]:
            age_str = source.get(age_field, "")
            if age_str and age_str != "NA" and str(age_str).upper() not in ["UNKNOWN", "NULL", ""]:
                try:
                    age_num = int(''.join(filter(str.isdigit, str(age_str))))
                    source[age_field] = age_num
                except (ValueError, TypeError):
                    source.pop(age_field, None)
            else:
                source.pop(age_field, None)

        for num_field in ["number_of_arms", "number_of_groups"]:
            val = source.get(num_field)
            if val is not None and val not in ["NA", "None", "null", ""]:
                try:
                    source[num_field] = int(str(val))
                except (ValueError, TypeError):
                    source.pop(num_field, None)
            else:
                source.pop(num_field, None)

        for bool_field in ["subject_masked", "caregiver_masked", "investigator_masked", 
                          "outcomes_assessor_masked", "has_results"]:
            val = source.get(bool_field)
            if val is not None:
                if isinstance(val, bool):
                    source[bool_field] = val
                elif isinstance(val, (int, float)):
                    source[bool_field] = bool(val)
                elif isinstance(val, str):
                    source[bool_field] = val.lower() in ["true", "yes", "1"]
                else:
                    source.pop(bool_field, None)
            else:
                source.pop(bool_field, None)

        for d_field in ["start_date", "completion_date", "primary_completion_date"]:
            val = source.get(d_field)
            if not val or str(val).upper() in ["NA", "NULL", "UNKNOWN", ""]:
                source.pop(d_field, None)

        if isinstance(source.get("conditions"), list):
            source["conditions"] = [
                c.get("name", str(c)) if isinstance(c, dict) else str(c) 
                for c in source["conditions"]
            ]
            
        fields_to_keep = {
            "nct_id", "acronym", "source",
            "brief_title", "official_title",
            "overall_status", "phase",
            "study_type", "primary_purpose", "allocation", "intervention_model", "intervention_model_description",
            "masking", "subject_masked", "caregiver_masked", "investigator_masked", "outcomes_assessor_masked",
            "enrollment", "minimum_age", "maximum_age", "gender", "healthy_volunteers",
            "number_of_arms", "number_of_groups",
            "start_date", "completion_date", "primary_completion_date",
            "has_results",
            "conditions", "sponsors", "facilities", "interventions", "design_outcomes", "design_groups"
        }
        
        source = {k: v for k, v in source.items() if k in fields_to_keep}

        yield {
            "_index": INDEX_NAME,
            "_id": trial.get("nct_id"),
            "_source": source,
        }

def index_data():
    if not es.ping():
        logger.error("ES Connection Failed. Is Elasticsearch running?")
        return

    if es.indices.exists(index=INDEX_NAME):
        logger.info(f"Deleting existing index: {INDEX_NAME}")
        es.indices.delete(index=INDEX_NAME)

    logger.info(f"Creating index: {INDEX_NAME}")
    es.indices.create(index=INDEX_NAME, body=get_mapping())

    logger.info("Starting bulk indexing...")
    success, errors = helpers.bulk(es, generate_actions(), raise_on_error=False)

    if errors:
        logger.error(f"Failed to index {len(errors)} docs.")
        for i, error in enumerate(errors[:5]):
            error_details = error.get('index', {}).get('error', {})
            reason = error_details.get('reason')
            doc_id = error.get('index', {}).get('_id')
            logger.error(f"Doc {doc_id} failed: {reason}")
    
    logger.info(f"Successfully indexed {success} trials.")
    logger.info(f"Total results (success + errors): {success + len(errors)}")

if __name__ == "__main__":
    index_data()