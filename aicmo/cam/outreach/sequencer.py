"""
Channel Sequencer

Orchestrates multi-channel outreach sequences.
Implements fallback logic: Email → LinkedIn → Contact Form
Phase B: Step 4 - Core sequencing logic
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

from aicmo.cam.domain import (
    OutreachMessage,
    ChannelType,
    OutreachStatus,
    SequenceConfig,
    SequenceStep,
)
from aicmo.cam.outreach import OutreachServiceBase, OutreachResult
from aicmo.cam.outreach.email_outreach import EmailOutreachService
from aicmo.cam.outreach.linkedin_outreach import LinkedInOutreachService
from aicmo.cam.outreach.contact_form_outreach import ContactFormOutreachService

logger = logging.getLogger(__name__)


class FailureReason(str, Enum):
    """Reasons why a channel attempt might fail."""
    DELIVERY_FAILED = "delivery_failed"
    RATE_LIMITED = "rate_limited"
    INVALID_ADDRESS = "invalid_address"
    BOUNCE = "bounce"
    COMPLAINT = "complaint"
    NO_PROFILE = "no_profile"
    FORM_UNREACHABLE = "form_unreachable"
    FORM_SPAM_PROTECTED = "form_spam_protected"
    RETRY_EXHAUSTED = "retry_exhausted"


class ChannelSequencer:
    """
    Orchestrates multi-channel outreach sequences.
    
    Implements sequential fallback logic:
    1. Try primary channel (usually Email)
    2. If fails with certain conditions, try fallback channel (LinkedIn)
    3. If fails again, try final fallback (Contact Form)
    4. Track all attempts and retry logic
    """
    
    def __init__(self):
        """Initialize sequencer with all channel services."""
        self.email_service = EmailOutreachService()
        self.linkedin_service = LinkedInOutreachService()
        self.form_service = ContactFormOutreachService()
        
        self.services: Dict[ChannelType, OutreachServiceBase] = {
            ChannelType.EMAIL: self.email_service,
            ChannelType.LINKEDIN: self.linkedin_service,
            ChannelType.CONTACT_FORM: self.form_service,
        }
    
    def execute_sequence(
        self,
        message: OutreachMessage,
        recipient_email: Optional[str] = None,
        recipient_linkedin_id: Optional[str] = None,
        form_url: Optional[str] = None,
        sequence_config: Optional[SequenceConfig] = None,
        retry_count: int = 0,
        max_retries: int = 1,
    ) -> Dict[str, Any]:
        """
        Execute a multi-channel outreach sequence.
        
        Tries channels in order, falling back based on failure reason.
        Tracks all attempts for audit trail.
        
        Args:
            message: Outreach message to send
            recipient_email: Email address (for Email and Contact Form)
            recipient_linkedin_id: LinkedIn profile ID (for LinkedIn)
            form_url: Contact form URL (for Contact Form)
            sequence_config: Optional sequence configuration with fallback rules
            retry_count: Current retry attempt number
            max_retries: Maximum retry attempts allowed
            
        Returns:
            Dictionary with:
            - success: Boolean indicating overall success
            - message_id: ID of sent message
            - channel_used: ChannelType that succeeded
            - attempts: List of all attempts made
            - final_status: OutreachStatus
        """
        
        # Build default sequence if not provided
        if not sequence_config:
            sequence_config = self._build_default_sequence()
        
        attempts: List[Dict[str, Any]] = []
        final_result = None
        channel_used = None
        
        # Execute channels in sequence order
        for step in sequence_config.steps:
            if final_result and final_result.success:
                break
            
            attempt = {
                'channel': step.channel.value,
                'timestamp': datetime.utcnow().isoformat(),
                'retry_count': retry_count,
            }
            
            try:
                # Route to appropriate service
                result = self._send_via_channel(
                    step.channel,
                    message,
                    recipient_email,
                    recipient_linkedin_id,
                    form_url,
                )
                
                attempt['success'] = result.success
                attempt['status'] = result.status.value
                attempt['message_id'] = result.message_id
                
                if result.error:
                    attempt['error'] = result.error
                
                attempts.append(attempt)
                
                # If successful, record and potentially stop
                if result.success:
                    final_result = result
                    channel_used = step.channel
                    logger.info(
                        f"Message sent successfully via {step.channel.value} "
                        f"(ID: {result.message_id})"
                    )
                    break
                
                # If failed, check if there are more steps (fallback enabled)
                is_last_step = step.order == len(sequence_config.steps)
                if is_last_step:
                    logger.warning(
                        f"Final channel {step.channel.value} failed, no more fallbacks"
                    )
                    break
                
                # Determine if this failure warrants fallback
                if self._should_fallback(result, step):
                    logger.info(
                        f"Channel {step.channel.value} failed, trying fallback"
                    )
                    continue
                else:
                    # Fatal error, don't try fallbacks
                    logger.error(
                        f"Channel {step.channel.value} failed with non-recoverable error"
                    )
                    break
            
            except Exception as e:
                logger.error(
                    f"Exception sending via {step.channel.value}: {str(e)}"
                )
                attempt['success'] = False
                attempt['error'] = str(e)
                attempts.append(attempt)
        
        # If no successful result yet, determine final failure state
        if not final_result:
            final_result = OutreachResult(
                success=False,
                channel=attempts[-1]['channel'] if attempts else None,
                status=OutreachStatus.FAILED,
                error="All channels exhausted"
            )
        
        return {
            'success': final_result.success,
            'message_id': final_result.message_id,
            'channel_used': channel_used.value if channel_used else None,
            'attempts': attempts,
            'final_status': final_result.status.value,
            'retry_count': retry_count,
            'max_retries': max_retries,
        }
    
    def _send_via_channel(
        self,
        channel: ChannelType,
        message: OutreachMessage,
        recipient_email: Optional[str],
        recipient_linkedin_id: Optional[str],
        form_url: Optional[str],
    ) -> OutreachResult:
        """
        Send message via specified channel.
        
        Args:
            channel: ChannelType to use
            message: Message to send
            recipient_email: Email address
            recipient_linkedin_id: LinkedIn ID
            form_url: Form URL
            
        Returns:
            OutreachResult from the channel service
        """
        service = self.services.get(channel)
        
        if not service:
            logger.error(f"No service found for channel {channel}")
            return OutreachResult(
                success=False,
                channel=channel,
                status=OutreachStatus.FAILED,
                error=f"No service for channel {channel.value}"
            )
        
        return service.send(
            message,
            recipient_email=recipient_email,
            recipient_linkedin_id=recipient_linkedin_id,
            form_url=form_url,
        )
    
    def _should_fallback(
        self,
        result: OutreachResult,
        step: SequenceStep,
    ) -> bool:
        """
        Determine if a failure should trigger fallback to next channel.
        
        Args:
            result: Result from channel attempt
            step: Sequence step configuration
            
        Returns:
            True if should try next channel, False if fatal
        """
        if result.success:
            return False
        
        # Failures that warrant fallback
        fallback_worthy_errors = {
            'rate limited',
            'invalid',
            'bounce',
            'no profile',
        }
        
        if result.error:
            error_lower = result.error.lower()
            return any(
                err in error_lower
                for err in fallback_worthy_errors
            )
        
        # Default: try fallback
        return True
    
    def _build_default_sequence(self) -> SequenceConfig:
        """
        Build default sequence: Email → LinkedIn → Contact Form
        
        Returns:
            SequenceConfig with default steps
        """
        return SequenceConfig(
            name="default_sequence",
            description="Default: Email → LinkedIn → Contact Form",
            steps=[
                SequenceStep(
                    order=1,
                    channel=ChannelType.EMAIL,
                    message_template="email_intro",
                ),
                SequenceStep(
                    order=2,
                    channel=ChannelType.LINKEDIN,
                    message_template="linkedin_dm",
                ),
                SequenceStep(
                    order=3,
                    channel=ChannelType.CONTACT_FORM,
                    message_template="contact_form_submit",
                ),
            ],
        )
    
    def schedule_retry(
        self,
        attempt_result: Dict[str, Any],
        delay_minutes: int = 60,
        max_retries: int = 3,
    ) -> Optional[datetime]:
        """
        Schedule a retry for a failed outreach attempt.
        
        Args:
            attempt_result: Result dictionary from execute_sequence()
            delay_minutes: Minutes to wait before retry
            max_retries: Maximum total retries allowed
            
        Returns:
            Scheduled retry datetime, or None if max retries reached
        """
        current_retry = attempt_result.get('retry_count', 0)
        
        if current_retry >= max_retries:
            logger.warning(
                f"Max retries ({max_retries}) reached for message "
                f"{attempt_result.get('message_id')}"
            )
            return None
        
        next_retry = datetime.utcnow() + timedelta(minutes=delay_minutes)
        
        logger.info(
            f"Scheduled retry for message {attempt_result.get('message_id')} "
            f"at {next_retry.isoformat()}"
        )
        
        return next_retry
    
    def get_sequence_metrics(
        self,
        attempts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate metrics from a sequence of attempts.
        
        Args:
            attempts: List of attempt dictionaries from execute_sequence()
            
        Returns:
            Dictionary with:
            - total_attempts: Number of channels tried
            - successful_channels: List of channels that succeeded
            - failed_channels: List of channels that failed
            - success_rate: Percentage of successful attempts
        """
        if not attempts:
            return {
                'total_attempts': 0,
                'successful_channels': [],
                'failed_channels': [],
                'success_rate': 0.0,
            }
        
        successful = [a for a in attempts if a.get('success')]
        failed = [a for a in attempts if not a.get('success')]
        
        return {
            'total_attempts': len(attempts),
            'successful_channels': [a['channel'] for a in successful],
            'failed_channels': [a['channel'] for a in failed],
            'success_rate': len(successful) / len(attempts) * 100,
        }
