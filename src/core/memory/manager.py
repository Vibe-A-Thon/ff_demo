from typing import Any, Dict, List, Optional
from core.memory.vector import VectorMemory
from core.memory.relational import RelationalMemory


class MemoryManager:
    def __init__(
        self,
        vector_memory: VectorMemory = None,
        relational_memory: RelationalMemory = None,
    ):
        self.vector = vector_memory or VectorMemory()
        self.relational = relational_memory or RelationalMemory()

    def remember_battle(self, battle_id: str, data: Dict[str, Any]):
        """
        Store battle outcome in both relational and vector memory.
        """
        # Store structured data
        # In a real scenario, we would have specific tables.
        # For now, we assume a flexible schema or just logging.
        # self.relational.execute_query("INSERT INTO battles ...")
        pass

        # Store vector embedding of the battle summary/description
        if "description" in data:
            self.vector.add(
                text=data["description"],
                metadata={"type": "battle", "battle_id": battle_id},
                doc_id=f"battle_{battle_id}",
            )

    def retrieve_context(self, query: str) -> Dict[str, Any]:
        """
        Retrieve relevant context from vector memory.
        """
        vector_results = self.vector.query(query)
        return {"similar_events": vector_results}
