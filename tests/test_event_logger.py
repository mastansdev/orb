from event_logger import event_logger

event_logger.system(
    event="TEST_EVENT",
    message="Testing Event Logger"
)

print("Event Logged Successfully")