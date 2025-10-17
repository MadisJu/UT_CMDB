import time
from fastapi import Request

# Middleware on kood, mis jookseb iga sissetuleva päringu ja väljamineva vastuse puhul.
async def add_process_time_header(request: Request, call_next):
    """
    See middleware mõõdab, kui kaua API päringu töötlemine aega võttis,
    ja lisab selle info vastuse päisesse (header).
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response