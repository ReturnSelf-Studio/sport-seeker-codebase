import { useState } from 'react'

function SearchInput({ onSearch, disabled, mode }) {
  const [preview, setPreview] = useState(null)
  const [text, setText] = useState('')

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setPreview(URL.createObjectURL(file))
      // Immediate search on file select? Or wait for button?
      // Previous behavior was immediate. But for Bib we might want generic "Search" button if using text.
      // Let's keep immediate for file if text is empty? 
      // Actually, let's change to a submission model or just trigger on file select as before, 
      // and separate trigger for text.
      
      onSearch({ file: file, text: text })
    }
  }

  const handleTextSearch = (e) => {
      e.preventDefault()
      if (text.trim()) {
          onSearch({ text: text, file: null })
      }
  }

  // If mode changes, clear preview/text? Maybe.
  
  return (
    <div className="search-box">
      <div className="input-group">
        {mode === 'bib' && (
            <div className="text-search">
                <input 
                    type="text" 
                    placeholder="Enter Bib Number" 
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    disabled={disabled}
                    onKeyDown={(e) => e.key === 'Enter' && handleTextSearch(e)}
                />
                <button onClick={handleTextSearch} disabled={disabled || !text}>
                    Search Text
                </button>
            </div>
        )}
      
        {mode !== 'bib' && (
        <div className="file-upload">
          <input 
            type="file" 
            accept="image/*" 
            onChange={handleFileChange} 
            disabled={disabled}
            id="fileInput"
            style={{ display: 'none' }}
          />
          <label htmlFor="fileInput" className="upload-btn">
            {preview ? 'Change Image' : `Upload ${mode === 'face' ? 'Face' : 'Bib'} Image`}
          </label>
        </div>
        )}
      </div>
      
      {preview && (
        <div className="preview-container">
            <img src={preview} alt="Query" className="query-preview" />
        </div>
      )}
    </div>
  )
}

export default SearchInput
