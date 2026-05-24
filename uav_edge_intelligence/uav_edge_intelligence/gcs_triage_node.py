import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os
import csv

class GCSTriageNode(Node):
    def __init__(self):
        super().__init__('gcs_triage_node')
        self.sub_data = self.create_subscription(String, 'victim_data', self.data_callback, 10)
        self.sub_vitals = self.create_subscription(String, 'victim_vitals', self.vitals_callback, 10)
        
        self.db = {} 

    def data_callback(self, msg):
        import json
        data = json.loads(msg.data)
        vid = data.get("id", "Unknown")
        
        if vid not in self.db:
            self.db[vid] = {
                "ID": vid,
                # .get() so that if there is neither 'x' nor 'y', puts 0.0 and doesn't crash
                "Location_X": round(data.get('x', 0.0), 2),
                "Location_Y": round(data.get('y', 0.0), 2),
                "Pose": data.get("pose", "Unknown"),
                "Req_medic": "YES" if data.get("req_medic", False) else "NO",
                "SGI": data.get("sgi", "N/A") if data.get("req_medic", False) else "N/A",
                "Assigned_Unit": "Auction pending..." if data.get("req_medic", False) else "Ground patrol"
            }

    def vitals_callback(self, msg):
        data = json.loads(msg.data)
        vid = data["victim_id"]
        
        if vid in self.db:
            self.db[vid]["SGI"] = data["sgi"]
            self.db[vid]["Assigned_Unit"] = data["assigned_drone"]

def main(args=None):
    rclpy.init(args=args)
    node = GCSTriageNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()

if __name__ == '__main__':
    main()
