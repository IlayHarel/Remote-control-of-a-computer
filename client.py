import socket
from pynput import mouse
from pynput import keyboard
from PIL import ImageGrab
import datetime

def main():
    """
    Connects to the server and listens for remote commands.
    Handles mouse and keyboard actions, and takes screenshots when requested.
    """
    s = socket.socket()
    s.connect(("127.0.0.1", 8080))
    print("Connected to server")

    # Create mouse and keyboard controllers

    mouse_ctrl = mouse.Controller()
    key_ctrl = keyboard.Controller()

    # button_map - maps button names from the server to real mouse buttons
    """
    Used to translate button names like "left" or "right" to actual mouse buttons.
    """
    button_map = {
        "left": mouse.Button.left,
        "right": mouse.Button.right,
        "middle": mouse.Button.middle,
    }
    # special_keys - maps special key names to real keyboard keys
    """
    Helps identify and press/release special keys like Enter, Ctrl, or Arrow keys.
    """
    special_keys = {
        "Key.enter": keyboard.Key.enter,
        "Key.shift": keyboard.Key.shift,
        "Key.ctrl": keyboard.Key.ctrl,
        "Key.alt": keyboard.Key.alt,
        "Key.space": keyboard.Key.space,
        "Key.backspace": keyboard.Key.backspace,
        "Key.tab": keyboard.Key.tab,
        "Key.esc": keyboard.Key.esc,
        "Key.up": keyboard.Key.up,
        "Key.down": keyboard.Key.down,
        "Key.left": keyboard.Key.left,
        "Key.right": keyboard.Key.right,
    }

    f = s.makefile()
    count = 0
    max_events = 4

    # Main loop: listen to messages from the server
    # and do what the server tells us to do (screenshot, mouse, keyboard, etc.)
    for line in f:


        line = line.strip()
        if not line:
            continue
        print(line)



        parts = line.split(",")

        if len(parts) >= 2 and parts[1] == "SCREENSHOT":
            print("Taking screenshot...")

            screenshot = ImageGrab.grab()
            filename = f"client_screenshot_{datetime.datetime.now().strftime('%H-%M-%S')}.png"
            screenshot.save(filename)

            import os
            with open(filename, "rb") as f_img:
                img_data = f_img.read()
                img_size = len(img_data)
                f_img.close()
                print(f"Sending screenshot of size: {img_size} bytes")

                # שליחת גודל התמונה קודם
                s.send(f"IMG,{img_size}\n".encode("utf-8"))

                # שליחת תוכן התמונה
                s.sendall(img_data)
                os.remove(filename)
            print("Screenshot sent.")

            continue

        if len(parts) >= 4 and parts[1].startswith("MOUSE_"):
            event = parts[1]

            if event == "MOUSE_CLICK":
                btn_name = parts[2]
                state = parts[3]
                btn = button_map.get(btn_name)
                if not btn:
                    continue
                if state == "1":
                    mouse_ctrl.press(btn)
                elif state == "0":
                    mouse_ctrl.release(btn)


            elif event == "MOUSE_MOVE":
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    mouse_ctrl.position = (x, y)
                except ValueError:
                    pass
            elif event == "MOUSE_SCROLL":
                try:
                    dx = int(parts[2])
                    dy = int(parts[3])
                    mouse_ctrl.scroll(dx, dy)
                except ValueError:
                    pass
        if len(parts) >= 3 and parts[1].startswith("KEY_"):
            event = parts[1]  # KEY_PRESS או KEY_RELEASE
            key_str = parts[2]
            if key_str == "Key.f12":
                continue
            if key_str in special_keys:
                key_obj = special_keys[key_str]
            else:
                key_obj = key_str
            if event == "KEY_PRESS":
                key_ctrl.press(key_obj)
                print(f"Pressed: {key_obj}")
            elif event == "KEY_RELEASE":
                key_ctrl.release(key_obj)
                print(f"Released: {key_obj}")



        count += 1
        if count >= max_events:
            break

    s.close()
    print("Connection closed")

if __name__ == "__main__":
    main()
