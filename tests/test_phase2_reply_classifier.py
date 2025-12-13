"""
Phase 2: IMAP inbox and reply classification tests.
"""

import pytest
from datetime import datetime
from aicmo.cam.services.reply_classifier import ReplyClassifier, ReplyClassification


class TestReplyClassifier:
    """Tests for email reply classification."""
    
    def test_classifier_init(self):
        """Test classifier can be initialized."""
        classifier = ReplyClassifier()
        assert classifier is not None
    
    def test_classify_positive_response(self):
        """Test positive response detection."""
        classifier = ReplyClassifier()
        
        classification, confidence, reason = classifier.classify(
            subject="RE: Great opportunity",
            body="Hey! I'm very interested in this. Let's talk more about it.",
        )
        
        assert classification == ReplyClassification.POSITIVE
        assert confidence > 0.0
        assert "positive" in reason.lower() or "interest" in reason.lower()
    
    def test_classify_negative_response(self):
        """Test negative response detection."""
        classifier = ReplyClassifier()
        
        classification, confidence, reason = classifier.classify(
            subject="RE: Your message",
            body="Not interested, I cannot help with this project.",
        )
        
        assert classification == ReplyClassification.NEGATIVE
        assert confidence > 0.0
    
    def test_classify_ooo_response(self):
        """Test out-of-office detection."""
        classifier = ReplyClassifier()
        
        classification, confidence, reason = classifier.classify(
            subject="Out of office auto-reply",
            body="I am out of the office returning December 15th.",
        )
        
        assert classification == ReplyClassification.OOO
        assert confidence > 0.0
    
    def test_classify_bounce_response(self):
        """Test bounce/delivery failure detection."""
        classifier = ReplyClassifier()
        
        classification, confidence, reason = classifier.classify(
            subject="Mail Delivery Failed",
            body="This address is invalid and the email was undeliverable.",
        )
        
        assert classification == ReplyClassification.BOUNCE
        assert confidence > 0.0
    
    def test_classify_unsub_response(self):
        """Test unsubscribe detection."""
        classifier = ReplyClassifier()
        
        classification, confidence, reason = classifier.classify(
            subject="Unsubscribe",
            body="Please unsubscribe me from your mailing list.",
        )
        
        assert classification == ReplyClassification.UNSUB
        assert confidence > 0.0
    
    def test_classify_neutral_response(self):
        """Test neutral response (no clear signals)."""
        classifier = ReplyClassifier()
        
        classification, confidence, reason = classifier.classify(
            subject="RE: Your message",
            body="Thanks for reaching out. I'll look into this.",
        )
        
        assert classification == ReplyClassification.NEUTRAL
        assert confidence == 0.0
    
    def test_classify_case_insensitive(self):
        """Test classification is case-insensitive."""
        classifier = ReplyClassifier()
        
        classification1, _, _ = classifier.classify(
            subject="INTERESTED",
            body="I AM VERY INTERESTED IN THIS OPPORTUNITY",
        )
        
        classification2, _, _ = classifier.classify(
            subject="interested",
            body="i am very interested in this opportunity",
        )
        
        assert classification1 == classification2 == ReplyClassification.POSITIVE
    
    def test_classify_negative_priority_over_positive(self):
        """Test that explicit rejection takes priority over positive signals."""
        classifier = ReplyClassifier()
        
        classification, _, _ = classifier.classify(
            subject="Interested but not available",
            body="I'm interested but I'm not available right now and cannot help.",
        )
        
        # Should lean toward negative due to explicit 'cannot'
        assert classification in (ReplyClassification.NEGATIVE, ReplyClassification.NEUTRAL)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
