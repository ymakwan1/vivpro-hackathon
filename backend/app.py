from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from services.brain import QueryBrain
from services.search_engine import SearchEngine

app = Flask(__name__)
es = Elasticsearch("http://localhost:9200")
brain = QueryBrain()
engine = SearchEngine(es)

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