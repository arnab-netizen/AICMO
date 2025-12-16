"""
Campaign Orchestrator CLI.

Usage:
  python -m aicmo.cam.orchestrator.run --campaign-id 1 --mode proof --ticks 1
  python -m aicmo.cam.orchestrator.run --campaign-id 1 --mode live --interval 30
"""

import sys
import time
import argparse
from datetime import datetime

from backend.db.session import get_session

from aicmo.cam.orchestrator.engine import CampaignOrchestrator
from aicmo.cam.orchestrator.artifacts import generate_artifacts


def main():
    parser = argparse.ArgumentParser(description="Campaign Orchestrator")
    parser.add_argument("--campaign-id", type=int, required=True, help="Campaign ID to orchestrate")
    parser.add_argument("--mode", choices=["proof", "live"], default="proof", help="Execution mode")
    parser.add_argument("--interval-seconds", type=int, default=30, help="Seconds between ticks")
    parser.add_argument("--ticks", type=int, help="Number of ticks (omit for infinite)")
    parser.add_argument("--batch-size", type=int, default=25, help="Leads per tick")
    parser.add_argument("--export-artifacts", action="store_true", help="Generate artifacts after run")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("FAST REVENUE MARKETING ENGINE - CAMPAIGN ORCHESTRATOR")
    print("=" * 80)
    print(f"Campaign ID: {args.campaign_id}")
    print(f"Mode: {args.mode}")
    print(f"Interval: {args.interval_seconds}s")
    print(f"Batch size: {args.batch_size}")
    print(f"Ticks: {args.ticks or 'infinite'}")
    print("=" * 80)
    
    tick_count = 0
    
    try:
        while True:
            with get_session() as session:
                # Create orchestrator
                orchestrator = CampaignOrchestrator(
                    session=session,
                    mode=args.mode,
                )
                
                # Execute tick
                now = datetime.utcnow()
                print(f"\n[Tick {tick_count + 1}] {now.isoformat()}")
                
                result = orchestrator.tick(
                    campaign_id=args.campaign_id,
                    now=now,
                    batch_size=args.batch_size,
                )
                
                # Display results
                print(f"  Leads processed: {result.leads_processed}")
                print(f"  Jobs created: {result.jobs_created}")
                print(f"  Attempts succeeded: {result.attempts_succeeded}")
                print(f"  Attempts failed: {result.attempts_failed}")
                
                if result.skipped_dnc:
                    print(f"  Skipped (DNC): {result.skipped_dnc}")
                if result.skipped_unsubscribed:
                    print(f"  Skipped (unsubscribed): {result.skipped_unsubscribed}")
                if result.skipped_suppressed:
                    print(f"  Skipped (suppressed): {result.skipped_suppressed}")
                if result.skipped_quota:
                    print(f"  Skipped (quota): {result.skipped_quota}")
                if result.skipped_idempotent:
                    print(f"  Skipped (idempotent): {result.skipped_idempotent}")
                
                if result.errors:
                    print(f"  Errors: {len(result.errors)}")
                    for error in result.errors[:3]:  # Show first 3
                        print(f"    - {error}")
                
                session.commit()
            
            tick_count += 1
            
            # Check exit condition
            if args.ticks and tick_count >= args.ticks:
                print(f"\nCompleted {tick_count} ticks")
                break
            
            # Wait for next interval
            if not args.ticks:
                time.sleep(args.interval_seconds)
        
        # Generate artifacts if requested
        if args.export_artifacts:
            print("\nGenerating artifacts...")
            with get_session() as session:
                artifacts_dir = generate_artifacts(
                    session=session,
                    campaign_id=args.campaign_id,
                )
                print(f"Artifacts saved to: {artifacts_dir}")
        
        print("\nOrchestrator completed successfully")
        return 0
        
    except KeyboardInterrupt:
        print("\nOrchestrator interrupted by user")
        return 130
    except Exception as e:
        print(f"\nOrchestrator error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
