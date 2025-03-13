# Snowflake-config
import os


def _snow_config():
    return {
        "user": os.environ["DBT_USR"],
        "authenticator": "externalbrowser",
        "account": "wx23413.europe-west4.gcp",
        "role": "securityadmin",
        "warehouse": "dev__xs",
    }