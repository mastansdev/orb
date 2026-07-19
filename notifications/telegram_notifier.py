import time
import requests
from queue import Queue
from threading import Thread


class TelegramNotifier:

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.queue = Queue()

        # Start the background worker thread
        Thread(
            target=self._worker,
            daemon=True
        ).start()

    # --------------------------------------------------

    def _worker(self):
        while True:
            item = self.queue.get()
            message = item["message"]
            retry = item["retry"]

            try:
                response = requests.post(
                    self.url,
                    data={
                        "chat_id": self.chat_id,
                        "text": message
                    },
                    timeout=10
                )
                result = response.json()

                if result.get("ok", False):
                    print("✅ Telegram Message Delivered")
                else:
                    print("\n========== TELEGRAM ERROR ==========")
                    print(result)
                    print("====================================\n")

                    if retry < 5:
                        item["retry"] += 1
                        time.sleep(5)
                        self.queue.put(item)

            except Exception as e:
                print("\n========== TELEGRAM EXCEPTION ==========")
                print(e)
                
                if retry < 5:
                    print(f"Retrying... ({retry + 1}/5)")
                    item["retry"] += 1
                    time.sleep(5)
                    self.queue.put(item)
                else:
                    print("Telegram message discarded after 5 retries.")
                    
                print("========================================\n")

            finally:
                self.queue.task_done()

    # --------------------------------------------------

    def send(self, message):
        self.queue.put({
            "message": message,
            "retry": 0
        })