import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose
from gazebo_msgs.srv import DeleteEntity
import math

# -------------------------
# Configuration
# -------------------------
HOTSPOT_RADIUS = 0.7
HUSKY_WIDTH = 0.75
HUSKY_LENGTH = 1.0

# -------------------------
# Collision utility
# -------------------------
def rect_circle_collision(rect_center, width, length, circle_center, radius):
    """Check collision between a rectangle (Husky) and a circle (Hotspot)."""
    rx, ry = rect_center
    cx, cy = circle_center
    closest_x = max(rx - width / 2, min(cx, rx + width / 2))
    closest_y = max(ry - length / 2, min(cy, ry + length / 2))
    dist = math.hypot(cx - closest_x, cy - closest_y)
    return dist <= radius


# -------------------------
# ROS2 Node
# -------------------------
class HotspotCooldownNode(Node):
    def __init__(self):
        super().__init__('hotspot_cooldown_node')

        # Declare parameter (default 10 if not set)
        self.declare_parameter('num_hotspots', 10)
        num_hotspots = self.get_parameter('num_hotspots').value

        self.get_logger().info(f"Hotspot Cooldown Node started. Tracking {num_hotspots} hotspots.")

        # Subscribe to Husky pose
        self.husky_pose_sub = self.create_subscription(
            Pose,
            '/model/husky/pose',
            self.husky_pose_callback,
            10
        )

        # Subscribe to all hotspot poses
        self.hotspot_positions = {}
        for i in range(1, num_hotspots + 1):
            topic = f'/hotspot_{i}/pose'
            self.create_subscription(Pose, topic, self.make_hotspot_callback(i), 10)

        # Gazebo delete service client
        self.delete_client = self.create_client(DeleteEntity, '/delete_entity')
        while not self.delete_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn("Waiting for /delete_entity service...")

        self.removed = set()
        self.husky_pos = None

    # -------------------------
    # Dynamic callbacks
    # -------------------------
    def make_hotspot_callback(self, i):
        def callback(msg):
            self.hotspot_positions[f"hotspot_{i}"] = (msg.position.x, msg.position.y)
        return callback

    def husky_pose_callback(self, msg):
        self.husky_pos = (msg.position.x, msg.position.y)
        self.check_collisions()

    # -------------------------
    # Collision and deletion
    # -------------------------
    def check_collisions(self):
        if self.husky_pos is None:
            return

        for name, pos in list(self.hotspot_positions.items()):
            if name in self.removed:
                continue

            if rect_circle_collision(self.husky_pos, HUSKY_WIDTH, HUSKY_LENGTH, pos, HOTSPOT_RADIUS):
                self.get_logger().info(f"Husky collided with {name}! Deleting...")
                self.remove_hotspot(name)

    def remove_hotspot(self, name):
        req = DeleteEntity.Request()
        req.name = name

        future = self.delete_client.call_async(req)
        future.add_done_callback(lambda _: self.handle_delete_response(name))

    def handle_delete_response(self, name):
        self.get_logger().info(f"{name} removed from Gazebo.")
        self.removed.add(name)


# -------------------------
# Main
# -------------------------
def main(args=None):
    rclpy.init(args=args)
    node = HotspotCooldownNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
