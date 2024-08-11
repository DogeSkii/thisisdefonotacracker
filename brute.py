import requests
import itertools
import string
import concurrent.futures
import logging
import time
from threading import Event, Thread
import tkinter as tk
from tkinter import scrolledtext
import queue

url = 'https://codes.thisisnotawebsitedotcom.com/'

headers = {
    'Host': 'codes.thisisnotawebsitedotcom.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': 'https://thisisnotawebsitedotcom.com/',
    'Content-Type': 'multipart/form-data; boundary=---------------------------22325320711689964980729421549',
    'Origin': 'https://thisisnotawebsitedotcom.com',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Priority': 'u=0'
}

logging.basicConfig(filename='successful_codes.log', level=logging.INFO, format='%(asctime)s - %(message)s')

pause_event = Event()
update_queue = queue.Queue()
request_log_interval = 60  # seconds
request_log_timer = time.time()

def generate_strings(starting_string):
    characters = string.ascii_lowercase + string.digits
    length = len(starting_string)
    
    for current_length in range(length, 17):
        for s in itertools.product(characters, repeat=current_length):
            s = ''.join(s)
            if current_length == length and s < starting_string:
                continue
            yield s

def log_full_request(s, body, response):
    with open('full_requests.log', 'a') as f:
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Request URL: {url}\n")
        f.write(f"Request Headers: {headers}\n")
        f.write(f"Request Body:\n{body}\n")
        f.write(f"Response Status Code: {response.status_code}\n")
        f.write(f"Response Headers: {response.headers}\n")
        f.write(f"Response Content:\n{response.text}\n")
        f.write("-" * 80 + "\n")

def send_request(s):
    global request_log_timer

    body = (
        "-----------------------------22325320711689964980729421549\r\n"
        f"Content-Disposition: form-data; name=\"code\"\r\n\r\n"
        f"{s}\r\n"
        "-----------------------------22325320711689964980729421549--"
    )

    while True:
        pause_event.wait()

        try:
            response = requests.post(url, headers=headers, data=body)

            if time.time() - request_log_timer > request_log_interval:
                log_full_request(s, body, response)
                request_log_timer = time.time()
            
            if response.status_code == 200:
                logging.info(f'Successful code: {s}')
                update_queue.put(('hit', s))
                # Schedule GUI update for successful request
                root.after(0, lambda: log_text.insert(tk.END, f'Successful: {s} | Status Code: {response.status_code}\n'))
            elif response.status_code == 429:
                print(f'Received 429 Too Many Requests. Pausing for 30 seconds...')
                pause_event.clear()
                time.sleep(45)
                pause_event.set()
            else:
                logging.info(f'Failed code: {s} | Status Code: {response.status_code}')
                print(f'Sent: {s} | Status Code: {response.status_code}')
            
            break

        except requests.exceptions.RequestException as e:
            logging.info(f'Error with code: {s} | Exception: {e}')
            print(f'Failed to send: {s} | Error: {e}')
            break

def send_requests_threaded(starting_string, max_workers=10):
    pause_event.set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(send_request, generate_strings(starting_string))

def process_updates():
    while not update_queue.empty():
        status, code = update_queue.get()
        if status == 'hit':
            log_text.insert(tk.END, f'Successful code: {code}\n')
    root.after(100, process_updates)

def start_processing():
    starting_string = starting_string_entry.get()
    Thread(target=send_requests_threaded, args=(starting_string,)).start()
    root.after(100, process_updates)

root = tk.Tk()
root.title("Request Tracker")
root.geometry("800x600")  # Increase the size of the main window

# Add a frame for better layout management
frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

starting_string_label = tk.Label(frame, text="Starting String:", font=("Arial", 14))
starting_string_label.pack(pady=(0, 5))

starting_string_entry = tk.Entry(frame, font=("Arial", 14))
starting_string_entry.pack(pady=(0, 10))

start_button = tk.Button(frame, text="Start", command=start_processing, font=("Arial", 14))
start_button.pack()

# Add a scrollable text area for logging successful requests
log_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Arial", 12), height=20)
log_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

root.mainloop()
