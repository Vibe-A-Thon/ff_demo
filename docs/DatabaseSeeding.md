# MongoDB Database Seeding System

Complete guide for populating the Fraud Forge database with demo data for hackathon presentations.

---

## 🎯 Overview

The database seeding system provides comprehensive demo data across all MongoDB collections, including:
- **Teams** (3): Purple Defenders, Gold Advisors, Red Attackers
- **Agents** (5): Blue sentinels, Gold XAI, Red attackers
- **Rules** (5): Production fraud detection rules
- **Battles** (15): Historical battle scenarios with outcomes
- **Run Events** (100+): Detailed battle event logs
- **RSB Packages** (2): Rule set bundles
- **Knowledge Nodes** (7): Brain graph structure
- **RAG Documents** (4): Semantic search content
- **Agent Artifacts** (10): Learning memories

---

## 🚀 Quick Start

### Via UI (Recommended)

1. Navigate to **Settings & Configuration** page
2. Scroll to **Database Seeding** section
3. Click **"Seed Demo Data"** button
4. Wait for confirmation toast (2-3 seconds)
5. ✅ Database populated with 200+ documents!

### Via API

```bash
# Seed comprehensive data
curl -X POST http://localhost:8000/api/seed-comprehensive \
  -H "Authorization: Bearer YOUR_TOKEN"

# Clear all data
curl -X DELETE http://localhost:8000/api/clear-all-data \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Via Python Script

```python
from app.seed_data.demo_data_generator import generate_demo_data
from app.core.external_services import DatabaseClient

# Generate data
data = generate_demo_data()

 # Seed manually
db = DatabaseClient()
await db.teams.insert_many(data["teams"])
await db.agents.insert_many(data["agents"])
# ... etc
```

---

## 📊 Data Structure

### Teams Collection
```json
{
  "team_id": "purple_defenders",
  "internal_name": "Purple Team - Defenders",
  "display_name": "Purple Defenders",
  "description": "Elite defense team specializing in fraud prevention",
 "operating_mode": "HITL",
  "status": "active",
  "created_at": "2026-02-02T19:00:00Z",
  "metrics": {
    "total_battles": 45,
    "win_rate": 0.87,
    "avg_response_time": 2.3
  }
}
```

### Agents Collection
```json
{
  "agent_id": "blue-sentinel-01",
  "agent_name": "Blue Sentinel",
  "team_id": "purple_defenders",
  "role": "blue",
  "status": "active",
  "operating_mode": "HITL",
  "last_run": "2026-02-01T14:30:00Z",
  "total_runs": 45,
  "success_rate": 0.89
}
```

### Battles Collection
```json
{
  "id": "battle-abc123",
  "run_id": "battle-abc123",
  "scenario_name": "Battle 15: Account Takeover",
  "status": "completed",
  "started_at": "2026-02-02T10:00:00Z",
  "completed_at": "2026-02-02T10:25:00Z",
  "parameters": {
    "difficulty": "hard",
    "max_turns": 20,
    "transaction_count": 150
  },
  "metrics": {
    "success_rate": 0.92,
    "money_at_risk": 250000,
    "money_saved": 230000,
    "time_to_immunity": 8,
    "patterns_learned": 5,
    "transactions_analyzed": 150,
    "threats_detected": 15,
    "false_positives": 2
  },
  "teams": {
    "purple": "purple_defenders",
    "gold": "gold_advisors",
    "red": "red_attackers"
  },
  "agents": {
    "blue": ["blue-sentinel-01", "guardian-shield-02"],
    "gold": ["xai-oracle-01"],
    "red": ["red-phantom-01", "crimson-viper-02"]
  }
}
```

---

##  API Endpoints

### POST /api/seed-comprehensive

Seeds all collections with comprehensive demo data.

**Request:**
```http
POST /api/seed-comprehensive
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Comprehensive demo data seeded successfully",
  "status": "success",
  "collections_seeded": {
    "teams": 3,
    "agents": 5,
    "rules": 5,
    "battles": 15,
    "run_events": 120,
    "rsb_packages": 2,
    "knowledge_nodes": 7,
    "rag_documents": 4,
    "agent_artifacts": 10
  },
  "total_documents": 171
}
```

### DELETE /api/clear-all-data

Clears all demo data from database.

**Request:**
```http
DELETE /api/clear-all-data
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "All data cleared",
  "deleted": {
    "teams": 3,
    "agents": 5,
    "battles": 15,
    "run_events": 120,
    ...
  },
  "total_deleted": 171
}
```

---

## 🎨 UI Components

### Settings Page Integration

The seeding UI is located in **Settings & Configuration** page:

```jsx
<Card data-testid="settings-database-seeding">
  <CardHeader>
    <CardTitle>Database Seeding</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Seed button */}
    <Button onClick={handleSeedComprehensive}>
      Seed Demo Data
    </Button>
    
    {/* Clear button */}
    <Button variant="destructive" onClick={handleClearData}>
      Clear All Data
    </Button>
  </CardContent>
</Card>
```

**Features:**
- ✅ Loading states with spinners
- ✅ Success/error toasts
- ✅ Confirmation dialog for clearing
- ✅ Detailed data breakdown
- ✅ Auto-disabled during operations

---

## 📁 File Structure

```
backend/
├── app/
│   ├── seed_data/
│   │   ├── __init__.py
│   │   └── demo_data_generator.py   # Data generation logic
│   └── routes/
│       └── seed.py                    # API endpoints
frontend/
├── src/
│   ├── pages/
│   │   └── SettingsConfiguration.jsx  # UI with seed buttons
│   └── lib/
│       └── api.js                      # seedAPI methods
```

---

## 🔧 Development

### Adding New Collections

1. **Update `demo_data_generator.py`:**
```python
def generate_demo_data():
    # ... existing collections ...
    
    # New collection
    new_collection = [
        {"id": "item-1", "data": "value"},
        {"id": "item-2", "data": "value"},
    ]
    
    return {
        # ... existing ...
        "new_collection": new_collection
    }
```

2. **Update `seed.py` endpoint:**
```python
if data["new_collection"]:
    await db.new_collection.insert_many(data["new_collection"])
    counts["new_collection"] = len(data["new_collection"])
```

3. **Update UI display** (optional)

### Customizing Data

Edit `demo_data_generator.py` to adjust:
- Number of items per collection
- Date ranges for battles
- Metric ranges
- Team/agent configurations

---

## ⚠️ Important Notes

### Data Clearing
- **Clearing is PERMANENT** - there's no undo
- Always confirms via dialog before clearing
- Logged to audit trail
- Requires `seed:write` permission

### Performance
- Seeding takes 2-3 seconds for full dataset
- No performance impact on small collections
- Indexes automatically created by MongoDB

### Permissions
Both endpoints require `seed:write` permission:
```python
@router.post("/seed-comprehensive")
async def seed_comprehensive_data(
    current_user: dict = Depends(require_permission("seed:write")),
    ...
):
```

---

## 🎯 Use Cases

### 1. Hackathon Demo Prep
```bash
# Before demo
POST /api/seed-comprehensive

# After demo
DELETE /api/clear-all-data
```

### 2. Development Testing
```bash
# Test with fresh data
DELETE /api/clear-all-data
POST /api/seed-comprehensive

# Run your tests
# ...
```

### 3. Feature Showcasing
```bash
# Seed specific scenario data
# (use custom generator script)
python scripts/seed_custom.py
```

---

## 📈 Metrics & Monitoring

All seeding operations are:
- ✅ Logged to application logs
- ✅ Recorded in audit trail
- ✅ Tracked with counts per collection
- ✅ Timestamped with ISO dates

**Audit Trail Entry:**
```json
{
  "user_id": "user@example.com",
  "action": "seed.comprehensive_completed",
  "resource_type": "seed",
  "resource_id": "comprehensive",
  "metadata": {
    "teams": 3,
    "agents": 5,
    "battles": 15,
    ...
  },
  "timestamp": "2026-02-02T19:10:00Z"
}
```

---

## 🐛 Troubleshooting

### "Permission Denied"
- Ensure user has `seed:write` permission
- Check authentication token

### "Database Connection Error"
- Verify MongoDB is running
- Check connection string in `.env`

### "Seeding Takes Too Long"
- Normal for first seed (indexes created)
- Subsequent seeds should be faster

### "Data Not Appearing"
- Refresh the page
- Check correct database/collection
- Verify no errors in backend logs

---

## ✅ Checklist for Demo

- [ ] Clear old data: `DELETE /api/clear-all-data`
- [ ] Seed fresh data: `POST /api/seed-comprehensive`
- [ ] Verify battles appear in War Room
- [ ] Check agents in Agent Management
- [ ] Confirm rules in RSB Marketplace
- [ ] Test all dashboard metrics
- [ ] Review audit trail entries

---

## 🚀 Next Steps

1. **Extend Data**: Add more realistic scenarios
2. **Custom Seeders**: Create domain-specific datasets
3. **Seed Profiles**: Save/load different seed configurations
4. **Incremental Seeding**: Add data without clearing
5. **Export/Import**: Save seed states for reproducibility

---

**Status**: ✅ **READY FOR PRODUCTION**  
**Version**: 1.0  
**Last Updated**: 2026-02-02
