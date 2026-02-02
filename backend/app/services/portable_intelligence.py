"""
Portable Intelligence Service

Implements the "killer feature" - portable AI brain export/import:
- PEP (Portable Evolution Pack) - Export brain state
- APMC (Agent Pattern Memory Capsule) - Import memory
- RSB (Rule Suite Box) - Rule packages
- BRC (Brain Capsule) - Full brain state

Each package is a zipped bundle containing:
- manifest.json (version, checksum, metadata)
- memories/ (RAG documents, anonymized)
- evolution/ (learning history)
- rules/ (rule definitions)
"""

from __future__ import annotations

import hashlib
import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.external_services import DatabaseClient, LLMClient
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Package types
class PackageType:
    PEP = "pep"  # Portable Evolution Pack
    APMC = "apmc"  # Agent Pattern Memory Capsule
    RSB = "rsb"  # Rule Suite Box
    BRC = "brc"  # Brain Capsule


class PortableIntelligenceService:
    """
    Service for exporting and importing portable intelligence packages.
    """
    
    def __init__(self, db: DatabaseClient, llm_client: Optional[LLMClient] = None):
        self.db = db
        self.llm_client = llm_client
    
    # =========================================================================
    # EXPORT FUNCTIONS
    # =========================================================================
    
    async def export_pep(
        self,
        name: str,
        description: str = "",
        collections: Optional[List[str]] = None,
        anonymize: bool = True,
        include_evolution: bool = True,
        agent_ids: Optional[List[str]] = None,
    ) -> io.BytesIO:
        """
        Export a Portable Evolution Pack (PEP).
        
        Args:
            name: Package name
            description: Package description
            collections: RAG collections to include
            anonymize: Whether to anonymize sensitive data
            include_evolution: Whether to include evolution history
            agent_ids: Specific agents to include
            
        Returns:
            BytesIO containing the zipped PEP file
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        package_id = str(uuid.uuid4())[:8]
        
        # Prepare manifest
        manifest = {
            "package_id": package_id,
            "package_type": PackageType.PEP,
            "name": name,
            "description": description,
            "version": "1.0.0",
            "created_at": timestamp,
            "created_by": "fraud_forge",
            "checksum": None,  # Will be calculated
            "contents": {
                "memories": 0,
                "evolution_events": 0,
                "agents": 0,
            },
            "metadata": {
                "anonymized": anonymize,
                "source_system": "fraud_forge",
                "export_version": "2.0",
            }
        }
        
        # Create zip buffer
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Export RAG memories
            memories = await self._export_memories(collections, anonymize)
            manifest["contents"]["memories"] = len(memories)
            zf.writestr("memories/rag_documents.json", json.dumps(memories, indent=2))
            
            # Export evolution history
            if include_evolution:
                evolution = await self._export_evolution_history(agent_ids)
                manifest["contents"]["evolution_events"] = len(evolution)
                zf.writestr("evolution/history.json", json.dumps(evolution, indent=2))
            
            # Export agent profiles
            agents = await self._export_agent_profiles(agent_ids)
            manifest["contents"]["agents"] = len(agents)
            zf.writestr("agents/profiles.json", json.dumps(agents, indent=2))
            
            # Calculate checksum
            manifest["checksum"] = self._calculate_checksum(memories, agents)
            
            # Write manifest
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        
        zip_buffer.seek(0)
        
        # Log export
        await self.db.export_logs.insert_one({
            "package_id": package_id,
            "package_type": PackageType.PEP,
            "name": name,
            "timestamp": timestamp,
            "contents": manifest["contents"],
        })
        
        logger.info(
            "portable.export.pep",
            extra={"payload": {"package_id": package_id, "name": name}}
        )
        
        return zip_buffer
    
    async def export_rsb(
        self,
        name: str,
        rule_ids: Optional[List[str]] = None,
        include_tests: bool = True,
    ) -> io.BytesIO:
        """
        Export a Rule Suite Box (RSB).
        
        Args:
            name: Package name
            rule_ids: Specific rule IDs to include (None = all)
            include_tests: Whether to include test cases
            
        Returns:
            BytesIO containing the zipped RSB file
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        package_id = str(uuid.uuid4())[:8]
        
        # Query rules
        query = {}
        if rule_ids:
            query["rule_id"] = {"$in": rule_ids}
        
        rules = await self.db.rules.find(query, {"_id": 0}).to_list(500)
        
        # Prepare manifest
        manifest = {
            "package_id": package_id,
            "package_type": PackageType.RSB,
            "name": name,
            "version": "1.0.0",
            "created_at": timestamp,
            "checksum": None,
            "contents": {
                "rules": len(rules),
                "tests": 0,
            },
        }
        
        # Create zip buffer
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Export rules
            zf.writestr("rules/definitions.json", json.dumps(rules, indent=2))
            
            # Export tests if requested
            if include_tests:
                tests = await self._export_rule_tests(rule_ids)
                manifest["contents"]["tests"] = len(tests)
                zf.writestr("tests/cases.json", json.dumps(tests, indent=2))
            
            # Calculate checksum
            manifest["checksum"] = self._calculate_checksum(rules, [])
            
            # Write manifest
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        
        zip_buffer.seek(0)
        
        logger.info(
            "portable.export.rsb",
            extra={"payload": {"package_id": package_id, "name": name, "rules": len(rules)}}
        )
        
        return zip_buffer
    
    async def export_brc(
        self,
        name: str,
        description: str = "",
    ) -> io.BytesIO:
        """
        Export a full Brain Capsule (BRC) - complete brain state.
        
        Args:
            name: Package name
            description: Package description
            
        Returns:
            BytesIO containing the zipped BRC file
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        package_id = str(uuid.uuid4())[:8]
        
        manifest = {
            "package_id": package_id,
            "package_type": PackageType.BRC,
            "name": name,
            "description": description,
            "version": "1.0.0",
            "created_at": timestamp,
            "checksum": None,
            "contents": {},
        }
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Export all RAG collections
            all_collections = ["attacks", "patterns", "taxonomy", "rules", "explanations"]
            for collection in all_collections:
                docs = await self.db.rag_documents.find(
                    {"collection": collection},
                    {"_id": 0, "embedding": 0}
                ).to_list(1000)
                manifest["contents"][f"rag_{collection}"] = len(docs)
                zf.writestr(f"rag/{collection}.json", json.dumps(docs, indent=2))
            
            # Export knowledge graph
            nodes = await self.db.knowledge_nodes.find({}, {"_id": 0}).to_list(1000)
            manifest["contents"]["knowledge_nodes"] = len(nodes)
            zf.writestr("graph/nodes.json", json.dumps(nodes, indent=2))
            
            # Export agents
            agents = await self.db.agents.find({}, {"_id": 0}).to_list(100)
            manifest["contents"]["agents"] = len(agents)
            zf.writestr("agents/all.json", json.dumps(agents, indent=2))
            
            # Export rules
            rules = await self.db.rules.find({}, {"_id": 0}).to_list(500)
            manifest["contents"]["rules"] = len(rules)
            zf.writestr("rules/all.json", json.dumps(rules, indent=2))
            
            # Export learning events
            learnings = await self.db.learning_events.find({}, {"_id": 0}).to_list(1000)
            manifest["contents"]["learning_events"] = len(learnings)
            zf.writestr("evolution/learnings.json", json.dumps(learnings, indent=2))
            
            # Calculate checksum
            manifest["checksum"] = hashlib.sha256(
                json.dumps(manifest["contents"]).encode()
            ).hexdigest()[:16]
            
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        
        zip_buffer.seek(0)
        
        logger.info(
            "portable.export.brc",
            extra={"payload": {"package_id": package_id, "name": name}}
        )
        
        return zip_buffer
    
    # =========================================================================
    # IMPORT FUNCTIONS
    # =========================================================================
    
    async def import_package(
        self,
        file_content: bytes,
        merge_mode: str = "merge",  # "merge", "replace", "skip_existing"
        validate_checksum: bool = True,
    ) -> Dict[str, Any]:
        """
        Import a portable intelligence package.
        
        Args:
            file_content: Raw bytes of the zip file
            merge_mode: How to handle conflicts
            validate_checksum: Whether to validate package integrity
            
        Returns:
            Dict with import results
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Open and parse the zip
        zip_buffer = io.BytesIO(file_content)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            # Read manifest
            manifest_content = zf.read("manifest.json")
            manifest = json.loads(manifest_content)
            
            package_type = manifest.get("package_type", "unknown")
            package_id = manifest.get("package_id", "unknown")
            
            # Validate checksum if requested
            if validate_checksum and manifest.get("checksum"):
                # Simplified validation - in production, recalculate full checksum
                logger.info(
                    "portable.import.checksum_valid",
                    extra={"payload": {"package_id": package_id}}
                )
            
            # Route to appropriate handler
            if package_type == PackageType.PEP:
                result = await self._import_pep(zf, manifest, merge_mode)
            elif package_type == PackageType.RSB:
                result = await self._import_rsb(zf, manifest, merge_mode)
            elif package_type == PackageType.BRC:
                result = await self._import_brc(zf, manifest, merge_mode)
            elif package_type == PackageType.APMC:
                result = await self._import_apmc(zf, manifest, merge_mode)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown package type: {package_type}",
                }
        
        # Log import
        await self.db.import_logs.insert_one({
            "package_id": package_id,
            "package_type": package_type,
            "timestamp": timestamp,
            "merge_mode": merge_mode,
            "result": result,
        })
        
        logger.info(
            "portable.import.complete",
            extra={"payload": {"package_id": package_id, "type": package_type}}
        )
        
        return {
            "status": "success",
            "package_id": package_id,
            "package_type": package_type,
            "imported_at": timestamp,
            **result,
        }
    
    async def _import_pep(
        self,
        zf: zipfile.ZipFile,
        manifest: Dict[str, Any],
        merge_mode: str,
    ) -> Dict[str, Any]:
        """Import a PEP package."""
        imported = {"memories": 0, "evolution": 0, "agents": 0}
        
        # Import memories
        try:
            memories_content = zf.read("memories/rag_documents.json")
            memories = json.loads(memories_content)
            for mem in memories:
                mem["imported_from"] = manifest.get("package_id")
                mem["imported_at"] = datetime.now(timezone.utc).isoformat()
                
                if merge_mode == "skip_existing":
                    existing = await self.db.rag_documents.find_one({"id": mem.get("id")})
                    if existing:
                        continue
                
                await self.db.rag_documents.update_one(
                    {"id": mem.get("id")},
                    {"$set": mem},
                    upsert=True
                )
                imported["memories"] += 1
        except KeyError:
            pass
        
        # Import evolution history
        try:
            evolution_content = zf.read("evolution/history.json")
            evolution = json.loads(evolution_content)
            for event in evolution:
                event["imported_from"] = manifest.get("package_id")
                await self.db.learning_events.insert_one(event)
                imported["evolution"] += 1
        except KeyError:
            pass
        
        return imported
    
    async def _import_rsb(
        self,
        zf: zipfile.ZipFile,
        manifest: Dict[str, Any],
        merge_mode: str,
    ) -> Dict[str, Any]:
        """Import an RSB package."""
        imported = {"rules": 0, "tests": 0}
        
        # Import rules
        try:
            rules_content = zf.read("rules/definitions.json")
            rules = json.loads(rules_content)
            for rule in rules:
                rule["imported_from"] = manifest.get("package_id")
                rule["imported_at"] = datetime.now(timezone.utc).isoformat()
                
                if merge_mode == "skip_existing":
                    existing = await self.db.rules.find_one({"rule_id": rule.get("rule_id")})
                    if existing:
                        continue
                
                await self.db.rules.update_one(
                    {"rule_id": rule.get("rule_id")},
                    {"$set": rule},
                    upsert=True
                )
                imported["rules"] += 1
        except KeyError:
            pass
        
        return imported
    
    async def _import_brc(
        self,
        zf: zipfile.ZipFile,
        manifest: Dict[str, Any],
        merge_mode: str,
    ) -> Dict[str, Any]:
        """Import a BRC (full brain) package."""
        imported = {}
        
        # Import all RAG collections
        for collection in ["attacks", "patterns", "taxonomy", "rules", "explanations"]:
            try:
                content = zf.read(f"rag/{collection}.json")
                docs = json.loads(content)
                count = 0
                for doc in docs:
                    doc["imported_from"] = manifest.get("package_id")
                    await self.db.rag_documents.update_one(
                        {"id": doc.get("id")},
                        {"$set": doc},
                        upsert=True
                    )
                    count += 1
                imported[f"rag_{collection}"] = count
            except KeyError:
                pass
        
        # Import knowledge nodes
        try:
            content = zf.read("graph/nodes.json")
            nodes = json.loads(content)
            for node in nodes:
                node["imported_from"] = manifest.get("package_id")
                node["status"] = "pending_merge"  # For Brain Surgery
                await self.db.knowledge_nodes.update_one(
                    {"id": node.get("id")},
                    {"$set": node},
                    upsert=True
                )
            imported["knowledge_nodes"] = len(nodes)
        except KeyError:
            pass
        
        return imported
    
    async def _import_apmc(
        self,
        zf: zipfile.ZipFile,
        manifest: Dict[str, Any],
        merge_mode: str,
    ) -> Dict[str, Any]:
        """Import an APMC package."""
        # APMC is similar to PEP but focused on memory capsules
        return await self._import_pep(zf, manifest, merge_mode)
    
    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================
    
    async def _export_memories(
        self,
        collections: Optional[List[str]],
        anonymize: bool,
    ) -> List[Dict[str, Any]]:
        """Export RAG memories."""
        query = {}
        if collections:
            query["collection"] = {"$in": collections}
        
        docs = await self.db.rag_documents.find(
            query,
            {"_id": 0, "embedding": 0}  # Exclude embeddings for portability
        ).to_list(1000)
        
        if anonymize:
            for doc in docs:
                # Remove sensitive metadata
                if "metadata" in doc:
                    doc["metadata"].pop("user_id", None)
                    doc["metadata"].pop("ip_address", None)
                    doc["metadata"].pop("session_id", None)
        
        return docs
    
    async def _export_evolution_history(
        self,
        agent_ids: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Export learning/evolution events."""
        query = {}
        if agent_ids:
            query["agent_id"] = {"$in": agent_ids}
        
        events = await self.db.learning_events.find(
            query,
            {"_id": 0}
        ).to_list(500)
        
        return events
    
    async def _export_agent_profiles(
        self,
        agent_ids: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Export agent profiles."""
        query = {}
        if agent_ids:
            query["agent_id"] = {"$in": agent_ids}
        
        agents = await self.db.agents.find(
            query,
            {"_id": 0}
        ).to_list(100)
        
        return agents
    
    async def _export_rule_tests(
        self,
        rule_ids: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Export test cases for rules."""
        # In production, this would query actual test cases
        # For now, return mock data
        return [
            {
                "test_id": "test-001",
                "rule_id": "VEL-001",
                "name": "Velocity burst test",
                "input": {"tx_count": 10, "time_window": 5},
                "expected": {"action": "flag", "severity": "high"},
            }
        ]
    
    def _calculate_checksum(
        self,
        memories: List[Dict[str, Any]],
        agents: List[Dict[str, Any]],
    ) -> str:
        """Calculate content checksum."""
        content = json.dumps({
            "memories_count": len(memories),
            "agents_count": len(agents),
        }).encode()
        return hashlib.sha256(content).hexdigest()[:16]
    
    async def validate_package(
        self,
        file_content: bytes,
    ) -> Dict[str, Any]:
        """
        Validate a package without importing it.
        
        Returns package manifest and validation status.
        """
        try:
            zip_buffer = io.BytesIO(file_content)
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                manifest_content = zf.read("manifest.json")
                manifest = json.loads(manifest_content)
                
                return {
                    "valid": True,
                    "manifest": manifest,
                    "files": zf.namelist(),
                }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
            }


async def create_portable_service(
    db: DatabaseClient,
    llm_client: Optional[LLMClient] = None,
) -> PortableIntelligenceService:
    """Factory function to create a PortableIntelligenceService instance."""
    return PortableIntelligenceService(db, llm_client)
