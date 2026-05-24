#!/bin/bash

echo "Launching TFM: Swarm Rescue Mission + 2.5D Tactical Map"
# 1. Complete cleaning of previous processes
killall -9 gzserver gzclient px4 MicroXRCEAgent rviz2 2>/dev/null

# 2. AGENT (Drone-PC Communication)
gnome-terminal --tab --title="1_AGENT" -- bash -c "MicroXRCEAgent udp4 -p 8888; exec bash"
sleep 2

# 3. GAZEBO (World + Drone with camera)
echo "Loading World and Drone..."
gnome-terminal --tab --title="2_GAZEBO" -- bash -c "cd ~/PX4-Autopilot; PX4_SITL_WORLD=/home/alvaro/ros2_ws/src/triage_mission.world make px4_sitl gazebo-classic_iris_depth_camera; exec bash"

# Wait for Gazebo to load properly before launching the AI
sleep 30 

# 4. MAP AND COORDS (Marker and route viewer only)
echo "Setting up tactical visualization..."
gnome-terminal --tab --title="3_MAP_VISUALIZER" -- bash -c "
source /opt/ros/humble/setup.bash;
source ~/ros2_ws/install/setup.bash;
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map base_link & 
python3 ~/ros2_ws/src/uav_edge_intelligence/map_visualizer.py; 
exec bash"

# 5. AI (Mission Nodes and YOLO)
echo "Launching AI Edge..."
gnome-terminal --tab --title="4_MISSION_AI" -- bash -c "cd ~/ros2_ws; source /opt/ros/humble/setup.bash; source install/setup.bash; ros2 launch uav_edge_intelligence swarm_mission.launch.py; exec bash"
sleep 5

# 6. SWARM (Fake Pilot / Props)
echo "Deploying Fleet Manager (Swarm Command)..."
gnome-terminal --tab --title="5_SWARM" -- bash -c "
source /opt/ros/humble/setup.bash;
source ~/ros2_ws/install/setup.bash;
python3 ~/ros2_ws/src/uav_edge_intelligence/dummy_uav_controller.py;
exec bash"

# 7. GRAPHIC VIEWERS (Video + RViz)
echo "Opening Viewers..."
gnome-terminal --tab --title="6_VIEWERS" -- bash -c "
source /opt/ros/humble/setup.bash;
source ~/ros2_ws/install/setup.bash;
ros2 run rqt_image_view rqt_image_view & 
rviz2; 
exec bash"
