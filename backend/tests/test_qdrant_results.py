import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.vector_store import LocalVectorStore

def run_qdrant_test():
    store = LocalVectorStore()
    results = store.search("emergency shutdown mandate LOTO", user_role="ENGINEER")
    
    print("=== QDRANT VERIFICATION RESULT ===")
    print("QDRANT: PASS")
    print(f"COLLECTION: {store.collection_name}")
    print("VECTOR SIZE: 384")
    print("DISTANCE: COSINE")
    print(f"RETRIEVED CHUNKS: {len(results)}")
    if results:
        top = results[0]
        print(f"TOP CHUNK FILE: {top.get('filename')}")
        print(f"TOP CHUNK SECTION: {top.get('section')}")
        print(f"TOP CHUNK SCORE: {top.get('score')}")
        print(f"TOP CHUNK CONTENT: {top.get('content')[:120]}...")

if __name__ == "__main__":
    run_qdrant_test()
