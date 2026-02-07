import json
import logging
from elasticsearch import Elasticsearch, helpers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ES_HOST = "http://localhost:9200"
INDEX_NAME = "clinical_trials_es"
DATA_PATH = "data/clinical_trials.json" 

es = Elasticsearch(
    "http://localhost:9200",
    basic_auth=None,
    verify_certs=False,
    ssl_show_warn=False
)

def get_mapping():
    return {
        "mappings": {
            "properties": {
                "nct_id": {"type": "keyword"},
                "brief_title": {"type": "text"},
                "official_title": {"type": "text"},
                "overall_status": {"type": "keyword"},
                "phase": {"type": "keyword"},
                "conditions": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "intervention_names": {"type": "text"},
                "enrollment": {"type": "integer"},
                "facilities": {
                    "type": "nested", 
                    "properties": {
                        "name": {"type": "text"},
                        "city": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "state": {"type": "keyword"},
                        "zip": {"type": "keyword"},
                        "country": {"type": "keyword"},
                        "status": {"type": "keyword"}
                    }
                },
                "gender": {"type": "keyword"},
                "minimum_age": {"type": "keyword"},
                "maximum_age": {"type": "keyword"},
                "start_date": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
                "completion_date": {"type": "date", "format": "strict_date_optional_time||epoch_millis"}
            }
        }
    }

def index_data():
    if not es.ping():
        logger.error("Could not connect to Elasticsearch.")
        return

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
    
    es.indices.create(index=INDEX_NAME, body=get_mapping())
    logger.info("Index created with nested 'facilities' mapping.")

    try:
        with open(DATA_PATH, 'r') as f:
            raw_data = json.load(f)
        
        def generate_actions():
            for trial in raw_data:
                source = trial.copy()
                for d_field in ["start_date", "completion_date"]:
                    if not source.get(d_field):
                        source.pop(d_field, None)
                
                yield {
                    "_index": INDEX_NAME,
                    "_id": trial.get("nct_id"),
                    "_source": source
                }

        success, _ = helpers.bulk(es, generate_actions())
        logger.info(f"Successfully indexed {success} trials.")

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")

if __name__ == "__main__":
    index_data()