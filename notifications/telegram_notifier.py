import time
import requests
from queue import Queue
from threading import Thread, Timer


class TelegramNotifier:

    # Fix (2026-07-20): the old design used exactly ONE worker
    # thread processing the queue strictly sequentially, with
    # retries done via time.sleep(5) INSIDE that same worker --
    # blocking it from picking up anything else in the queue for
    # up to 25s per failing message (5 retries x 5s). Confirmed
    # live: this produced a 63-minute delay on a real trade alert
    # (SPLPETRO) during a busy window where many messages queued
    # up back-to-back. A small pool of workers means one message
    # retrying doesn't freeze delivery for everything behind it.
    WORKER_COUNT = 3

    # Retry backoff, in seconds, per attempt (5 attempts total).
    RETRY_DELAYS = [2, 4, 8, 15, 30]

    # Fix (2026-07-20): Telegram rejects any single message over
    # 4096 characters with "Bad Request: message is too long" --
    # confirmed live on /brief. But cmd_brief is not unique --
    # telegram_command_center.py has ~10 other report commands
    # (cmd_fno, cmd_exposure, cmd_eod, cmd_execution, cmd_causal,
    # etc.) that all funnel their output through this same send()
    # method, so any of them could hit the same wall as reports
    # grow. Fixed once, here, instead of patching each command
    # individually. Kept a bit under the real 4096 limit for
    # formatting headroom.
    MAX_MESSAGE_LENGTH = 4000

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.queue = Queue()

        # Start a small pool of background worker threads instead
        # of one -- lets multiple messages be in-flight (or
        # retrying) at the same time.
        for i in range(self.WORKER_COUNT):
            Thread(
                target=self._worker,
                daemon=True,
                name=f"TelegramWorker-{i}"
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

                    self._schedule_retry(item)

            except Exception as e:
                print("\n========== TELEGRAM EXCEPTION ==========")
                print(e)
                self._schedule_retry(item)
                print("========================================\n")

            finally:
                self.queue.task_done()

    # --------------------------------------------------

    def _schedule_retry(self, item):
        """
        Fix (2026-07-20): retries used to block the worker thread
        via time.sleep() -- meaning the worker sat idle, unable to
        process anything else in the queue, for the entire wait.
        Now the retry is scheduled with a non-blocking Timer, and
        this worker returns immediately to pick up the next queued
        message right away. The retried item re-enters the SAME
        queue once its delay elapses, to be picked up by whichever
        worker is free at that point.
        """
        retry = item["retry"]

        if retry >= len(self.RETRY_DELAYS):
            print(
                f"Telegram message discarded after "
                f"{len(self.RETRY_DELAYS)} retries."
            )
            return

        delay = self.RETRY_DELAYS[retry]
        item["retry"] = retry + 1

        print(f"Retrying in {delay}s... ({item['retry']}/{len(self.RETRY_DELAYS)})")

        Timer(delay, self.queue.put, args=(item,)).start()

    # --------------------------------------------------

    def send(self, message):
        for chunk in self._split_message(message):
            self.queue.put({
                "message": chunk,
                "retry": 0
            })

    # --------------------------------------------------

    def _split_message(self, message):
        """
        Split a message into pieces that each fit under
        MAX_MESSAGE_LENGTH, breaking at line boundaries where
        possible so words/sentences don't get cut mid-way. Falls
        back to a hard split only for a single line that's
        somehow longer than the limit on its own.
        """
        if len(message) <= self.MAX_MESSAGE_LENGTH:
            return [message]

        chunks = []
        current = ""

        for line in message.split("\n"):

            if len(current) + len(line) + 1 > self.MAX_MESSAGE_LENGTH:
                if current:
                    chunks.append(current)
                    current = ""

                # A single line longer than the limit on its own --
                # no good boundary to split on, hard-split it.
                while len(line) > self.MAX_MESSAGE_LENGTH:
                    chunks.append(line[:self.MAX_MESSAGE_LENGTH])
                    line = line[self.MAX_MESSAGE_LENGTH:]

            current = f"{current}\n{line}" if current else line

        if current:
            chunks.append(current)

        # Mark multi-part messages so it's clear in Telegram that
        # these sequential messages belong together.
        if len(chunks) > 1:
            chunks = [
                f"({i}/{len(chunks)})\n{chunk}"
                for i, chunk in enumerate(chunks, start=1)
            ]

        return chunks