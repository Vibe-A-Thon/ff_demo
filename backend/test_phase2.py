"""Simple test to verify the Phase 2 implementation."""

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    
    from app.seed_data.full_roster_generator import generate_full_roster, get_team_summary
    
    summary = get_team_summary()
    print("=" * 60)
    print("FRAUD FORGE - FULL 54-AGENT ROSTER VERIFICATION")
    print("=" * 60)
    print(f"Total Teams: {summary['total_teams']}")
    print(f"Total Agents: {summary['total_agents']}")
    print()
    print("Team Breakdown:")
    for team_id, count in summary['team_breakdown'].items():
        team_name = summary['team_names'].get(team_id, team_id)
        print(f"  - {team_name}: {count} agents")
    
    # Verify the counts are correct
    assert summary['total_teams'] == 8, f"Expected 8 teams, got {summary['total_teams']}"
    assert summary['total_agents'] == 54, f"Expected 54 agents, got {summary['total_agents']}"
    
    print()
    print("✅ All verifications passed!")
