"""
CAM Phase 7 - Lead Discovery Service.

Orchestrates discovery jobs across multiple platforms with ethical compliance.
"""

from typing import List, Optional
from datetime import datetime
import json

from sqlalchemy.orm import Session

from aicmo.cam.discovery_domain import (
    DiscoveryCriteria,
    DiscoveryJob,
    DiscoveredProfile,
    Platform,
)
from aicmo.cam.db_models import (
    DiscoveryJobDB,
    DiscoveredProfileDB,
    LeadDB,
    LeadSource,
    LeadStatus,
)
from aicmo.cam.platforms import linkedin_source, twitter_source, instagram_source


def create_discovery_job(
    db: Session,
    campaign_id: int,
    name: str,
    criteria: DiscoveryCriteria,
) -> DiscoveryJobDB:
    """
    Create a new discovery job.
    
    Args:
        db: Database session
        campaign_id: Campaign to attach discovered leads to
        name: Human-readable job name
        criteria: Search criteria
        
    Returns:
        Created DiscoveryJobDB instance
    """
    job_db = DiscoveryJobDB(
        name=name,
        campaign_id=campaign_id,
        criteria=criteria.model_dump(),  # Serialize to JSON
        status="PENDING",
    )
    db.add(job_db)
    db.commit()
    db.refresh(job_db)
    return job_db


def run_discovery_job(
    db: Session,
    job_id: int,
) -> List[DiscoveredProfile]:
    """
    Execute a discovery job across configured platforms.
    
    Process:
    1. Load job and criteria
    2. For each platform, call appropriate source.search()
    3. Normalize results into DiscoveredProfile objects
    4. Persist profiles to database
    5. Update job status
    
    Args:
        db: Database session
        job_id: Job ID to execute
        
    Returns:
        List of discovered profiles
        
    Raises:
        ValueError: If job not found or already completed
    """
    # Load job
    job_db = db.get(DiscoveryJobDB, job_id)
    if not job_db:
        raise ValueError(f"Discovery job {job_id} not found")
    
    if job_db.status in ["DONE", "FAILED"]:
        raise ValueError(f"Job {job_id} already completed with status {job_db.status}")
    
    # Update status to RUNNING
    job_db.status = "RUNNING"
    db.commit()
    
    try:
        # Parse criteria
        criteria = DiscoveryCriteria(**job_db.criteria)
        
        all_profiles: List[DiscoveredProfile] = []
        
        # Search each platform
        for platform in criteria.platforms:
            try:
                if platform == Platform.LINKEDIN:
                    profiles = linkedin_source.search(criteria)
                elif platform == Platform.TWITTER:
                    profiles = twitter_source.search(criteria)
                elif platform == Platform.INSTAGRAM:
                    profiles = instagram_source.search(criteria)
                elif platform == Platform.WEB:
                    # TODO: Integrate with external provider (Apollo, etc.)
                    profiles = []
                else:
                    profiles = []
                
                # Add job_id to each profile
                for profile in profiles:
                    profile.job_id = job_id
                
                all_profiles.extend(profiles)
                
            except Exception as e:
                # Log platform error but continue with other platforms
                print(f"Error searching {platform}: {e}")
                continue
        
        # Persist profiles to database
        for profile in all_profiles:
            profile_db = DiscoveredProfileDB(
                job_id=job_id,
                platform=profile.platform.value,
                handle=profile.handle,
                profile_url=profile.profile_url,
                display_name=profile.display_name,
                bio=profile.bio,
                followers=profile.followers,
                location=profile.location,
                match_score=profile.match_score,
            )
            db.add(profile_db)
        
        # Mark job as DONE
        job_db.status = "DONE"
        job_db.completed_at = datetime.utcnow()
        db.commit()
        
        return all_profiles
        
    except Exception as e:
        # Mark job as FAILED
        job_db.status = "FAILED"
        job_db.error_message = str(e)
        job_db.completed_at = datetime.utcnow()
        db.commit()
        raise


def convert_profiles_to_leads(
    db: Session,
    profile_ids: List[int],
    campaign_id: int,
) -> int:
    """
    Convert discovered profiles to CAM leads.
    
    Args:
        db: Database session
        profile_ids: List of DiscoveredProfileDB IDs to convert
        campaign_id: Campaign to attach leads to
        
    Returns:
        Number of leads created (excludes duplicates)
    """
    created_count = 0
    
    for profile_id in profile_ids:
        profile_db = db.get(DiscoveredProfileDB, profile_id)
        if not profile_db:
            continue
        
        # Check if lead already exists (by profile_url or handle)
        existing = (
            db.query(LeadDB)
            .filter(
                LeadDB.campaign_id == campaign_id,
                (LeadDB.linkedin_url == profile_db.profile_url)
                | (LeadDB.name == profile_db.display_name),
            )
            .first()
        )
        
        if existing:
            continue  # Skip duplicate
        
        # Create new lead
        lead_db = LeadDB(
            campaign_id=campaign_id,
            name=profile_db.display_name,
            company=None,  # Not available in basic profile discovery
            role=None,  # Extract from bio if available
            email=None,  # Not available from social platforms
            linkedin_url=profile_db.profile_url if profile_db.platform == "linkedin" else None,
            source=LeadSource.OTHER,  # Or create DISCOVERY source
            status=LeadStatus.NEW,
            notes=f"Discovered via job. Bio: {profile_db.bio[:200] if profile_db.bio else 'N/A'}",
        )
        db.add(lead_db)
        created_count += 1
    
    db.commit()
    return created_count


def list_discovery_jobs(
    db: Session,
    campaign_id: Optional[int] = None,
) -> List[DiscoveryJobDB]:
    """
    List discovery jobs, optionally filtered by campaign.
    
    Args:
        db: Database session
        campaign_id: Optional campaign filter
        
    Returns:
        List of DiscoveryJobDB instances
    """
    query = db.query(DiscoveryJobDB)
    
    if campaign_id is not None:
        query = query.filter(DiscoveryJobDB.campaign_id == campaign_id)
    
    return query.order_by(DiscoveryJobDB.created_at.desc()).all()


def list_discovered_profiles(
    db: Session,
    job_id: int,
) -> List[DiscoveredProfileDB]:
    """
    List profiles discovered by a specific job.
    
    Args:
        db: Database session
        job_id: Discovery job ID
        
    Returns:
        List of DiscoveredProfileDB instances
    """
    return (
        db.query(DiscoveredProfileDB)
        .filter(DiscoveredProfileDB.job_id == job_id)
        .order_by(DiscoveredProfileDB.match_score.desc())
        .all()
    )
