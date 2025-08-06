from pynput import mouse, keyboard
import socket
import datetime
from threading import Thread

client_connection = None;


def now_ts():
    """
    Returns the current timestamp in a readable format.
    Used for tagging each event with the time it happened.
    """
    return datetime.datetime.now().isoformat(timespec='milliseconds')


def server():
    """
    Starts a TCP server and waits for a connection from a client.
    When connected, sends a "hello" message and stores the connection for later use.
    """
    global client_connection
    server = socket.socket()
    server.bind(("0.0.0.0", 8080))
    server.listen(1)
    print("Waiting for connection...")
    client_connection, addr = server.accept()
    print("Connected by:", addr)

    try:
        client_connection.send("hello\n".encode("utf-8"))
        print("Sent 'hello'")
    except Exception:
        print("Failed to send initial hello")


def receive_loop():
    """
    Listens for incoming image data from the client and saves the image as a file.
    """
    global client_connection

    while True:
        try:
            header = client_connection.recv(1024).decode("utf-8")
            if not header:
                print("Connection closed by client.")
                break

            if header.startswith("IMG,"):
                img_size = int(header.strip().split(",")[1])
                print(f"Receiving image of size: {img_size} bytes...")

                img_data = b""
                while len(img_data) < img_size:
                    chunk = client_connection.recv(min(4096, img_size - len(img_data)))
                    if not chunk:
                        break
                    img_data += chunk

                # Create a file name based on date and time
                filename = f"received_screenshot_{datetime.datetime.now().strftime('%H-%M-%S')}.png"

                # Saving the image to a file
                with open(filename, "wb") as f_out:
                    f_out.write(img_data)

                print(f"Image received and saved as '{filename}'")

        except Exception as e:
            print("Error in receive_loop:", e)
            break


def on_click(x, y, button, pressed):
    """
    Sends a message to the client when a mouse button is pressed or released.
    Includes which button and whether it was pressed or released.
    """
    if client_connection is None:
        return
    state = 1 if pressed else 0

    btn = button.name

    msg = f"{now_ts()},MOUSE_CLICK,{btn},{state}\n"
    print("Sending:", msg.strip())
    try:
        client_connection.sendall(msg.encode("utf-8"))
    except Exception:
        print("Failed to send; client maybe disconnected")


def on_move(x, y):
    """
    Sends a message to the client when the mouse is moved.
    Includes the new X, Y coordinates.
    """
    if client_connection is None:
        return
    msg = f"{now_ts()},MOUSE_MOVE,{x},{y}\n"

    print("Sending:", msg.strip())
    try:
        client_connection.sendall(msg.encode("utf-8"))
    except Exception:
        print("Failed to send; client maybe disconnected")


def on_scroll(x, y, dx, dy):
    """
    Sends a message to the client when the mouse wheel is scrolled.
    Includes how much the user scrolled (dx, dy).
    """
    if client_connection is None:
        return
    msg = f"{now_ts()},MOUSE_SCROLL,{dx},{dy}\n"
    print("Sending:", msg.strip())
    try:
        client_connection.sendall(msg.encode("utf-8"))
    except Exception:
        print("Failed to send; client maybe disconnected")


def on_press(key):
    """
    Sends a message when a key is pressed.
    If F12 is pressed, it tells the client to take a screenshot.
    """

    if client_connection is None:
        return

    if key == keyboard.Key.f12:
        print("\n" + "=" * 40)
        print("F12 - Taking screenshot on remote computer")
        print("=" * 40)

        msg = f"{now_ts()},SCREENSHOT\n"
        client_connection.sendall(msg.encode("utf-8"))

        print("Screenshot command sent!")
        print("Check the CLIENT console for the file location")
        print("=" * 40 + "\n")

        return

    try:
        key_name = key.char
    except AttributeError:
        key_name = str(key)
    msg = f"{now_ts()},KEY_PRESS,{key_name}\n"
    print("Sending:", msg.strip())
    try:
        client_connection.sendall(msg.encode("utf-8"))
    except Exception:
        print("Failed to send; client maybe disconnected")


def on_release(key):
    """
    Sends a message when a key is released.
    Includes which key was released.
    """
    if client_connection is None:
        return
    try:
        key_name = key.char
    except AttributeError:
        key_name = str(key)
    msg = f"{now_ts()},KEY_RELEASE,{key_name}\n"
    print("Sending:", msg.strip())
    try:
        client_connection.sendall(msg.encode("utf-8"))
    except Exception:
        print("Failed to send; client maybe disconnected")


if __name__ == "__main__":
    """
    Starts the server and begins listening for mouse and keyboard events.
    Each listener runs in a separate thread.
    To request a screenshot from the client, press F12
    """
    server()
    mouse_thread = Thread(target=lambda: mouse.Listener(on_click=on_click, on_move=on_move, on_scroll=on_scroll).run())
    kb_thread = Thread(target=lambda: keyboard.Listener(on_press=on_press, on_release=on_release).run())
    recv_thread = Thread(target=receive_loop)
    recv_thread.start()
    mouse_thread.start()
    kb_thread.start()
    mouse_thread.join()
    kb_thread.join()
