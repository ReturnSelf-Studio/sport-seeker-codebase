import { useState } from 'react'
import SearchInput from './components/SearchInput'
import ResultsGrid from './components/ResultsGrid'
import './App.css'

function App() {
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchMode, setSearchMode] = useState('face') // 'face' or 'bib'

  const handleSearch = async (searchData) => {
    setIsLoading(true)
    setError(null)
    setResults([])

    const formData = new FormData()
    formData.append('type', searchMode)
    
    if (searchData.file) {
        formData.append('file', searchData.file)
    }
    if (searchData.text) {
        formData.append('text', searchData.text)
    }

    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const data = await response.json()
      setResults(data.results)
    } catch (err) {
        console.error(err)
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Face Search on Video</h1>
      
      <div className="mode-toggle">
        <button 
            className={searchMode === 'face' ? 'active' : ''} 
            onClick={() => setSearchMode('face')}
        >
            Face Search
        </button>
        <button 
            className={searchMode === 'bib' ? 'active' : ''} 
            onClick={() => setSearchMode('bib')}
        >
            Bib Search
        </button>
      </div>

      <SearchInput 
        onSearch={handleSearch} 
        disabled={isLoading} 
        mode={searchMode}
      />
      
      {isLoading && <p>Searching...</p>}
      {error && <p className="error">{error}</p>}
      
      <ResultsGrid results={results} />
    </div>
  )
}

export default App
