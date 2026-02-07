import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [interpretation, setInterpretation] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    
    try {
      const response = await axios.get(`http://localhost:5003/search?q=${query}`);
      setResults(response.data.trials);
      setInterpretation(response.data.interpretation);
    } catch (error) {
      console.error("Search failed", error);
    }
    setLoading(false);
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Vivpro <span style={{fontWeight: '300'}}>TrialSearch</span></h1>
        <p style={styles.subtitle}>AI-Powered Clinical Trial Intelligence</p>
      </header>
      
      <form onSubmit={handleSearch} style={styles.searchBox}>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., Phase 3 melanoma trials by NIH"
          style={styles.input}
        />
        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? '...' : 'Search'}
        </button>
      </form>

      {interpretation && (
        <div style={styles.interpretation}>
          <span style={styles.label}>AI Interpretation:</span> 
          {Object.entries(interpretation).map(([key, val]) => val && (
            <div key={key} style={styles.chip}>
              {key}: <b>{val}</b>
            </div>
          ))}
        </div>
      )}

      <div style={styles.summaryBar}>
        <h2 style={styles.countText}>
          {loading ? "Analyzing data..." : `Showing ${results.length} trials`}
        </h2>
      </div>

      <div style={styles.resultsGrid}>
        {!loading && results.map((trial) => (
          <div key={trial.nct_id} style={styles.card}>
            <div style={styles.cardHeader}>
              <span style={styles.nctId}>{trial.nct_id}</span>
              <span style={styles.phaseTag}>{trial.phase || 'N/A'}</span>
            </div>
            <h3 style={styles.trialTitle}>{trial.brief_title}</h3>
            
            <div style={styles.metaRow}>
              <strong>Status:</strong> 
              <span style={{color: trial.overall_status === 'RECRUITING' ? '#28a745' : '#666'}}>
                {trial.overall_status}
              </span>
            </div>
            
            <p style={styles.conditions}>
              {Array.isArray(trial.conditions) ? trial.conditions.slice(0, 3).join(', ') : trial.conditions}
              {trial.conditions?.length > 3 && '...'}
            </p>

            <div style={styles.footer}>
              <strong>Lead:</strong> {
                Array.isArray(trial.sponsors) 
                  ? trial.sponsors.find(s => s.lead_or_collaborator === 'lead')?.name || trial.sponsors[0]?.name
                  : 'N/A'
              }
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: { 
    padding: '40px 20px', 
    maxWidth: '1000px', 
    margin: 'auto', 
    fontFamily: '"Inter", "Segoe UI", sans-serif', 
    backgroundColor: '#f4f7f9', // Light professional background
    minHeight: '100vh' 
  },
  header: { 
    textAlign: 'center', 
    marginBottom: '40px' 
  },
  title: { 
    fontSize: '2.8rem', 
    color: '#0f172a', 
    margin: 0, 
    letterSpacing: '-1px' 
  },
  subtitle: { 
    color: '#64748b', 
    marginTop: '8px', 
    fontSize: '1.1rem' 
  },
  searchBox: { 
    display: 'flex', 
    gap: '12px', 
    backgroundColor: '#ffffff', 
    padding: '12px', 
    borderRadius: '16px', 
    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
    border: '1px solid #e2e8f0'
  },
  input: { 
    flex: 1, 
    padding: '12px 18px', 
    border: 'none', 
    fontSize: '1.1rem', 
    outline: 'none',
    color: '#1e293b'
  },
  button: { 
    padding: '0 35px', 
    backgroundColor: '#2563eb', // Vibrant primary blue
    color: 'white', 
    border: 'none', 
    borderRadius: '12px', 
    cursor: 'pointer', 
    fontWeight: '600',
    transition: 'all 0.2s ease',
    boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.2)'
  },
  interpretation: { 
    marginTop: '24px', 
    display: 'flex', 
    flexWrap: 'wrap', 
    gap: '10px', 
    alignItems: 'center',
    padding: '0 10px'
  },
  label: { 
    fontSize: '0.85rem', 
    fontWeight: '700', 
    color: '#94a3b8', 
    textTransform: 'uppercase', 
    letterSpacing: '0.05em' 
  },
  chip: { 
    padding: '6px 14px', 
    backgroundColor: '#ffffff', 
    borderRadius: '8px', 
    fontSize: '0.85rem', 
    color: '#334155',
    border: '1px solid #e2e8f0',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
  },
  summaryBar: { 
    display: 'flex', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginTop: '48px', 
    padding: '0 10px 15px 10px',
    borderBottom: '2px solid #e2e8f0'
  },
  countText: { 
    fontSize: '1.2rem', 
    color: '#1e293b', 
    margin: 0,
    fontWeight: '600'
  },
  badge: { 
    padding: '6px 16px', 
    borderRadius: '99px', 
    fontSize: '0.8rem', 
    fontWeight: '600', 
    border: '1px solid transparent'
  },
  resultsGrid: { 
    marginTop: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px'
  },
  card: { 
    backgroundColor: '#ffffff', 
    border: '1px solid #e2e8f0', 
    padding: '24px', 
    borderRadius: '16px', 
    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    cursor: 'default'
  },
  cardHeader: { 
    display: 'flex', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: '14px' 
  },
  nctId: { 
    fontSize: '0.85rem', 
    color: '#64748b', 
    fontFamily: 'monospace',
    backgroundColor: '#f1f5f9',
    padding: '2px 8px',
    borderRadius: '4px'
  },
  phaseTag: { 
    backgroundColor: '#dcfce7', 
    color: '#166534', 
    padding: '4px 10px', 
    borderRadius: '6px', 
    fontSize: '0.7rem', 
    fontWeight: '800',
    textTransform: 'uppercase'
  },
  trialTitle: { 
    fontSize: '1.25rem', 
    color: '#0f172a', 
    margin: '0 0 16px 0', 
    lineHeight: '1.5',
    fontWeight: '700'
  },
  metaRow: { 
    fontSize: '0.95rem', 
    marginBottom: '10px',
    color: '#475569' 
  },
  conditions: { 
    fontSize: '0.9rem', 
    color: '#64748b', 
    backgroundColor: '#f8fafc',
    padding: '10px',
    borderRadius: '8px',
    marginBottom: '20px',
    borderLeft: '4px solid #cbd5e1'
  },
  footer: { 
    paddingTop: '18px', 
    borderTop: '1px solid #f1f5f9', 
    fontSize: '0.85rem', 
    color: '#475569',
    display: 'flex',
    justifyContent: 'space-between'
  }
};

export default App;