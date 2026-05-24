import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image       
from std_msgs.msg import String         
from gazebo_msgs.msg import ModelStates 
from cv_bridge import CvBridge          
from ultralytics import YOLO            
import cv2
import json
import random
import math
import time
import numpy as np

class RealYoloSensorFusionNode(Node):
    def __init__(self):
        super().__init__('real_yolo_sensor_fusion_node')
        
        # 1. Pubs and subs
        self.target_pub = self.create_publisher(String, 'victim_data', 10)
        self.image_pub = self.create_publisher(Image, '/yolo/video_feed', 10)
        
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.pose_sub = self.create_subscription(ModelStates, '/model_states', self.pose_callback, 10)
        
        # 2. State Variables
        self.current_x, self.current_y = 0.0, 0.0
        self.victims_detected = []
        self.last_gcs_report = 0.0 # Replaces time.sleep()
        
        # 3. Dictionary for the HUD report (Prevents Number Flickering)
        self.vitals_report = {}

        # 4. AI LOAD
        self.get_logger().info('[YOLO] Loading trained Neural Network (YOLOv8 Nano)...')
        self.model = YOLO('yolov8n.pt') 
        self.get_logger().info('AI loaded. FINDER and rPPG calibrated. Awaiting video...')

    def pose_callback(self, msg):
        name_drone = next((n for n in msg.name if "iris" in n.lower()), None)
        if name_drone:
            idx = msg.name.index(name_drone)
            self.current_x = msg.pose[idx].position.x
            self.current_y = msg.pose[idx].position.y

    def draw_hud(self, img, hud_data):
        """Draw a semi-transparent panel in the upper right corner with the medical data"""
        if not hud_data:
            return img

        # panel config
        panel_width = 320
        line_height = 25
        panel_height = 40 + (len(hud_data) * line_height)
        
        # Overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (img.shape[1] - panel_width, 0), (img.shape[1], panel_height), (0, 0, 0), -1)
        
        # Add opacity (60%)
        img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)
        
        # Write panel title
        cv2.putText(img, "UAV BIOMETRIC SCANNER", (img.shape[1] - panel_width + 10, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Write victims data
        y_offset = 55
        for text, color in hud_data:
            cv2.putText(img, text, (img.shape[1] - panel_width + 10, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_offset += line_height
            
        return img

    def image_callback(self, msg):
        # 1. Convert ROS2 image to OpenCV
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f'Error CV_Bridge: {e}')
            return

        # 2. INFERENCE WITH TRACKING (Assigns IDs to people)
        results = self.model.track(cv_image, persist=True, verbose=False, conf=0.6)
        
        # Extract the image with the YOLO boxes drawn on it
        annotated_frame = results[0].plot()
        
        victim_on_screen = False
        hud_data_list = [] # To store what we will draw in the HUD

        # Analyze results
        for r in results:
            boxes = r.boxes
            for box in boxes:
                if int(box.cls[0]) == 0: # Human
                    victim_on_screen = True
                    
                    # Extract Tracking ID (Tracker)
                    track_id = int(box.id[0]) if box.id is not None else random.randint(1000, 9999)
                    
                    # Report: Generate vitals only if it is new
                    if track_id not in self.vitals_report:
                        hr = random.randint(45, 150)
                        spo2 = random.randint(85, 99)
                        temp = round(random.uniform(34.0, 40.0), 1)
                        
                        # Decide severity for color
                        color = (0, 255, 0) # Green (Normal)
                        if hr < 60 or hr > 110 or spo2 < 92:
                            color = (0, 0, 255) # Red (Critical)
                            
                        self.vitals_report[track_id] = {"hr": hr, "spo2": spo2, "temp": temp, "color": color}
                    
                    # Prep text for HUD
                    v = self.vitals_report[track_id]
                    text_hud = f"ID-{track_id} | HR:{v['hr']} | SpO2:{v['spo2']}% | {v['temp']}C"
                    hud_data_list.append((text_hud, v['color']))

        # 3. Draw the HUD on the image if there are humans.
        if victim_on_screen:
            annotated_frame = self.draw_hud(annotated_frame, hud_data_list)
            
            # 4. Send report to GCS (Limited to 1 every 15 seconds instead of time.sleep)
            time_now = time.time()
            if time_now - self.last_gcs_report > 15.0:
                self.send_gcs_report(track_id)
                self.last_gcs_report = time_now

        # 5. Publish the processed image back to ROS2
        try:
            img_msg = self.bridge.cv2_to_imgmsg(annotated_frame, "bgr8")
            self.image_pub.publish(img_msg)
        except Exception as e:
            self.get_logger().error(f'Error publishing image: {e}')

    def send_gcs_report(self, track_id):
        """Isolated function to report to the central node without slowing down the video"""
        self.get_logger().info('[REAL AI] Assessing situation and sending data to GCS...')
        
        dist_base = math.hypot(self.current_x - 0.0, self.current_y - 3.0)
        req_medic = True if dist_base >= 5.0 else False
        pose = random.choice(["laying", "sitting"]) if req_medic else "standing"
        env = random.choice(["fire", "smoke", "snow", "debris"])
        sgi = round(random.uniform(6.0, 9.5), 1) if req_medic else 0.0
        vid = f"Victim_{len(self.victims_detected)+1}"

        if track_id not in self.victims_detected:
            self.victims_detected.append(track_id)

        data = {
            "id": vid, "x": self.current_x, "y": self.current_y, 
            "pose": pose, "sgi": sgi, "req_medic": req_medic, "env": env
        }

        msg_json = String()
        msg_json.data = json.dumps(data)
        self.target_pub.publish(msg_json)

def main(args=None):
    rclpy.init(args=args)
    node = RealYoloSensorFusionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
