import faiss
import numpy as np
import json
import pandas as pd
import os
from glob import glob
from typing import List, Dict, Tuple
from app.core.config import settings

class VectorStore:
    def __init__(self, load_existing: bool = True):
        self.dimension = settings.VECTOR_DIM
        self.indices = [] # List of (index, metadata) tuples for Face
        self.bib_indices = [] # List of (index, metadata) tuples for Bib

        if load_existing:
            self.load()
        else:
            self.indices.append((faiss.IndexFlatIP(self.dimension), []))
            self.bib_indices.append((faiss.IndexFlatIP(settings.TEXT_EMBEDDING_DIM), []))

    @property
    def index(self):
        return self.indices[0][0]

    @property
    def metadata(self):
        return self.indices[0][1]

    @property
    def bib_index(self):
        return self.bib_indices[0][0]

    @property
    def bib_metadata(self):
        return self.bib_indices[0][1]

    def add_vectors(self, vectors: np.ndarray, metadata_entries: List[Dict]):
        """
        Add vectors to the PRIMARY (first) index.
        """
        if vectors.shape[0] != len(metadata_entries):
            raise ValueError("Number of vectors and metadata entries must match.")

        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.metadata.extend(metadata_entries)

    def add_bib_vectors(self, vectors: np.ndarray, metadata_entries: List[Dict]):
        if vectors.shape[0] != len(metadata_entries):
            raise ValueError("Number of vectors and metadata entries must match.")

        faiss.normalize_L2(vectors)
        self.bib_index.add(vectors)
        self.bib_metadata.extend(metadata_entries)

    def search(self, vector: np.ndarray, k: int = 5) -> List[Dict]:
        """
        Search Face Index across ALL shards.
        """
        faiss.normalize_L2(vector)
        all_results = []

        for idx, meta in self.indices:
            if idx.ntotal == 0: continue

            distances, indices = idx.search(vector, k)
            for i, result_idx in enumerate(indices[0]):
                if result_idx != -1 and result_idx < len(meta):
                    item = meta[result_idx].copy()
                    item['score'] = float(distances[0][i])
                    all_results.append(item)

        all_results.sort(key=lambda x: x['score'], reverse=True)
        return all_results[:k]

    def search_bib(self, vector: np.ndarray, k: int = 5) -> List[Dict]:
        """
        Search Bib Index across ALL shards.
        """
        faiss.normalize_L2(vector)
        all_results = []

        for idx, meta in self.bib_indices:
             if idx.ntotal == 0: continue

             distances, indices = idx.search(vector, k)
             for i, result_idx in enumerate(indices[0]):
                if result_idx != -1 and result_idx < len(meta):
                    item = meta[result_idx].copy()
                    item['score'] = float(distances[0][i])
                    all_results.append(item)

        all_results.sort(key=lambda x: x['score'], reverse=True)
        return all_results[:k]

    def save(self):
        os.makedirs(os.path.dirname(settings.INDEX_PATH), exist_ok=True)

        faiss.write_index(self.index, settings.INDEX_PATH)

        if self.metadata:
            df = pd.DataFrame(self.metadata)
            df.to_parquet(settings.METADATA_PATH, index=False)
        else:
             pass

        if self.bib_indices:
             faiss.write_index(self.bib_index, settings.BIB_INDEX_PATH)
             if self.bib_metadata:
                df = pd.DataFrame(self.bib_metadata)
                df.to_parquet(settings.BIB_METADATA_PATH, index=False)

    def load(self):
        self.indices = []
        self.bib_indices = []

        shard_pattern = os.path.join(os.path.dirname(settings.INDEX_PATH), "shard_*")
        shard_dirs = sort_shard_dirs(glob(shard_pattern))

        if shard_dirs:
            print(f"Found {len(shard_dirs)} shards: {shard_dirs}")
            for d in shard_dirs:
                self._load_pair(d)
        else:
            if os.path.exists(settings.INDEX_PATH):
                print(f"Loading main index from {settings.INDEX_PATH}")
                self._load_pair(os.path.dirname(settings.INDEX_PATH), main_file=True)
            else:
                self.indices.append((faiss.IndexFlatIP(self.dimension), []))
                self.bib_indices.append((faiss.IndexFlatIP(settings.TEXT_EMBEDDING_DIM), []))

    def _load_pair(self, directory: str, main_file: bool = False):
        if main_file:
            idx_path = settings.INDEX_PATH
            meta_path = settings.METADATA_PATH
            bib_idx_path = settings.BIB_INDEX_PATH
            bib_meta_path = settings.BIB_METADATA_PATH
        else:
            idx_path = os.path.join(directory, "index.faiss")
            meta_path = os.path.join(directory, "metadata.parquet")
            bib_idx_path = os.path.join(directory, "bib_index.faiss")
            bib_meta_path = os.path.join(directory, "bib_metadata.parquet")

        try:
            if os.path.exists(idx_path):
                idx = faiss.read_index(idx_path)
                meta = []
                if os.path.exists(meta_path):
                    try:

                        df = pd.read_parquet(meta_path)
                        meta = json.loads(df.to_json(orient='records'))
                    except Exception as e:
                         if meta_path.endswith('.parquet') and os.path.exists(meta_path.replace('.parquet', '.json')):
                             with open(meta_path.replace('.parquet', '.json'), 'r') as f:
                                 meta = json.load(f)
                         else:
                             print(f"Warning: Could not load metadata from {meta_path}: {e}")
                             meta = []
                self.indices.append((idx, meta))
        except Exception as e:
            print(f"Error loading face index from {directory}: {e}")

        try:
            if os.path.exists(bib_idx_path):
                bib_idx = faiss.read_index(bib_idx_path)
                bib_meta = []
                if os.path.exists(bib_meta_path):
                    try:
                        df = pd.read_parquet(bib_meta_path)
                        bib_meta = json.loads(df.to_json(orient='records'))
                    except Exception as e:
                         if bib_meta_path.endswith('.parquet') and os.path.exists(bib_meta_path.replace('.parquet', '.json')):
                             with open(bib_meta_path.replace('.parquet', '.json'), 'r') as f:
                                 bib_meta = json.load(f)
                         else:
                             print(f"Warning: Could not load bib metadata from {bib_meta_path}: {e}")
                             bib_meta = []
                self.bib_indices.append((bib_idx, bib_meta))
            else:
                self.bib_indices.append((faiss.IndexFlatIP(settings.TEXT_EMBEDDING_DIM), []))
        except Exception as e:
             print(f"Error loading bib index from {directory}: {e}")
             self.bib_indices.append((faiss.IndexFlatIP(settings.TEXT_EMBEDDING_DIM), []))

def sort_shard_dirs(paths):
    try:
        return sorted(paths, key=lambda x: int(x.split('_')[-1]))
    except:
        return sorted(paths)
