from flask import Flask, request, jsonify
from flask_cors import CORS
from elasticsearch import Elasticsearch
from services.brain import QueryBrain
from services.search_engine import SearchEngine

app = Flask(__name__)
CORS(app)
es = Elasticsearch("http://localhost:9200")
brain = QueryBrain()
engine = SearchEngine(es)

@app.route('/audit', methods=['POST'])
def audit_data():
    entities = request.json 
    
    try:
        with open('clinical_trials.json', 'r') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "Source file not found"}), 500

    matches = []

    for trial in raw_data:
        is_match = True
        
        
        for key, value in entities.items():
            if not value: continue  
            
            val_lower = str(value).lower()

            
            if key == "sponsor":
                sponsors = trial.get('sponsors', [])
                
                sponsor_match = any(
                    val_lower in s.get('name', '').lower() or 
                    val_lower == s.get('agency_class', '').lower() 
                    for s in sponsors
                )
                if not sponsor_match:
                    is_match = False

            
            elif key == "condition":
                conditions_list = [str(c).lower() for c in trial.get('conditions', [])]
                
                title = trial.get('brief_title', '').lower()
                if not any(val_lower in c for c in conditions_list) and val_lower not in title:
                    is_match = False

            
            elif key == "city":
                facilities = trial.get('facilities', [])
                city_match = any(val_lower == f.get('city', '').lower() for f in facilities)
                if not city_match:
                    is_match = False

            
            else:
                
                if str(trial.get(key, '')).lower() != val_lower:
                    is_match = False
            
            
            if not is_match:
                break

        if is_match:
            matches.append(trial.get('nct_id'))

    return jsonify({
        "audit_count": len(matches),
        "total_source_records": len(raw_data),
        "verified_ids": matches[:10]  
    })
@app.route('/search', methods=['GET'])
def search():
    user_query = request.args.get('q', '')
    print(user_query)
    
    entities = brain.extract_entities(user_query)
    print(f"Entities: {entities}")
    results = engine.execute(entities)
    print(f"Results: {results}")
    
    return jsonify({
        "interpretation": entities,
        "trials": [hit['_source'] for hit in results['hits']['hits']],
        "total": results['hits']['total']['value']
    })

if __name__ == '__main__':
    app.run(debug=True, port=5003)