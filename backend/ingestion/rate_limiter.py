import time                        # time = to get current time in seconds
from collections import deque      # deque = a special list (explained below)
from fastapi import Request, HTTPException
# Request = represents the incoming HTTP request
# HTTPException = a way to send error responses back

# ─── What is a deque? ─────────────────────────────────────────
# deque = double ended queue
# Think of it like a sliding window of timestamps
# Example: [1.0, 1.2, 1.4, 1.6, 1.8]  ← timestamps of last 5 requests
# When window slides past 1 second, old timestamps fall off the left side

class RateLimiter:
    # __init__ = constructor, called when we create a RateLimiter object
    def __init__(self, max_requests: int, window_seconds: float = 1.0):
        # max_requests = how many requests allowed per window
        # window_seconds = the time window size (default = 1 second)

        self.max_requests = max_requests
        # save max_requests so other methods can use it
        # self = "this object", like "this" in Java

        self.window = window_seconds
        # save window size

        self.requests = deque()
        # empty deque to store timestamps of recent requests
        # example after 3 requests: deque([1.0, 1.3, 1.7])

    async def __call__(self, request: Request, call_next):
        # __call__ = makes this object work like a function
        # FastAPI calls this for EVERY incoming request automatically
        # request = the incoming HTTP request
        # call_next = function to call the actual route handler

        now = time.time()
        # time.time() = current time as float
        # example: 1714500000.123

        # ── Step 1: Remove old timestamps outside the window ──
        while self.requests and self.requests[0] < now - self.window:
            # self.requests = our deque of timestamps
            # self.requests[0] = oldest timestamp (left side of deque)
            # now - self.window = 1 second ago
            # if oldest timestamp is older than 1 second → remove it
            self.requests.popleft()
            # popleft() = remove from left side of deque

        # ── Step 2: Check if we are over the limit ──
        if len(self.requests) >= self.max_requests:
            # len() = count of items in deque
            # if count >= max → too many requests
            raise HTTPException(
                status_code=429,
                # 429 = HTTP status code for "Too Many Requests"
                detail="Rate limit exceeded. Max 10,000 signals/sec."
                # detail = error message sent back to client
            )

        # ── Step 3: Record this request's timestamp ──
        self.requests.append(now)
        # append = add to right side of deque
        # now we have a record that a request happened at this time

        # ── Step 4: Let the request through ──
        return await call_next(request)
        # call_next = call the actual route handler
        # await = wait for it to finish
        # return its response back to the client

# ─── HOW IT WORKS (Simple Example) ───────────────────────────
# max_requests = 3, window = 1 second
#
# Request 1 arrives at t=0.0  → deque=[0.0]           → allowed
# Request 2 arrives at t=0.3  → deque=[0.0, 0.3]      → allowed
# Request 3 arrives at t=0.6  → deque=[0.0, 0.3, 0.6] → allowed
# Request 4 arrives at t=0.8  → deque still has 3 items → BLOCKED 429
# Request 5 arrives at t=1.1  → 0.0 is now old, removed → deque=[0.3, 0.6, 1.1] → allowed