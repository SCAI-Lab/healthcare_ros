std_msgs/Header header 

string session_id				# Match DeviceInfo's session_id

uint16 sample_size

float32[] eeg		        # Flattened raw or filtered EEG values: length = channel_count * sample_count. Access sample s of channel c as: eeg_flat[c * sample_count + s]

float32[] quality		    # From 0 (poor) to 1 (excellent)
