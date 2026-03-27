# Face Search on Video MVP

A system to index faces from videos and search for them using a query image.

## 1. Setup

Install dependencies using [uv](https://github.com/astral-sh/uv):
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 2. Prepare Data

1.  **Videos**: Place your `.mp4` or `.avi` files in `data/videos`.
    - Example: `data/videos/meeting_recording.mp4`
2.  **Index Output**: The script will create `data/index/` to store the FAISS index.

## 3. Run Offline Processing

Run the processing script to detect faces and build the index.
**Note**: The first run will download InsightFace models (~300MB).

```bash
uv run scripts/process_videos.py
```

Output:
```text
Processing data/videos/test.mp4...
100%|██████████| 1500/1500 [00:45<00:00, 33.15it/s]
Processing complete. Index saved.
```

## 4. Run Search API

Start the FastAPI server:

```bash
uv run uvicorn app.api.main:app --reload
```

## 5. Test with Swagger UI

1.  Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
2.  Go to `POST /search`.
3.  Click **Try it out**.
4.  Upload an image of a person you want to find.
5.  Execute.

**Response Example**:
```json
{
  "results": [
    {
      "video_path": "data/videos/test.mp4",
      "timestamp": 12.5,
      "frame_idx": 375,
      "bbox": [100, 200, 150, 250],
      "det_score": 0.85,
      "score": 0.65
    }
  ]
}
```