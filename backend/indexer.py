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
                "brief_title": {"type": "text", "analyzer": "standard"},
                "official_title": {"type": "text", "analyzer": "standard"},
                "overall_status": {"type": "keyword"},
                "phase": {"type": "keyword"},
                "conditions": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "enrollment": {"type": "long"}, 
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
                "start_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd||epoch_millis"},
                "completion_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd||epoch_millis"}
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

        e_val = source.get("enrollment")
        if e_val is not None:
            try:
                source["enrollment"] = int(float(str(e_val).replace(',', '')))
            except (ValueError, TypeError):
                source["enrollment"] = None

        for d_field in ["start_date", "completion_date"]:
            val = source.get(d_field)
            if not val or str(val).upper() in ["NA", "NULL", "UNKNOWN", ""]:
                source.pop(d_field, None)

        if isinstance(source.get("conditions"), list):
            source["conditions"] = [
                c.get("name", str(c)) if isinstance(c, dict) else str(c) 
                for c in source["conditions"]
            ]

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
        es.indices.delete(index=INDEX_NAME)

    es.indices.create(index=INDEX_NAME, body=get_mapping())

    success, errors = helpers.bulk(es, generate_actions(), raise_on_error=False)
    
    if errors:
        logger.error(f"Failed to index {len(errors)} docs.")
    
    logger.info(f"Successfully indexed {success} trials.")

if __name__ == "__main__":
    index_data()