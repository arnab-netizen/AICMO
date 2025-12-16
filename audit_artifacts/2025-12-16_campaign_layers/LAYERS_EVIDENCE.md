# Campaign Layers Evidence Collection

## LAYER 1: Campaign Definition Layer

### Search 1: Campaign Table
```
Campaign Definition Model (cam_campaigns table found ✅)
```

### Evidence Files Found:
### Layer 1: Campaign Definition Data Model
39:    __tablename__ = "cam_campaigns"

Model file: aicmo/cam/db_models.py


## LAYER 2: Content Calendar / Scheduling Layer
aicmo/cam/auto.py:18:from aicmo.cam.outreach.sequencer import ChannelSequencer
aicmo/cam/auto.py:38:       c. Execute multi-channel sequence (Email → LinkedIn → Contact Form)
aicmo/cam/auto.py:42:    Uses ChannelSequencer to intelligently route through channels,
aicmo/cam/auto.py:52:        dry_run: If True, generate messages but don't execute sequences
aicmo/cam/auto.py:79:    sequencer = ChannelSequencer()
aicmo/cam/auto.py:91:                sequence=SequenceConfig(channel=Channel.EMAIL, steps=1),
aicmo/cam/auto.py:128:                # Execute multi-channel sequence
aicmo/cam/auto.py:129:                sequence_result = sequencer.execute_sequence(
aicmo/cam/auto.py:137:                if sequence_result['success']:
aicmo/cam/auto.py:139:                    channel = sequence_result.get('channel_used', 'unknown')
