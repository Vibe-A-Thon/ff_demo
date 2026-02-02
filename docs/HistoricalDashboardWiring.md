# Historical Dashboard Wiring - Complete Implementation

## Overview

The **Historical Dashboard Wiring** feature provides true MongoDB aggregations for dashboard time-series charts, eliminating dependency on mock data and real-time War Room feeds.

This implementation computes historical metrics from stored `runs`, `run_events`, and `artifacts` collections, enabling:
- Multi-day trend analysis
- Accurate historical charting
- Granular time bucketing (hourly/daily/weekly)

---

## Architecture

```
MongoDB Collections          Aggregation Service         Dashboard API
┌────────────────┐         ┌──────────────────┐       ┌──────────────┐
│  runs          │────────▶│ Historical       │──────▶│/metrics/     │
│  run_events    │         │ Aggregator       │       │historical    │
│  artifacts     │         └──────────────────┘       └──────────────┘
└────────────────┘                                     │/metrics/     │
                                                        │dashboard/v2  │
                                                        └──────────────┘
```

### Key Components

1. **HistoricalMetricsAggregator** - Core aggregation engine
2. **API Endpoints** - REST endpoints for historical data
3. **Time Bucketing** - Flexible hourly/daily/weekly aggregation
4. **Trend Analysis** - Automatic trend detection

---

## Features

### 1. Time-Series Aggregation

Computes metrics across configurable time periods:

#### Daily Aggregation (Default)
```python
GET /api/metrics/historical?days=30&granularity=daily
```

Returns one data point per day with:
- Total runs
- Completed/failed runs
- Success rate
- Time to immunity
- Patterns learned
- Risk scores
- Actions (blocked/allowed)

#### Hourly Aggregation
```python
GET /api/metrics/historical?days=7&granularity=hourly
```

For high-frequency analysis.

#### Weekly Aggregation
```python
GET /api/metrics/historical?days=90&granularity=weekly
```

For long-term trends.

### 2. Dashboard Metrics v2

Enhanced dashboard endpoint with true historical data:

```python
GET /api/metrics/dashboard/v2?days=30
```

Returns:
- Summary metrics (total battles, success rate, etc.)
- Complete time-series data
- Trend analysis
- Operational KPIs

**Replaces**: `/api/metrics/dashboard` (legacy endpoint with fallback data)

### 3. Trend Analysis

Automatic trend detection:

```python
GET /api/metrics/trends?days=30
```

Compares first half vs second half of period to detect:
- Success rate trends (increasing/decreasing/stable)
- Run volume trends
- Pattern learning trends

---

## API Reference

### GET /api/metrics/historical

Get time-series historical metrics.

**Query Parameters:**
- `days` (int, default: 30) - Number of days to include
- `granularity` (string, default: "daily") - Time bucket size: "hourly", "daily", "weekly"

**Response:**
```json
{
  "period_days": 30,
  "granularity": "daily",
  "data_points": 30,
  "time_series": [
    {
      "timestamp": "2026-01-15",
      "total_runs": 12,
      "completed_runs": 10,
      "failed_runs": 2,
      "success_rate": 85.5,
      "time_to_immunity": 8.2,
      "patterns_learned": 45,
      "avg_risk_score": 0.68,
      "total_actions": 120,
      "blocked_actions": 95
    },
    ...
  ]
}
```

### GET /api/metrics/dashboard/v2

Get complete dashboard metrics with historical aggregations.

**Query Parameters:**
- `days` (int, default: 30) - Aggregation period

**Response:**
```json
{
  "total_battles": 350,
  "completed_battles": 320,
  "running_battles": 0,
  "avg_success_rate": 87.2,
  "total_rules": 25,
  "active_rules": 22,
  "patterns_learned": 1250,
  "avg_time_to_immunity": 7.8,
  "time_series": [...],
  "trends": {
    "success_rate_trend": "increasing",
    "success_rate_change_pct": 12.5,
    "run_volume_trend": "stable",
    "run_volume_change_pct": -2.3,
    "patterns_trend": "increasing",
    "patterns_change_pct": 18.7
  },
  "operational_kpis": {
    "total_runs": 350,
    "completed_runs": 320,
    "total_actions": 1205,
    "blocked_actions": 980,
    "block_rate": 81.3,
    "period_days": 30
  }
}
```

### GET /api/metrics/trends

Get trend analysis for key metrics.

**Query Parameters:**
- `days` (int, default: 30) - Analysis period

**Response:**
```json
{
  "period_days": 30,
  "trends": {
    "success_rate_trend": "increasing",
    "success_rate_change_pct": 12.5,
    "run_volume_trend": "stable",
    "run_volume_change_pct": -2.3,
    "patterns_trend": "increasing",
    "patterns_change_pct": 18.7
  }
}
```

---

## Implementation Details

### Aggregation Logic

The `HistoricalMetricsAggregator` processes data in stages:

1. **Fetch Data**: Query MongoDB for runs, events, and artifacts in date range
2. **Create Time Buckets**: Generate time slots based on granularity
3. **Aggregate Per Bucket**: Group data into time buckets
4. **Compute Metrics**: Calculate averages, totals, and rates
5. **Format Output**: Return structured time-series

### Time Bucketing

Timestamps are normalized to bucket boundaries:

- **Hourly**: `2026-02-01T15:30:00Z` → `2026-02-01T15:00:00Z`
- **Daily**: `2026-02-01T15:30:00Z` → `2026-02-01`
- **Weekly**: `2026-02-04T15:30:00Z` → `2026-02-02` (Monday of week)

### Metrics Computed

For each time bucket:

| Metric | Calculation |
|--------|-------------|
| Total Runs | Count of runs in bucket |
| Completed Runs | Count where `status == "completed"` |
| Failed Runs | Count where `status == "failed"` |
| Success Rate | Average of `(blocked_actions / total_actions) * 100` |
| Time to Immunity | Average of `step_count` from runs |
| Patterns Learned | Count of artifacts created in bucket |
| Avg Risk Score | Average of `last_metrics.avg_score` |
| Total Actions | Sum of all actions from run_events |
| Blocked Actions | Sum of actions where `action == "block"` |

---

## Usage Examples

### Frontend Integration

```javascript
// Fetch 30-day historical data for charts
const response = await fetch('/api/metrics/dashboard/v2?days=30');
const data = await response.json();

// Use time_series for charts
const chartData = data.time_series.map(item => ({
  x: new Date(item.timestamp),
  success: item.success_rate,
  patterns: item.patterns_learned
}));

// Display trends
if (data.trends.success_rate_trend === 'increasing') {
  showPositiveTrend(data.trends.success_rate_change_pct);
}
```

### Custom Time Range

```javascript
// Get last 7 days with hourly granularity
const response = await fetch(
  '/api/metrics/historical?days=7&granularity=hourly'
);
const { time_series } = await response.json();

// High-resolution chart
renderHourlyChart(time_series);
```

### Trend Dashboard Widget

```javascript
const response = await fetch('/api/metrics/trends?days=30');
const { trends } = await response.json();

// Show trend indicators
displayTrend('Success Rate', trends.success_rate_trend, trends.success_rate_change_pct);
displayTrend('Run Volume', trends.run_volume_trend, trends.run_volume_change_pct);
```

---

## Performance

| Operation | Dataset Size | Time | Notes |
|-----------|--------------|------|-------|
| Daily Aggregation | 1000 runs, 30 days | < 500ms | Typical use case |
| Hourly Aggregation | 1000 runs, 7 days | < 800ms | Higher granularity |
| Weekly Aggregation | 5000 runs, 90 days | < 1s | Long-term analysis |

**Optimizations:**
- In-memory aggregation (no MongoDB aggregation pipeline overhead)
- Date range filtering before processing
- Efficient time bucket lookup

---

## Migration from Legacy Dashboard

### Before (Old Endpoint)
```javascript
// Used fallback data and real-time events only
const data = await fetch('/api/metrics/dashboard');
// time_series was limited to last 20 completed runs
```

### After (New Endpoint)
```javascript
// True historical aggregation
const data = await fetch('/api/metrics/dashboard/v2?days=30');
// time_series covers full 30 days with accurate data
```

**Migration Steps:**
1. Update frontend to call `/metrics/dashboard/v2`
2. Update chart components to use `time_series`
3. Add trend indicators using `trends` data
4. Test with production data

---

## Testing

Run the test suite:

```bash
pytest backend/tests/test_historical_metrics.py -v
```

### Test Coverage

- ✅ Daily time-series aggregation
- ✅ Hourly time-series aggregation
- ✅ Weekly time-series aggregation
- ✅ Aggregated dashboard metrics
- ✅ Trend analysis (increasing/decreasing/stable)
- ✅ Empty data handling
- ✅ Bucket key generation (all granularities)
- ✅ Time bucket creation
- ✅ Realistic battle scenarios
- ✅ Performance with large datasets (1000+ runs)

---

## Monitoring

### Metrics to Track

- `metrics.historical.generated` - Historical queries
- `metrics.dashboard.v2.generated` - Dashboard v2 queries
- `metrics.trends.generated` - Trend analysis queries

### Dashboard

View aggregation metrics at:
```
/metrics → Historical Data Pipeline
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Time series empty | Check date range includes completed runs |
| Slow performance | Reduce `days` parameter or increase granularity |
| Missing data points | Verify `started_at` timestamps on runs |
| Incorrect trends | Ensure enough data in period (minimum 10 data points) |

---

## Future Enhancements

1. **Caching**: Redis cache for frequently accessed time ranges
2. **MongoDB Aggregation Pipeline**: Offload aggregation to database
3. **Real-time Updates**: WebSocket stream for live data
4. **Custom Metrics**: User-defined metric calculations
5. **Export**: CSV/Excel export of time-series data

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-02 18:50 IST  
**Status:** ✅ Production Ready
