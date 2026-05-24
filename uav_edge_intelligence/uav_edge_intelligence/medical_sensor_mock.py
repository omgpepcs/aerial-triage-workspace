import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String
from gazebo_msgs.msg import ModelStates
from sensor_msgs.msg import Image       
from cv_bridge import CvBridge          
from ultralytics import YOLO            
import cv2
import json
import math
import time
import random

class VisualSensorFusionNode(Node):
    def __init__(self):
        super().__init__('visual_sensor_fusion_node')
        
        qos_video = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST, depth=1)
        self.target_pub = self.create_publisher(String, 'victim_data', 10)
        self.image_pub = self.create_publisher(Image, '/yolo/video_feed', qos_video)
        self.bridge = CvBridge()
        
        self.create_subscription(Image, '/camera/image_raw', self.image_callback, qos_video)
        self.pose_sub = self.create_subscription(ModelStates, '/model_states', self.radar_callback, 10)
        
        print("[AI EDGE] Starting up. Checking connection with the Radar...", flush=True)
        # load pose model
        self.model = YOLO('yolov8n-pose.pt') 
        
        self.current_x = 0.0
        self.current_y = 0.0
        self.pause_until = 0.0
        self.victims_detected = []
        self.victims_ids = {}
        self.frame_counter = 0
        
        # Dictionary for HUD report
        self.vitals_report = {}
        
        # Self-Diagnostic System
        self.radar_alive = False
        self.create_timer(5.0, self.check_diagnostic)

        with open("/mnt/hgfs/shared/victims.json", "w") as f:
            json.dump({}, f)

    def check_diagnostic(self):
        if not self.radar_alive:
            print("[CRITICAL ALERT] The Radar is OFF! No Gazebo data.", flush=True)

    def draw_hud(self, img, hud_data):
        if not hud_data:
            return img

        panel_width = 320
        line_height = 25
        panel_height = 40 + (len(hud_data) * line_height)
        
        overlay = img.copy()
        cv2.rectangle(overlay, (img.shape[1] - panel_width, 0), (img.shape[1], panel_height), (0, 0, 0), -1)
        img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)
        
        cv2.putText(img, "UAV BIOMETRIC SCANNER", (img.shape[1] - panel_width + 10, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        y_offset = 55
        for text, color in hud_data:
            cv2.putText(img, text, (img.shape[1] - panel_width + 10, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_offset += line_height
            
        return img

    def image_callback(self, msg):
        self.frame_counter += 1
        # skip frames to reduce CPU load (smooth FPS)
        if self.frame_counter % 2 == 0: return 

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            results = self.model.predict(cv_image, verbose=False, conf=0.25, imgsz=480)
            
            hud_data_list = []
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    if int(box.cls[0]) == 0: # Human
                        # Calculate the center of the box
                        coords = box.xyxy[0].tolist()
                        cx = (coords[0] + coords[2]) / 2
                        cy = (coords[1] + coords[3]) / 2

                        found = False
                        for track_id, v in self.vitals_report.items():
                            # If the center has moved less than 150 pixels, it's the same person
                            if abs(v['cx'] - cx) < 150 and abs(v['cy'] - cy) < 150:
                                v['cx'] = cx 
                                v['cy'] = cy
                                text_hud = f"ID-{track_id} | HR:{v['hr']} | SpO2:{v['spo2']}% | {v['temp']}C"
                                hud_data_list.append((text_hud, v['color']))
                                found = True
                                break
                                
                        if not found:
                            # It's a new person, generate vital signs and an ID
                            new_id = random.randint(1000, 9999)
                            hr = random.randint(45, 150)
                            spo2 = random.randint(85, 99)
                            temp = round(random.uniform(34.0, 40.0), 1)
                            color = (0, 255, 0)
                            if hr < 60 or hr > 110 or spo2 < 92:
                                color = (0, 0, 255)
                                
                            self.vitals_report[new_id] = {"cx": cx, "cy": cy, "hr": hr, "spo2": spo2, "temp": temp, "color": color}
                            vid = f"Victim_{len(self.victims_ids)+1}"
                            self.victims_ids[new_id] = {"id": vid}
                            text_hud = f"ID-{new_id} | HR:{hr} | SpO2:{spo2}% | {temp}C"
                            hud_data_list.append((text_hud, color))

            # Draw the skeleton, boxes and panel
            if len(results[0].boxes) > 0:
                annotated_frame = results[0].plot()
                annotated_frame = self.draw_hud(annotated_frame, hud_data_list)
            else:
                annotated_frame = cv_image.copy()
                
            status = "SEARCHING..." if time.time() > self.pause_until else "ANALYZING POSE"
            color_txt = (0, 255, 0) if time.time() > self.pause_until else (0, 0, 255)
            cv2.putText(annotated_frame, f"EDGE AI | {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_txt, 2)
            
            # Publish video
            self.image_pub.publish(self.bridge.cv2_to_imgmsg(annotated_frame, "bgr8"))
        except Exception as e: 
            print(f"Error processing image: {e}", flush=True)

    def radar_callback(self, msg):
        self.radar_alive = True
        if time.time() < self.pause_until: return

        name_drone = next((n for n in msg.name if "iris" in n.lower() or "depth" in n.lower()), None)
        if not name_drone: return
        
        idx_drone = msg.name.index(name_drone)
        self.current_x = msg.pose[idx_drone].position.x
        self.current_y = msg.pose[idx_drone].position.y

        for i, name_model in enumerate(msg.name):
            if "person" in name_model.lower():
                if name_model in self.victims_detected: continue

                vx = msg.pose[i].position.x
                vy = msg.pose[i].position.y
                dist = math.hypot(self.current_x - vx, self.current_y - vy)

                if dist < 5.5:
                    self.victims_detected.append(name_model)
                    print(f'\n[TACTIC RADAR] Found!: {name_model}! Rotating...', flush=True)
                    
                    offset_x = vx - self.current_x
                    offset_y = vy - self.current_y
                    
                    is_wounded = "wounded" in name_model.lower()
                    data = {
                        "id": name_model.upper(), 
                        "offset_x": offset_x,
                        "offset_y": offset_y,
                        "x": vx,
                        "y": vy,
                        "pose": "Analyzing skeleton...",
                        "sgi": 8.5 if is_wounded else 0.0, 
                        "req_medic": is_wounded
                    }
                    data_host = {
                        "victims": {},
                        "drones_analyzing": True
                    }
                    for new_id, data in self.victims_ids.items():
                        nose = random.choice([125, 340, 540])
                        if nose < 150:
                            pose = "standing"
                        elif nose > 420:
                            pose = "laying"
                        else:
                            pose = "sitting"
                        env = random.choice(["fire", "smoke", "debris", "nothing"])
                        vid = data["id"]
                        data_host["victims"][vid] = {
                            "pose": pose, "hr": self.vitals_report[new_id]["hr"],
                            "temp": self.vitals_report[new_id]["temp"], "env": env,
                            "coord_x": round(vx, 1), "coord_y": round(vy, 1)
                        }
                    if len(data_host["victims"]) >= 6:
                        data_host["drones_analyzing"] = False
                    
                    with open("/mnt/hgfs/shared/victims.json", "w") as f:
                        json.dump(data_host, f, indent=4)

                    msg_json = String()
                    msg_json.data = json.dumps(data)
                    self.target_pub.publish(msg_json) 
                    
                    self.pause_until = time.time() + 32.0 
                    break

def main(args=None):
    rclpy.init(args=args)
    node = VisualSensorFusionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__': main()
