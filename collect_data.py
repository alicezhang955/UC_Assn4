import time
import csv
import os
import serial
import matplotlib.pyplot as plt
from collections import deque

# config
port = "/dev/tty.usbmodem487F30FE67E91"  # replace with your port
baud_rate = 115200
output_dir = "training_data"
os.makedirs(output_dir, exist_ok=True)

COLUMNS = ["gyro_x", "gyro_y", "gyro_z", "acc_x", "acc_y", "acc_z", "mag_x", "mag_y", "mag_z"]
refresh_rate = 1 / 10
max_points = 35000
# second smoothing pass matching real_time_vis.py (alpha = weight on new value)
alpha_vis = 0.3

def main():
    shape = input("Enter shape label (e.g. circle, cross, rainbow, triangle): ").strip().lower()
    session = input("Session number (e.g. 1): ").strip()
    filename = os.path.join(output_dir, f"{shape}_{session}.csv")

    feather = serial.Serial(port, baud_rate, timeout=0.1)
    time.sleep(1.0)
    feather.reset_input_buffer()

    print(f"\nSaving to {filename}")
    print("Press the button on the feather to start, press again to stop.")
    print("Ctrl+C to quit early.\n")

    # plot setup
    plt.ion()
    fig, ax = plt.subplots()
    plt.show(block=False)
    (line,) = ax.plot([], [], linewidth=2, color="black")
    (cursor,) = ax.plot([], [], "ro", markersize=8)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Data Collection - Live Drawing")

    rows = []
    x_coords = deque(maxlen=max_points)
    y_coords = deque(maxlen=max_points)
    converted_x = 0.0
    converted_y = 0.0
    is_recording = False
    next_plot = time.time()

    try:
        while True:
            raw_line = feather.readline()
            if raw_line:
                decoded = raw_line.decode("utf-8", errors="ignore").strip()
                if not decoded:
                    pass
                elif decoded == "Start":
                    print("Recording started...")
                    rows = []
                    x_coords.clear()
                    y_coords.clear()
                    converted_x = 0.0
                    converted_y = 0.0
                    is_recording = True
                elif decoded == "Stop":
                    print(f"Recording stopped. {len(rows)} samples captured.")
                    is_recording = False
                elif is_recording:
                    parts = decoded.split(",")
                    if len(parts) == 11:
                        try:
                            values = [float(p) for p in parts]
                            rows.append(values[:9])
                            # second smoothing pass matching real_time_vis.py
                            x = -values[9]
                            y = -values[10]
                            converted_x = alpha_vis * x + (1 - alpha_vis) * converted_x
                            converted_y = alpha_vis * y + (1 - alpha_vis) * converted_y
                            x_coords.append(converted_x)
                            y_coords.append(converted_y)
                        except ValueError:
                            pass

            if time.time() >= next_plot:
                next_plot += refresh_rate
                if len(x_coords) > 1:
                    line.set_data(x_coords, y_coords)
                    cursor.set_data([x_coords[-1]], [y_coords[-1]])
                    ax.relim()
                    ax.autoscale_view()
                fig.canvas.draw()
                fig.canvas.flush_events()

            if not is_recording and rows:
                break

    except KeyboardInterrupt:
        print("\nInterrupted early.")

    finally:
        feather.close()
        plt.ioff()

    if rows:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)
            writer.writerows(rows)
        print(f"Saved {len(rows)} samples to {filename}")
        plot_file = os.path.join(output_dir, f"{shape}_{session}.png")
        ax.axis("off")
        fig.savefig(plot_file, dpi=150, bbox_inches="tight", pad_inches=0)
        print(f"Plot saved to {plot_file}")
    else:
        print("No data collected, file not saved.")

    plt.show()

if __name__ == "__main__":
    main()
