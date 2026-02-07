import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [interpretation, setInterpretation] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:5003/search?q=${query}`);
      console.log(response);
      setResults(response.data.trials);
      setInterpretation(response.data.interpretation);
    } catch (error) {
      console.error("Search failed", error);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: 'auto', fontFamily: 'Arial' }}>
      <h1>Intelligent Clinical Trials Search</h1>
      
      {/* 1. Search Bar [cite: 56] */}
      <form onSubmit={handleSearch}>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., Phase 3 lung cancer trials in USA"
          style={{ width: '80%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <button type="submit" style={{ padding: '10px 20px', marginLeft: '10px' }}>Search</button>
      </form>

      {/* 2. Interpretation Display [cite: 60] */}
      {interpretation && (
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#e9ecef', borderRadius: '5px' }}>
          <strong>We understood:</strong> 
          {Object.entries(interpretation).map(([key, val]) => val && (
            <span key={key} style={{ marginLeft: '10px', color: '#495057' }}>
              {key.charAt(0).toUpperCase() + key.slice(1)}: <b>{val}</b>
            </span>
          ))}
        </div>
      )}
      
    <div className="results-summary" style={{ margin: '20px 0', borderBottom: '2px solid #eee' }}>
      <h2 style={{ fontSize: '1.2rem' }}>
        {loading ? "Searching..." : (
          <>
            Found <strong>{results.length}</strong> 
            {results.length === 1 ? ' trial' : ' trials'} for 
            <span style={{ color: '#007bff' }}> "{query}"</span>
          </>
        )}
      </h2>
    </div>

      {/* 3. Results List  */}
      <div style={{ marginTop: '30px' }}>
        {loading ? <p>Searching...</p> : results.map((trial) => (
          <div key={trial.nct_id} style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px', marginBottom: '15px' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>{trial.brief_title || trial.official_title}</h3>
            <div style={{ fontSize: '14px', color: '#555' }}>
              <p><strong>Status:</strong> {trial.overall_status}</p>
              <p><strong>Conditions:</strong> {Array.isArray(trial.conditions) ? trial.conditions.join(', ') : trial.conditions}</p>
              <p><strong>Phase:</strong> {trial.phase}</p>
              <p style={{ fontSize: '14px', color: '#666' }}>
                <strong>Sponsor:</strong> {
                  // Check if sponsors is an array and find the lead
                  Array.isArray(trial.sponsors) 
                    ? trial.sponsors.find(s => s.lead_or_collaborator === 'lead')?.name || trial.sponsors[0]?.name
                    : 'N/A'
                }
                {/* Optional: Show number of collaborators if they exist */}
                {trial.sponsors?.length > 1 && ` (+${trial.sponsors.length - 1} collaborators)`}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;