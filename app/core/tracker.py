import numpy as np
from typing import List, Dict, Tuple, Optional
import uuid

class FaceTracker:
    def __init__(self, similarity_threshold: float = 0.6, max_missed_frames: int = 2):
        self.active_tracks = []
        self.similarity_threshold = similarity_threshold
        self.max_missed_frames = max_missed_frames

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return np.dot(emb1, emb2) / (norm1 * norm2)

    def update(self, faces: List[Dict], frame_idx: int, timestamp: float) -> List[Dict]:
        """
        Update tracks with new faces.
        Returns a list of 'finished' tracks that have been lost/pruned.
        """
        finished_tracks = []

        if not faces:
            for track in self.active_tracks:
                track['missed_frames'] += 1
        else:

            matches = [] # (track_idx, face_idx, score)

            used_tracks = set()
            used_faces = set()

            for t_idx, track in enumerate(self.active_tracks):
                track_emb = track['best_face']['embedding']
                best_score = -1.0
                best_f_idx = -1

                for f_idx, face in enumerate(faces):
                    score = self._cosine_similarity(track_emb, face['embedding'])
                    if score > self.similarity_threshold:
                        matches.append((t_idx, f_idx, score))

            matches.sort(key=lambda x: x[2], reverse=True)

            for t_idx, f_idx, score in matches:
                if t_idx in used_tracks or f_idx in used_faces:
                    continue

                track = self.active_tracks[t_idx]
                face = faces[f_idx]

                track['missed_frames'] = 0
                track['last_seen_frame_idx'] = frame_idx
                track['end_timestamp'] = timestamp
                track['history'].append(face) # Optional: store history if needed

                if face['det_score'] > track['best_face']['det_score']:
                     track['best_face'] = face

                used_tracks.add(t_idx)
                used_faces.add(f_idx)

            for f_idx, face in enumerate(faces):
                if f_idx not in used_faces:
                     self.active_tracks.append({
                         'id': str(uuid.uuid4()),
                         'best_face': face,
                         'start_timestamp': timestamp,
                         'end_timestamp': timestamp,
                         'last_seen_frame_idx': frame_idx,
                         'missed_frames': 0,
                         'history': [face]
                     })

            for t_idx, track in enumerate(self.active_tracks):
                if t_idx not in used_tracks:
                    track['missed_frames'] += 1

        new_active = []
        for track in self.active_tracks:
            if track['missed_frames'] > self.max_missed_frames:
                finished_tracks.append(track)
            else:
                new_active.append(track)

        self.active_tracks = new_active

        return finished_tracks

    def finalize(self) -> List[Dict]:
        """
        Force finish all active tracks (e.g. at end of video).
        """
        finished = list(self.active_tracks)
        self.active_tracks = []
        return finished
