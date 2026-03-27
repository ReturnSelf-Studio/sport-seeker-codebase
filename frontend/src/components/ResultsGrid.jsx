function ResultsGrid({ results }) {
  if (!results.length) return null

  // Group by video functionality could be added here, 
  // currently just showing flat list as per plan, but let's make it look nice.

  return (
    <div className="results-grid">
      <h2>Found Matches ({results.length})</h2>
      <div className="grid">
        {results.map((item, index) => (
          <div key={index} className="result-card">
            {/* 
                Video URL construction:
                Backend serves /data/videos at /videos
                item.video_path is like "data/videos/test.mp4"
                We need to convert to "http://localhost:8000/videos/test.mp4"
            */}
            <video 
                controls 
                src={`http://localhost:8000/videos/${item.video_path.split('/').pop()}#t=${item.timestamp}`}
                className="result-video"
            />
            <div className="result-info">
              <p><strong>Video:</strong> {item.video_path.split('/').pop()}</p>
              <p><strong>Time:</strong> {item.timestamp.toFixed(2)}s</p>
              <p><strong>Score:</strong> {item.score.toFixed(3)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ResultsGrid
