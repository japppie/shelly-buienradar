import modal
import os
import sys

# Add the src directory to Python's path so it can be imported both locally and inside Modal
sys.path.insert(0, os.path.abspath("src"))

# Create a mount for the src directory so Modal ships it to the cloud
src_mount = modal.Mount.from_local_dir("src", remote_path="/root/src")

# Define the Modal app with required packages
app = modal.App("shelly_automation")


@app.function(
    secrets=[modal.Secret.from_name("shelly-secret")],
    schedule=modal.Cron("*/6 7-23 * * *"),  # Every 6 minutes between 07:00 and 23:00
    image=modal.Image.debian_slim().pip_install("requests", "python-dotenv"),
    mounts=[src_mount],
)
def scheduled_task():
    # Import inside the function so it doesn't try to load it globally before mounting
    from shelly_buienradar.core import check_and_close_sunscreen

    check_and_close_sunscreen(is_cloud=True)


if __name__ == "__main__":
    with app.run():
        scheduled_task()
