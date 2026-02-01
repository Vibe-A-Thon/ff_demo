"""Shared test fixtures and in-memory DB utilities."""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


def generate_id() -> str:
    return str(uuid.uuid4())


class InMemoryCursor:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = items

    def sort(self, field: str, direction: int):
        reverse = direction < 0
        self._items.sort(key=lambda item: item.get(field), reverse=reverse)
        return self

    async def to_list(self, limit: int):
        return self._items[:limit]


@dataclass
class UpdateResult:
    modified_count: int


@dataclass
class DeleteResult:
    deleted_count: int


class InMemoryCollection:
    def __init__(self):
        self._items: List[Dict[str, Any]] = []

    def _match(self, item: Dict[str, Any], query: Dict[str, Any]) -> bool:
        for key, value in query.items():
            if isinstance(value, dict) and "$in" in value:
                if item.get(key) not in value["$in"]:
                    return False
            else:
                if item.get(key) != value:
                    return False
        return True

    async def find_one(self, query: Dict[str, Any], projection: Optional[Dict[str, int]] = None):
        for item in self._items:
            if self._match(item, query):
                return self._project(item, projection)
        return None

    def find(self, query: Dict[str, Any], projection: Optional[Dict[str, int]] = None):
        matches = [self._project(item, projection) for item in self._items if self._match(item, query)]
        return InMemoryCursor(matches)

    async def insert_one(self, document: Dict[str, Any]):
        self._items.append(copy.deepcopy(document))
        return document

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        modified = 0
        for item in self._items:
            if self._match(item, query):
                if "$set" in update:
                    item.update(copy.deepcopy(update["$set"]))
                if "$push" in update:
                    for key, value in update["$push"].items():
                        if isinstance(value, dict) and "$each" in value:
                            item.setdefault(key, []).extend(copy.deepcopy(value["$each"]))
                        else:
                            item.setdefault(key, []).append(copy.deepcopy(value))
                modified = 1
                break
        return UpdateResult(modified_count=modified)

    async def delete_one(self, query: Dict[str, Any]):
        for idx, item in enumerate(self._items):
            if self._match(item, query):
                del self._items[idx]
                return DeleteResult(deleted_count=1)
        return DeleteResult(deleted_count=0)

    async def delete_many(self, query: Dict[str, Any]):
        self._items = [item for item in self._items if not self._match(item, query)]

    async def distinct(self, field: str):
        return list({item.get(field) for item in self._items if field in item})

    def _project(self, item: Dict[str, Any], projection: Optional[Dict[str, int]]):
        if not projection:
            return copy.deepcopy(item)
        data = copy.deepcopy(item)
        if "_id" in projection and projection.get("_id") == 0:
            data.pop("_id", None)
        return data


class InMemoryDB:
    def __init__(self):
        self._collections: Dict[str, InMemoryCollection] = {}

    def __getattr__(self, name: str) -> InMemoryCollection:
        if name.startswith("_"):
            raise AttributeError
        if name not in self._collections:
            self._collections[name] = InMemoryCollection()
        return self._collections[name]


def seed_user(db: InMemoryDB, role: str = "bank_admin") -> Dict[str, Any]:
    user = {
        "id": generate_id(),
        "email": f"user-{role}@example.com",
        "name": "Test User",
        "role": role,
        "password_hash": "hashed",
    }
    db.users._items.append(copy.deepcopy(user))
    return user
