import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import String
import json
import math

class SwarmFleetController(Node):
    def __init__(self):
        super().__init__('swarm_fleet_controller')
        
        self.rviz_pub = self.create_publisher(MarkerArray, '/mission_map_markers', 10)
        self.sub = self.create_subscription(String, 'victim_data', self.victim_callback, 10)

        self.fleet = {
            "drone_2_dummy": {"x": -10.0, "y": -10.0, "yaw": 0.0, "tx": None, "ty": None, "status": "IDLE"},
            "drone_3_dummy": {"x": -10.0, "y": -12.0, "yaw": 0.0, "tx": None, "ty": None, "status": "IDLE"},
            "drone_4_dummy": {"x": -10.0, "y": -14.0, "yaw": 0.0, "tx": None, "ty": None, "status": "IDLE"}
        }
        
        self.speed = 5.0      
        self.altitude = 8.0   
        self.dispatched_victims = set() 

        self.timer = self.create_timer(0.05, self.update_fleet)
        self.get_logger().info('[SWARM COMMAND] Fleet initialized. Unified Tactic Radar.')

    def victim_callback(self, msg):
        try:
            data = json.loads(msg.data)
            vid = data.get("id", "Unknown")
            vx = float(data.get('x', 0.0))
            vy = float(data.get('y', 0.0))
            
            if vid in self.dispatched_victims: return

            available_drone = None
            for name, drone in self.fleet.items():
                if drone["status"] == "IDLE":
                    available_drone = name
                    break
            
            if available_drone:
                self.fleet[available_drone]["tx"] = vx
                self.fleet[available_drone]["ty"] = vy
                self.fleet[available_drone]["status"] = "FLYING"
                self.dispatched_victims.add(vid)
                
                uav_id = available_drone.replace("_dummy", "").upper()
                self.get_logger().info(f'[{uav_id}] Dispatch received! Target: X={vx:.1f}, Y={vy:.1f}')
                self.get_logger().info(f'[{uav_id}] Auction won. Initiating flight sequence...')
        except Exception as e:
            pass

    def update_fleet(self):
        marker_array = MarkerArray()
        idx = 0
        
        for name, drone in self.fleet.items():
            # State handler for stationary or grounded aerial assets.
            if drone["status"] != "FLYING":
                self.add_rviz_marker(marker_array, idx, drone["x"], drone["y"], 0.2)
                idx += 1
                continue

            dx = drone["tx"] - drone["x"]
            dy = drone["ty"] - drone["y"]
            dist = math.hypot(dx, dy)

            # Target coordinates waypoint validation.
            if dist < 0.5:
                if drone["status"] != "ARRIVED":
                    uav_id = name.replace("_dummy", "").upper()
                    self.get_logger().info(f'[{uav_id}] Arrived at target location. Initiating protocol.')
                drone["status"] = "ARRIVED"
                self.add_rviz_marker(marker_array, idx, drone["x"], drone["y"], 0.2)
                idx += 1
                continue

            # Kinematic state updates for flight trajectory simulation.
            move_step = self.speed * 0.05
            drone["x"] += (dx / dist) * move_step
            drone["y"] += (dy / dist) * move_step
            
            self.add_rviz_marker(marker_array, idx, drone["x"], drone["y"], self.altitude)
            idx += 1
            
        self.rviz_pub.publish(marker_array)

    def add_rviz_marker(self, array, idx, x, y, z):
        m = Marker()
        m.header.frame_id = "map"
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = "dummy_drones"
        m.id = 5000 + idx
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x = float(x)
        m.pose.position.y = float(y)
        m.pose.position.z = float(z)
        m.scale.x = 0.8; m.scale.y = 0.8; m.scale.z = 0.8
        # Color light blue/cyan for swarm
        m.color.r = 0.0; m.color.g = 1.0; m.color.b = 1.0; m.color.a = 1.0
        array.markers.append(m)

def main(args=None):
    rclpy.init(args=args)
    node = SwarmFleetController()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
