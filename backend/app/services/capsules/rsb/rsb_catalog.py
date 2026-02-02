
from typing import List, Dict, Any, Optional
from app.core.external_services import DatabaseClient

class RSBCatalog:
    def __init__(self, db: DatabaseClient):
        self.db = db
        self.collection = db.rsb_packages

    async def list_packages(self, limit: int = 100) -> List[Dict[str, Any]]:
        return await self.collection.find({}, {"_id": 0}).to_list(limit)

    async def get_package(self, package_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"id": package_id}, {"_id": 0})

    async def register_package(self, package_data: Dict[str, Any]) -> str:
        # Check rule_id conflict?
        # Insert
        await self.collection.insert_one(package_data)
        return package_data.get("id")

    async def update_status(self, package_id: str, status: str, metadata: Dict[str, Any] = None):
        update = {"status": status}
        if metadata:
            update.update(metadata)
        await self.collection.update_one({"id": package_id}, {"$set": update})
    
    async def delete_package(self, package_id: str) -> bool:
        res = await self.collection.delete_one({"id": package_id})
        return res.deleted_count > 0
