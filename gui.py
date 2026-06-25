import os
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import signal
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class HuskyListener(Node):
    def __init__(self, gui_ref):
        super().__init__('husky_listener')
        self.gui_ref = gui_ref
        self.subscription = self.create_subscription(
            String, '/husky_status', self.listener_callback, 10
        )

    def listener_callback(self, msg):
        self.gui_ref.root.after(0, self.gui_ref.update_status, msg.data)

class HotspotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotspot GUI")
        self.root.geometry("400x400")
        self.root.resizable(False, False)

        # Top controls
        frm_top = ttk.Frame(root, padding=6)
        frm_top.pack(fill=tk.X)
        ttk.Label(frm_top, text="Number of Hotspots (1–10):").pack(side=tk.LEFT, padx=4)
        self.num_var = tk.IntVar(value=1)
        self.spin_num = ttk.Spinbox(frm_top, from_=1, to=10, textvariable=self.num_var, width=3)
        self.spin_num.pack(side=tk.LEFT, padx=4)
        self.btn_generate = ttk.Button(frm_top, text="Generate", command=self.run_hotspots)
        self.btn_generate.pack(side=tk.LEFT, padx=4)

        # Output window
        self.txt_output = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, height=15, width=50, font=("Courier", 9), state='disabled'
        )
        self.txt_output.pack(padx=6, pady=6, fill=tk.BOTH, expand=True)

        # Bottom buttons
        frm_bottom = ttk.Frame(root, padding=6)
        frm_bottom.pack(fill=tk.X)
        self.btn_start = ttk.Button(frm_bottom, text="Start", command=self.start_sim)
        self.btn_start.pack(side=tk.LEFT, padx=4)
        self.btn_kill = ttk.Button(frm_bottom, text="Close", command=self.kill_sim)
        self.btn_kill.pack(side=tk.LEFT, padx=4)
        self.btn_teleop = ttk.Button(frm_bottom, text="Teleop", command=self.start_teleop)
        self.btn_teleop.pack(side=tk.LEFT, padx=4)

        # Runtime state
        self.proc = None
        self.hotspots = []
        self.husky_pos = (0, 0)
        self.triggered_hotspots = set()

        # Handle window close and ESC key
        self.root.protocol("WM_DELETE_WINDOW", self.kill_sim)
        self.root.bind("<Escape>", lambda event: self.kill_sim())

        # Start ROS listener
        self.ros_thread = threading.Thread(target=self.ros_spin, daemon=True)
        self.ros_thread.start()

    def ros_spin(self):
        try:
            rclpy.init(args=None)
        except Exception:
            pass

        try:
            self.node = HuskyListener(self)
            rclpy.spin(self.node)
        except Exception:
            self.root.after(0, self.append_output, "ROS listener thread exiting.\n")
        finally:
            try:
                if hasattr(self, "node"):
                    self.node.destroy_node()
            except Exception:
                pass
            try:
                if rclpy.ok():
                    rclpy.shutdown()
            except Exception:
                pass

    def run_hotspots(self):
        num = self.num_var.get()
        if not (1 <= num <= 10):
            self.append_output("Please choose between 1 and 10 hotspots.\n")
            return

        script_path = os.path.join(SCRIPT_DIR, "random_hotspots.py")
        if not os.path.isfile(script_path):
            self.append_output(f"Error: random_hotspots.py not found at {script_path}\n")
            return

        def _run():
            self.root.after(0, self.clear_hotspot_messages)

            try:
                completed = subprocess.run(
                    ["python3", script_path],
                    input=f"{num}\n",
                    text=True,
                    capture_output=True,
                    check=True,
                    timeout=15.0
                )

                lines = [line for line in completed.stdout.strip().splitlines() if line]
                for idx, line in enumerate(lines):
                    # Ensure correct Hotspot prefix without duplicates
                    if not line.startswith(f"Hotspot {idx + 1}:"):
                        line = f"Hotspot {idx + 1}: {line}"
                    self.root.after(0, self.append_output, line + "\n")

                if completed.stderr.strip():
                    self.root.after(0, self.append_output, "Script stderr:\n" + completed.stderr.strip() + "\n")

            except subprocess.CalledProcessError as e:
                self.root.after(0, self.append_output, f"Hotspot script failed: {e}\n")
                if e.stdout:
                    self.root.after(0, self.append_output, e.stdout + "\n")
                if e.stderr:
                    self.root.after(0, self.append_output, "Script stderr:\n" + e.stderr + "\n")
            except subprocess.TimeoutExpired:
                self.root.after(0, self.append_output, "Hotspot generation timed out.\n")
            except Exception as e:
                self.root.after(0, self.append_output, f"Error running hotspot script: {e}\n")

        threading.Thread(target=_run, daemon=True).start()

    def clear_hotspot_messages(self):
        try:
            self.txt_output.config(state='normal')
            lines = self.txt_output.get("1.0", tk.END).splitlines()
            remaining = [line for line in lines if line and not line.startswith("Hotspot ")]
            self.txt_output.delete("1.0", tk.END)
            if remaining:
                self.txt_output.insert(tk.END, "\n".join(remaining) + "\n")
            self.txt_output.config(state='disabled')
        except Exception:
            pass

    def start_sim(self):
        self.append_output("Starting simulation (ros2 launch)...\n")
        ros_cmds = """
        cd ~/RS1-saket &&
        colcon build --symlink-install &&
        source install/setup.bash &&
        ros2 launch 41068_ignition_bringup 41068_ignition.launch.py rviz:=true nav2:=true world:=large_demo
        """
        try:
            terminal_cmd = ["gnome-terminal", "--", "bash", "-c", f"{ros_cmds}; exec bash"]
            self.proc = subprocess.Popen(terminal_cmd, preexec_fn=os.setsid)
            self.append_output("Simulation launched in new terminal.\n")
        except FileNotFoundError:
            self.append_output("Error: gnome-terminal or ros2 not found.\n")
        except Exception as e:
            self.append_output(f"Error launching simulation: {e}\n")

    def start_teleop(self):
        self.append_output("Starting teleop (teleop_twist_keyboard)...\n")
        cmd = ["ros2", "run", "teleop_twist_keyboard", "teleop_twist_keyboard"]
        try:
            terminal_cmd = ["gnome-terminal", "--"] + cmd
            subprocess.Popen(terminal_cmd)
            self.append_output("Teleop started in new terminal.\n")
        except FileNotFoundError:
            self.append_output("Error: gnome-terminal or ros2 not found.\n")
        except Exception as e:
            self.append_output(f"Error starting teleop: {e}\n")

    def kill_sim(self):
        self.append_output("\nShutting down simulation and GUI...\n")
        if self.proc:
            try:
                if self.proc.poll() is None:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except Exception:
                pass
            self.proc = None
        try:
            if hasattr(self, "node"):
                self.node.destroy_node()
        except Exception:
            pass
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass
        try:
            subprocess.run(["pkill", "-f", "gz"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-f", "ros2"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            try:
                self.root.quit()
            except Exception:
                pass

    def append_output(self, text):
        try:
            self.txt_output.config(state='normal')
            self.txt_output.insert(tk.END, text)
            self.txt_output.see(tk.END)
            self.txt_output.config(state='disabled')
        except Exception:
            pass

    def update_status(self, msg):
        self.append_output(f"{msg}\n")

def main():
    root = tk.Tk()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    app = HotspotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
