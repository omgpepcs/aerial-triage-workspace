import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Route to your 3D world (Make sure the name matches the one you saved)
    world_file_path = os.path.expanduser('~/ros2_ws/src/triage_mission.world')

    # 2. Turn on Drone 1 (The one that looks for victims)
    drone_1_node = Node(
        package='uav_edge_intelligence',
        executable='mock_node',
        name='mock_node'
    )

    # 3. Turn on the base (GCS)
    gcs_node = Node(
        package='uav_edge_intelligence',
        executable='triage_node',
        name='triage_node'
    )

    # 4. Turn on Drone 2 (The one that bids in the auction)
    drone_2_node = Node(
        package='uav_edge_intelligence',
        executable='uav02_node',
        name='uav02_node'
    )
    
    # 5. Turn on the Autonomous Flight Navigator
    nav_node = Node(
        package='uav_edge_intelligence',
        executable='navigator_node',
        name='navigator_node'
    )

    # Put everything in the "blender" and throw it all at once.
    return LaunchDescription([
        drone_1_node,
        gcs_node,
        drone_2_node,
        nav_node
    ])
