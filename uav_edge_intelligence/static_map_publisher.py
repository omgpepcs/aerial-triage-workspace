import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, MapMetaData
from geometry_msgs.msg import Pose
import numpy as np

class StaticMapPublisher(Node):
    def __init__(self):
        super().__init__('static_map_publisher')
        self.publisher = self.create_publisher(OccupancyGrid, '/map', 10)
        
        # map config (1 pixel = 0.5 m)
        self.res = 0.5
        self.width = 300  # 150 m / 0.5
        self.height = 300 # 150 m / 0.5
        
        self.timer = self.create_timer(2.0, self.publish_map)
        self.get_logger().info('2D Map Publisher Started...')

    def publish_map(self):
        msg = OccupancyGrid()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        
        # map info
        msg.info.resolution = self.res
        msg.info.width = self.width
        msg.info.height = self.height
        msg.info.origin.position.x = -75.0
        msg.info.origin.position.y = -75.0
        
        # Create grid (0 = free, 100 = occupied, -1 = unknown)
        # initialize everything as "free" (grass)
        data = np.zeros(self.width * self.height, dtype=np.int8)
        
        # --- DRAW ROAD (light grey on map) ---
        # Road on Gazebo: -10, 0 with size 60x10
        for x in range(int(20/self.res), int(80/self.res)):
            for y in range(int(70/self.res), int(80/self.res)):
                data[y * self.width + x] = 10 # Low value to indicate special ground
        
        # --- DRAW BUILDINGS (Black walls) ---
        # Building 1 (Post Office): -40, 10
        self.draw_box(data, -40, 10, 10, 15, 100)
        
        # House 1: 20, 35
        self.draw_box(data, 20, 35, 8, 8, 100)
        
        msg.data = data.tolist()
        self.publisher.publish(msg)

    def draw_box(self, data, cx, cy, sx, sy, val):
        """Draw an obstacle on the map based on Gazebo coordinates"""
        x_start = int((cx - sx/2 + 75) / self.res)
        x_end = int((cx + sx/2 + 75) / self.res)
        y_start = int((cy - sy/2 + 75) / self.res)
        y_end = int((cy + sy/2 + 75) / self.res)
        
        for i in range(x_start, x_end):
            for j in range(y_start, y_end):
                if 0 <= i < self.width and 0 <= j < self.height:
                    data[j * self.width + i] = val

def main(args=None):
    rclpy.init(args=args)
    node = StaticMapPublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
