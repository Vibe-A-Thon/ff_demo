import chromadb
from typing import List, Dict, Any, Optional
import os
import uuid


class VectorMemory:
    def __init__(
        self, collection_name: str = "fraud_forge", host: str = None, port: int = None
    ):
        self.host = host or os.getenv("CHROMA_HOST", "chromadb")
        self.port = port or int(os.getenv("CHROMA_PORT", "8000"))
        self.client = chromadb.HttpClient(host=self.host, port=self.port)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(self, text: str, metadata: Dict[str, Any], doc_id: str = None):
        if doc_id is None:
            doc_id = str(uuid.uuid4())

        self.collection.add(documents=[text], metadatas=[metadata], ids=[doc_id])
        return doc_id

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query_text], n_results=n_results, where=where
        )

        # Format results
        formatted_results = []
        if results and results["ids"]:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i]
                        if results["documents"]
                        else None,
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else None,
                        "distance": results["distances"][0][i]
                        if results["distances"]
                        else None,
                    }
                )

        return formatted_results

    def delete(self, doc_id: str):
        self.collection.delete(ids=[doc_id])
