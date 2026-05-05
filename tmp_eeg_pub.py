import time
import rclpy
from rclpy.node import Node
from healthcare_msgs.msg import EEG
from builtin_interfaces.msg import Time

rclpy.init()
node = Node("eeg_latency_test_publisher")
pub_raw = node.create_publisher(EEG, "/eeg/raw", 10)
pub_proc = node.create_publisher(EEG, "/eeg/processed", 10)
for i in range(10):
    t = time.time()
    sec = int(t)
    nsec = int((t - sec) * 1e9)
    raw = EEG()
    raw.header.stamp = Time(sec=sec, nanosec=nsec)
    raw.header.frame_id = "raw"
    proc = EEG()
    proc.header.stamp = Time(sec=sec, nanosec=nsec + 30000000)
    proc.header.frame_id = "processed"
    pub_raw.publish(raw)
    pub_proc.publish(proc)
    time.sleep(0.1)
rclpy.shutdown()
