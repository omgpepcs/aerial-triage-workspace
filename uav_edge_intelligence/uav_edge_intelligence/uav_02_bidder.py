import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import random
import math

class VirtualSwarmBidders(Node):
    """this class only operates if there is no GCS, used mainly to debug. System uses SeverityScore code in GCS host"""
    def __init__(self):
        super().__init__('virtual_swarm_bidders')
        self.sub = self.create_subscription(String, 'victim_data', self.auction_callback, 10)
        self.vitals_pub = self.create_publisher(String, 'victim_vitals', 10)
        
        # Fleet of medic drones available
        self.free_drones = ["Medic_Drone_1", "Medic_Drone_2", "Medic_Drone_3"]
        self.active_missions = {} # To monitor multiple victims at once

        self.timer = self.create_timer(2.0, self.monitor_callback) # Update status every 2 seconds
        self.get_logger().info('[EDGE FLEET] Drones 2, 3, and 4 at Base. Awaiting triage auctions...')

    def auction_callback(self, msg):
        data = json.loads(msg.data)
        vid = data["id"]
        previous_pose = data.get("pose", "Unknown")
        
        # If no medic is required, the fleet ignores the alert
        if not data["req_medic"]:
            self.get_logger().info(f'[GCS ALERT] Victim {vid} unharmed. Ground rescue en route. Fleet ignores.')
            return
            
        if not self.free_drones:
            self.get_logger().info('[GCS ALERT] NO FREE DRONES. Victim on waiting list.')
            return

        self.get_logger().info(f'\n--- STARTING AUCTION FOR VICTIM {vid} ---')
        
        bids = []
        for drone in self.free_drones:
            battery = random.randint(30, 100) # Random battery
            # Simulate that the drones were spread across the map
            dist = random.uniform(10.0, 80.0) 
            
            # BIDDING FORMULA: Having battery power is a plus, but being far away is a penalty.
            score = battery - (dist * 0.5)
            bids.append({"drone": drone, "battery": battery, "distance": dist, "score": score})
            self.get_logger().info(f' -> {drone} bid: Battery {battery}%, distance {dist:.1f}m (Score: {score:.1f})')
            
        # Sort score
        bids.sort(key=lambda x: x["score"], reverse=True)
        winner = bids[0]["drone"]
        
        self.get_logger().info(f'winner: {winner}. Assigned to {vid}. Taking off...')
        self.get_logger().info('------------------------------------------------')
        
        # We save the mission, remove the drone from the list, and set it to initial phase
        self.free_drones.remove(winner)
        self.active_missions[vid] = {
            "drone": winner,
            "pose": previous_pose,
            "phase": "TRAVELING",  # Phases: TRAVELING -> SCANNING -> MONITORING
            "ticks": 0           # Sim time
        }

    def monitor_callback(self):
        # Explore all active missions and advance their status
        for vid, info in list(self.active_missions.items()):
            info["ticks"] += 1

            # 1. TRAVEL phase (Takes about 4 seconds to arrive)
            if info["phase"] == "TRAVELING":
                if info["ticks"] >= 2:
                    self.get_logger().info(f"\n[{info['drone']}] Position reached. Starting medical scan over {vid}...")
                    info["phase"] = "SCANNING"

            # 2. SCANNING phase (Calculates the constants and the SGI)
            elif info["phase"] == "SCANNING":
                self.get_logger().info(f"[{info['drone']}] Processing {vid} biometrics...")
                
                # Generate vital signs consistent with the pose
                if info["pose"].upper() in ["LAYING", "SITTING"]:
                    bpm = random.randint(30, 55)
                    spo2 = random.randint(82, 91)
                    rpm = random.randint(8, 14)
                else:
                    bpm = random.randint(65, 110)
                    spo2 = random.randint(94, 99)
                    rpm = random.randint(12, 20)

                self.get_logger().info(f"[{info['drone']}] VITAL SIGNS OBTAINED:")
                self.get_logger().info(f"    Heart beat: {bpm} BPM")
                self.get_logger().info(f"    Oxygen (SpO2): {spo2} %")
                self.get_logger().info(f"    Respiratory Rate: {rpm} RPM")

                # SGI CALCULATOR
                if bpm < 40 or spo2 < 88:
                    sgi = "CRITICAL"
                elif bpm < 60 or spo2 < 93:
                    sgi = "URGENT"
                elif bpm > 100:
                    sgi = "STABLE"
                else:
                    sgi = "NORMAL"

                self.get_logger().info(f"[{info['drone']}] SGI RESULT: {sgi}")
                
                # Save the final SGI and move on to continuous monitoring
                info["sgi"] = sgi
                info["phase"] = "MONITORING"

            # 3. MONITORING PHASE (Sends data back to the GCS)
            elif info["phase"] == "MONITORING":
                vital_signs = {
                    "victim_id": vid, 
                    "sgi": info["sgi"], 
                    "assigned_drone": info["drone"]
                }
                msg = String()
                msg.data = json.dumps(vital_signs)
                self.vitals_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = VirtualSwarmBidders()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
