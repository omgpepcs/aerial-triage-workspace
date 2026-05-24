import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand
from std_msgs.msg import String
import math
import json

class PX4Navigator(Node):
    def __init__(self):
        super().__init__('px4_navigator')
        qos_profile = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.TRANSIENT_LOCAL, history=HistoryPolicy.KEEP_LAST, depth=1)
        self.offboard_control_mode_publisher = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_publisher = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos_profile)
        
        self.victim_sub = self.create_subscription(String, 'victim_data', self.hover_callback, 10)
        
        self.nav_state = "TAKEOFF"
        self.offboard_setpoint_counter = 0
        
        self.px4_x, self.px4_y = 0.0, 0.0
        self.current_yaw = 0.0
        self.hover_timer = 0
        
        self.waypoints = self.generate_zigzag_pattern()
        self.wp_index = 0
        self.target_x, self.target_y = self.waypoints[self.wp_index]
        
        # Keep the height at 5m. At a distance of 5.5m, the 45º angle nails it in the center.
        self.height_patrol = -5.0
        self.height_inspection = -5.0 
        
        self.timer = self.create_timer(0.1, self.timer_callback)

    def generate_zigzag_pattern(self):
        waypoints = []
        x_start, x_end = 15.0, -35.0
        y_top, y_bottom = 25.0, -30.0
        sidestep = 5.0
        x, direction = x_start, -1
        while x >= x_end:
            waypoints.append((x, y_bottom if direction == -1 else y_top))
            x -= sidestep
            waypoints.append((x, y_bottom if direction == -1 else y_top))
            direction *= -1
        return waypoints

    def hover_callback(self, msg):
        if self.nav_state == "PATROL":
            try:
                data = json.loads(msg.data)
                offset_x = float(data['offset_x'])
                offset_y = float(data['offset_y'])
                
                # TURRET MODE: We do NOT use px4_x or px4_y.
                self.current_yaw = math.atan2(offset_y, offset_x)
                
                self.get_logger().info('[STATIC TURRET] Brakes locked. Camera turning towards the victim...')
                self.nav_state = "HOVER"
                self.hover_timer = 300
            except Exception as e:
                pass

    def publish_vehicle_command(self, command, **params):
        msg = VehicleCommand()
        msg.command = command
        msg.param1, msg.param2 = params.get("param1", 0.0), params.get("param2", 0.0)
        msg.target_system, msg.target_component, msg.source_system, msg.source_component = 1, 1, 1, 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)

    def timer_callback(self):
        offboard_msg = OffboardControlMode()
        offboard_msg.position = True
        offboard_msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_publisher.publish(offboard_msg)
        
        trajectory_msg = TrajectorySetpoint()
        trajectory_msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)

        if self.nav_state == "TAKEOFF":
            trajectory_msg.position = [0.0, 0.0, self.height_patrol]
            trajectory_msg.yaw = self.current_yaw
            
            if self.offboard_setpoint_counter % 20 == 0 and self.offboard_setpoint_counter < 100:
                self.get_logger().info(f'Calibrating GPS... {5 - (self.offboard_setpoint_counter // 20)}s')

            if self.offboard_setpoint_counter == 100:
                self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
                self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
            
            if self.offboard_setpoint_counter > 150:
                self.nav_state = "PATROL"

        elif self.nav_state == "PATROL":
            dx = self.target_x - self.px4_x
            dy = self.target_y - self.px4_y
            dist = math.hypot(dx, dy)

            if dist < 0.8:
                self.wp_index += 1
                if self.wp_index < len(self.waypoints):
                    self.target_x, self.target_y = self.waypoints[self.wp_index]
                else:
                    self.nav_state = "RTL"
            else:
                vel = 0.25
                self.px4_x += (dx/dist) * vel
                self.px4_y += (dy/dist) * vel
                
                target_yaw = math.atan2(dy, dx)
                diff_yaw = math.atan2(math.sin(target_yaw - self.current_yaw), math.cos(target_yaw - self.current_yaw))
                self.current_yaw += diff_yaw * 0.05 
                
                trajectory_msg.position = [self.px4_x, self.px4_y, self.height_patrol]
                trajectory_msg.yaw = self.current_yaw

        elif self.nav_state == "HOVER":
            # THE DRONE IS FROZEN. Only updates the YAW to rotate.
            trajectory_msg.position = [self.px4_x, self.px4_y, self.height_inspection]
            trajectory_msg.yaw = self.current_yaw

            self.hover_timer -= 1
            if self.hover_timer <= 0:
                self.nav_state = "PATROL" 

        elif self.nav_state == "RTL":
            trajectory_msg.position = [0.0, 0.0, self.height_patrol]
            trajectory_msg.yaw = self.current_yaw
            if math.hypot(self.px4_x, self.px4_y) < 0.5: self.nav_state = "LAND"
        
        elif self.nav_state == "LAND":
            trajectory_msg.position = [0.0, 0.0, 0.0]
            trajectory_msg.yaw = self.current_yaw

        self.trajectory_setpoint_publisher.publish(trajectory_msg)
        self.offboard_setpoint_counter += 1

def main(args=None):
    rclpy.init(args=args)
    node = PX4Navigator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
