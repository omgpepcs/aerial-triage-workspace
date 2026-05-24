import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from std_msgs.msg import String
from gazebo_msgs.msg import ModelStates
import json

class MapVisualizer(Node):
    def __init__(self):
        super().__init__('map_visualizer_node')
        
        self.sub_victims = self.create_subscription(String, 'victim_data', self.victim_callback, 10)
        self.sub_drone = self.create_subscription(ModelStates, '/model_states', self.drone_callback, 10)
        self.marker_pub = self.create_publisher(MarkerArray, '/mission_map_markers', 10)
        
        self.drawn_victims = set() 
        self.marker_array = MarkerArray()
        self.id_counter = 1 
        
        self.draw_base()
        self.draw_vector_map()
        
        self.create_timer(1.0, self.force_pub)
        self.get_logger().info('🗺️ Tactical Vector Radar started. 100% Optimized.')

    def force_pub(self):
        self.marker_pub.publish(self.marker_array)

    def draw_base(self):
        base_marker = Marker()
        base_marker.header.frame_id = "map"
        base_marker.ns = "base"
        base_marker.id = 0
        base_marker.type = Marker.CUBE
        base_marker.action = Marker.ADD
        base_marker.pose.position.x = 0.0
        base_marker.pose.position.y = 0.0
        base_marker.pose.position.z = 0.2
        base_marker.scale.x = 0.8; base_marker.scale.y = 0.8; base_marker.scale.z = 0.8
        base_marker.color.r = 0.0; base_marker.color.g = 0.5; base_marker.color.b = 1.0; base_marker.color.a = 1.0
        self.marker_array.markers.append(base_marker)

    def draw_vector_map(self):
        """Draw the outline of buildings and roads using only lines (0 lag)"""
        # ROAD (Grey)
        road = Marker()
        road.header.frame_id = "map"
        road.ns = "environment_lines"
        road.id = 20001
        road.type = Marker.LINE_STRIP
        road.action = Marker.ADD
        road.scale.x = 0.5 # Line thickness
        road.color.r = 0.5; road.color.g = 0.5; road.color.b = 0.5; road.color.a = 1.0
        # Coords road
        rp1 = Point(x=-40.0, y=-5.0, z=0.0); rp2 = Point(x=20.0, y=-5.0, z=0.0)
        rp3 = Point(x=20.0, y=5.0, z=0.0); rp4 = Point(x=-40.0, y=5.0, z=0.0)
        road.points = [rp1, rp2, rp3, rp4, rp1]
        self.marker_array.markers.append(road)

        # POST OFFICE BUILDING (Neon blue)
        post = Marker()
        post.header.frame_id = "map"
        post.ns = "environment_lines"
        post.id = 20002
        post.type = Marker.LINE_STRIP
        post.action = Marker.ADD
        post.scale.x = 0.4
        post.color.r = 0.0; post.color.g = 0.8; post.color.b = 1.0; post.color.a = 1.0
        pp1 = Point(x=-45.0, y=2.5, z=0.0); pp2 = Point(x=-35.0, y=2.5, z=0.0)
        pp3 = Point(x=-35.0, y=17.5, z=0.0); pp4 = Point(x=-45.0, y=17.5, z=0.0)
        post.points = [pp1, pp2, pp3, pp4, pp1]
        self.marker_array.markers.append(post)

        # HOUSE (Neon blue)
        house = Marker()
        house.header.frame_id = "map"
        house.ns = "environment_lines"
        house.id = 20003
        house.type = Marker.LINE_STRIP
        house.action = Marker.ADD
        house.scale.x = 0.4
        house.color.r = 0.0; house.color.g = 0.8; house.color.b = 1.0; house.color.a = 1.0
        hp1 = Point(x=16.0, y=31.0, z=0.0); hp2 = Point(x=24.0, y=31.0, z=0.0)
        hp3 = Point(x=24.0, y=39.0, z=0.0); hp4 = Point(x=16.0, y=39.0, z=0.0)
        house.points = [hp1, hp2, hp3, hp4, hp1]
        self.marker_array.markers.append(house)

    def drone_callback(self, msg):
        # ONLY paint the main drone (the yellow one with camera).
        name_drone = next((n for n in msg.name if "iris" in n.lower() or "depth" in n.lower()), None)
        if not name_drone: return
        
        idx = msg.name.index(name_drone)
        drone_marker = Marker()
        drone_marker.header.frame_id = "map"
        drone_marker.header.stamp = self.get_clock().now().to_msg()
        drone_marker.ns = "main_drone"
        drone_marker.id = 9999
        drone_marker.type = Marker.SPHERE
        drone_marker.action = Marker.ADD
        drone_marker.pose.position.x = msg.pose[idx].position.x
        drone_marker.pose.position.y = msg.pose[idx].position.y
        drone_marker.pose.position.z = msg.pose[idx].position.z 
        drone_marker.scale.x = 0.8; drone_marker.scale.y = 0.8; drone_marker.scale.z = 0.8
        drone_marker.color.r = 1.0; drone_marker.color.g = 1.0; drone_marker.color.b = 0.0; drone_marker.color.a = 1.0
        
        temp_array = MarkerArray()
        temp_array.markers = self.marker_array.markers + [drone_marker]
        self.marker_pub.publish(temp_array)

    def victim_callback(self, msg):
        try:
            data = json.loads(msg.data)
            vid = data.get("id", "Unknown")
            if vid in self.drawn_victims: return
                
            vx = float(data.get('x', 0.0)); vy = float(data.get('y', 0.0))

            vic_marker = Marker()
            vic_marker.header.frame_id = "map"
            vic_marker.ns = "victims"
            vic_marker.id = self.id_counter
            vic_marker.type = Marker.CYLINDER
            vic_marker.action = Marker.ADD
            vic_marker.pose.position.x = vx; vic_marker.pose.position.y = vy; vic_marker.pose.position.z = 0.2
            vic_marker.scale.x = 0.8; vic_marker.scale.y = 0.8; vic_marker.scale.z = 0.8
            vic_marker.color.r = 1.0; vic_marker.color.g = 0.0; vic_marker.color.b = 0.0; vic_marker.color.a = 1.0
            self.marker_array.markers.append(vic_marker)

            line_marker = Marker()
            line_marker.header.frame_id = "map"
            line_marker.ns = "routes"
            line_marker.id = self.id_counter + 1000
            line_marker.type = Marker.LINE_STRIP
            line_marker.action = Marker.ADD
            line_marker.scale.x = 0.1
            line_marker.color.r = 0.0; line_marker.color.g = 1.0; line_marker.color.b = 0.0; line_marker.color.a = 0.8
            line_marker.points = [Point(x=0.0, y=0.0, z=0.2), Point(x=vx, y=vy, z=0.2)]
            self.marker_array.markers.append(line_marker)

            self.drawn_victims.add(vid)
            self.id_counter += 1
        except Exception as e:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = MapVisualizer()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
