import xml.etree.ElementTree as ET

xml_string = """<?xml version="1.0" encoding="UTF-8"?>
<launch>
  <!-- Essential parameters -->
  <arg name="map_path" description="point cloud and lanelet2 map directory path" />
  <arg name="vehicle_model" default="sample_vehicle" description="vehicle model name" />
  <arg name="sensor_model" default="logiee_s-tc_sensor" description="sensor model name" />
  <arg name="pointcloud_container_name" default="pointcloud_container" />
  <arg name="data_path" default="$(env HOME)/autoware_data"
    description="packages data and artifacts directory path" />

  <!-- launch module preset -->
  <arg name="planning_module_preset" default="default" description="planning module preset" />
  <!-- Optional parameters -->
  <!-- Modules to be launched -->
  <arg name="launch_vehicle" default="true" description="launch vehicle" />
  <arg name="launch_system" default="true" description="launch system" />
  <arg name="launch_map" default="true" description="launch map" />
  <arg name="launch_sensing" default="true" description="launch sensing" />
  <arg name="launch_sensing_driver" default="true" description="launch sensing driver" />
  <arg name="launch_localization" default="true" description="launch localization" />
  <arg name="launch_perception" default="true" description="launch perception" />
  <arg name="launch_planning" default="true" description="launch planning" />
  <arg name="launch_control" default="true" description="launch control" />
  <!-- Global parameters -->
  <arg name="use_sim_time" default="false" description="use_sim_time" />
  <!-- Vehicle -->
  <arg name="vehicle_id" default="$(env VEHICLE_ID default)" description="vehicle specific ID" />
  <arg name="launch_vehicle_interface" default="true" description="launch vehicle interface" />
  <!-- Control -->
  <arg name="check_external_emergency_heartbeat" default="false" />
  <!-- Map -->
  <arg name="lanelet2_map_file" default="lanelet2_map.osm" description="lanelet2 map file name" />
  <arg name="pointcloud_map_file" default="pointcloud_map.pcd"
    description="pointcloud map file name" />
  <!-- System -->
  <arg name="system_run_mode" default="online" description="run mode in system" />
  <arg name="launch_system_monitor" default="true" description="launch system monitor" />
  <arg name="launch_dummy_diag_publisher" default="false" description="launch dummy diag publisher" />
  <arg name="system_error_monitor_param_path"
    default="$(find-pkg-share autoware_launch)/config/system/system_error_monitor/system_error_monitor.param.yaml" />
  <!-- Tools -->
  <arg name="rviz" default="true" description="launch rviz" />
  <arg name="rviz_config" default="$(find-pkg-share autoware_launch)/rviz/autoware.rviz"
    description="rviz config" />
  <arg name="rviz_respawn" default="true" />
  <!-- Perception -->
  <arg name="perception_mode" default="lidar"
    description="select perception mode. camera_lidar_radar_fusion, camera_lidar_fusion, lidar_radar_fusion, lidar, radar" />
  <arg name="traffic_light_recognition/enable_fine_detection" default="true"
    description="enable traffic light fine detection" />
  <!-- Auto mode setting-->
  <arg name="enable_all_modules_auto_mode" default="false"
    description="enable all module's auto mode" />
  <arg name="is_simulation" default="false"
    description="Autoware's behavior will change depending on whether this is a simulation or not." />

  <!-- Global parameters -->
  <group scoped="false">
    <include file="$(find-pkg-share global_parameter_loader)/launch/global_params.launch.py">
      <arg name="use_sim_time" value="$(var use_sim_time)" />
      <arg name="vehicle_model" value="$(var vehicle_model)" />
    </include>
  </group>

  <!-- Pointcloud container -->
  <include file="$(find-pkg-share autoware_launch)/launch/pointcloud_container.launch.py">
    <arg name="use_multithread" value="true" />
    <arg name="container_name" value="$(var pointcloud_container_name)" />
  </include>

  <!-- Vehicle -->
  <group if="$(var launch_vehicle)">
    <include file="$(find-pkg-share tier4_vehicle_launch)/launch/vehicle.launch.xml">
      <arg name="vehicle_model" value="$(var vehicle_model)" />
      <arg name="sensor_model" value="$(var sensor_model)" />
      <arg name="vehicle_id" value="$(var vehicle_id)" />
      <arg name="launch_vehicle_interface" value="$(var launch_vehicle_interface)" />
      <arg name="config_dir"
        value="$(find-pkg-share individual_paramsa)/config/$(var vehicle_id)/$(var sensor_model)" />
      <arg name="raw_vehicle_cmd_converter_param_path"
        value="$(find-pkg-share autoware_launch)/config/vehicle/raw_vehicle_cmd_converter/raw_vehicle_cmd_converter.param.yaml" />
    </include>
  </group>

  <!-- System -->
  <group if="$(var launch_system)">
    <include
      file="$(find-pkg-share autoware_launch)/launch/components/tier4_map_component.launch.xml" />
  </group>

  <!-- Map -->
  <group if="$(var launch_map)">
    <include
      file="$(find-pkg-share autoware_launch)/launch/components/tier4_map_component.launch.xml" />
  </group>

  <!-- Sensing -->
  <group if="$(var launch_sensing)">
    <include
      file="$(find-pkg-share autoware_launch)/launch/components/tier4_sensing_component.launch.xml" />
  </group>

  <!-- Localization -->
  <group if="$(var launch_localization)">
    <include
      file="$(find-pkg-share autoware_launch)/launch/components/tier4_localization_component.launch.xml" />
  </group>

  <!-- Perception -->
  <group if="$(var launch_perception)">
    <include file="$(find-pkg-share autoware_launch)/launch/components/tier4_perception_component.launch.xml">
      <arg name="data_path" value="$(var data_path)"/>
    </include>
  </group>

  <!-- Planning -->
  <group if="$(var launch_planning)">
    <include
      file="$(find-pkg-share autoware_launch)/launch/components/tier4_planning_component.launch.xml">
      <arg name="module_preset" value="$(var planning_module_preset)" />
      <arg name="enable_all_modules_auto_mode" value="$(var enable_all_modules_auto_mode)" />
      <arg name="is_simulation" value="$(var is_simulation)" />
    </include>
  </group>

  <!-- Control -->
  <group if="$(var launch_control)">
    <include file="$(find-pkg-share autoware_launch)/launch/components/tier4_control_component.launch.xml"/>
  </group>

  <!-- API -->
  <group>
    <include
      file="$(find-pkg-share autoware_launch)/launch/components/tier4_autoware_api_component.launch.xml" />
  </group>

  <!-- Tools -->
  <group>
    <node
      pkg="rviz2"
      exec="rviz2"
      name="rviz2"
      output="screen"
      args="-d $(var rviz_config) -s $(find-pkg-share autoware_launch)/rviz/image/autoware.png"
      if="$(var rviz)"
      respawn="$(var rviz_respawn)"
    />
  </group>
</launch>
"""


def find_scope(xml_string: str, line_number: int, column_number: int):
    lines = xml_string.splitlines()
    target_line = lines[line_number - 1]
    target_col = column_number - 1

    # Create a fragment of XML up to the target line and column
    xml_fragment = "\n".join(lines[:line_number])
    xml_fragment = xml_fragment[:target_col]

    # Parse the XML fragment
    try:
        parser = ET.XMLPullParser(["start", "end"])
        parser.feed(xml_fragment)
        parser.close()
        events = list(parser.read_events())
    except ET.ParseError:
        return "Could not parse the XML fragment."

    # Find the scope of the last element before the target column
    scope = []
    for event, elem in events:
        if event == "start":
            scope.append(elem.tag)
        elif event == "end" and scope and scope[-1] == elem.tag:
            scope.pop()

    return " > ".join(scope) if scope else "Root"


# Example usage
line_number = 10  # 指定行番号
column_number = 15  # 指定列番号
scope = find_scope(xml_string, line_number, column_number)
print(f"The scope at line {line_number}, column {column_number} is: {scope}")
