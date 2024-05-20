# Copyright 2024 Broda Group Software Inc.
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
#
# Created:  2024-04-15 by eric.broda@brodagroupsoftware.com

import asyncio

# Library imports
import logging

import uvicorn as uvicorn
import yaml
from fastapi import FastAPI, HTTPException

import state

# Project imports
import utilities
from middleware import LoggingMiddleware

# Set up logging
LOGGING_FORMAT = \
    "%(asctime)s - %(module)s:%(funcName)s %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)

# Constants
ENDPOINT_MONITOR = "/monitor"
ENDPOINT_PREFIX = "/api" + ENDPOINT_MONITOR
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_CONFIGURATION = "./config/config.yaml"

STATE_CONFIGURATION = "state-configuration"
STATE_METRICS = "state-statistics"
STATE_HEALTH = "state-health"
STATE_ADDRESSES = "state-addresses"

SERVICE_REGISTRAR = "osc-dm-registrar-srv"
SERVICE_SEARCH = "osc-dm-search-srv"
SERVICE_PROXY = "osc-dm-proxy-srv"

HEADER_USERNAME = "OSC-DM-Username"
HEADER_CORRELATION_ID = "OSC-DM-Correlation-ID"
USERNAME = "osc-dm-search-srv"

#####
# STARTUP
#####

# Set up server
app = FastAPI()
app.add_middleware(LoggingMiddleware)

@app.on_event("startup")
async def startup_event():
    """
    At startup, immediately check status and then periodically thereafter
    """
    configuration = state.gstate(STATE_CONFIGURATION)
    logger.info("Running startup event")
    param1 = "fake param 1"
    param2 = "fake param 2"

    logger.info("Running task immediately...")
    await _task(param1, param2)  # Immediate invocation at startup

    interval = configuration["monitor"]["interval_seconds"]
    logger.info(f"Running task interval (seconds):{interval}")
    asyncio.create_task(_repeat_every(configuration["monitor"]["interval_seconds"], _task, param1, param2))  # Periodic invocation


#####
# ENDPOINTS
#####


@app.get(ENDPOINT_PREFIX + "/health")
async def health_get():
    """
    Return health information
    """
    statistics = state.gstate(STATE_HEALTH)
    return statistics


@app.get(ENDPOINT_PREFIX + "/metrics")
async def metrics_get():
    """
    Return metrics information
    """
    metrics = state.gstate(STATE_METRICS)
    return metrics


#####
# INTERNAL
#####


async def _task(param1, param2):
    """
    Load data from registrar
    """
    logger.info(f"Executing task param1:{param1} param2:{param2}")

    health = state.gstate(STATE_HEALTH)
    metrics = state.gstate(STATE_METRICS)
    addresses = state.gstate(STATE_ADDRESSES)

    configuration = state.gstate(STATE_CONFIGURATION)
    host = configuration["proxy"]["host"]
    port = configuration["proxy"]["port"]
    service = "/api/registrar/products"
    method = "GET"

    # Get all known products from registrar
    response = None
    try:
        logger.info("Get products")
        import uuid
        headers = {
            HEADER_USERNAME: USERNAME,
            HEADER_CORRELATION_ID: str(uuid.uuid4())
        }
        response = await utilities.httprequest(host, port, service, method, headers=headers)
        logger.info("Get products SUCCESS")
    except Exception as e:
        logger.error(f"Error getting product information, exception:{e}")

    # Get address for all health checks and add to addresses to check
    if response:
        products = response
        for product in products:
            logger.info(f"Using product:{product}")
            address = product["address"]
            uuid = product["uuid"]
            endpoint = f"/api/dataproducts/uuid/{uuid}"
            addresses[address] = endpoint

    # Get info (health) from each service and data product
    logger.info(f"Current health:{health}")
    for address in addresses:
        try:
            logger.info(f"Getting health address:{address}")
            service = addresses[address] + "/health"
            method = "GET"
            import uuid
            headers = {
                HEADER_USERNAME: USERNAME,
                HEADER_CORRELATION_ID: str(uuid.uuid4())
            }
            response = await utilities.httprequest(host, port, service, method, headers=headers)
            health[address] = "OK"
            logger.info(f"Successful getting health address:{address} response:{response}")
        except Exception as e:
            logger.error(f"Error getting health address:{address}, exception:{e}")
            health[address] = "NOT-OK"
    logger.info(f"Full health:{health}")

    # Get info (metrics) from each service and data product
    logger.info(f"Current metrics:{metrics}")
    for address in addresses:
        try:
            logger.info(f"Getting metrics address:{address}")
            service = addresses[address] + "/metrics"
            method = "GET"
            headers = {
                HEADER_USERNAME: USERNAME,
                HEADER_CORRELATION_ID: str(uuid.uuid4())
            }
            response = await utilities.httprequest(host, port, service, method, headers=headers)
            metrics[address] = response
            logger.info(f"Successful getting metrics address:{address} response:{response}")
        except Exception as e:
            logger.error(f"Error getting metrics address:{address}, exception:{e}")
            metrics[address] = "NOT-AVAILABLE"
    logger.info(f"Full metrics:{metrics}")


async def _repeat_every(interval_sec, func, *args):
    """
    Setup a periodically called function
    """
    import asyncio
    while True:
        await func(*args)
        await asyncio.sleep(interval_sec)




#####
# MAINLINE
#####


if __name__ == "__main__":
    # Set up argument parsing
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help=f"Host for the server (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port for the server (default: {DEFAULT_PORT})")
    parser.add_argument("--configuration", type=str, default=DEFAULT_CONFIGURATION, help=f"Configuration file (default: {DEFAULT_CONFIGURATION})")
    args = parser.parse_args()

    logger.info(f"Using args.host:{args.host}")
    logger.info(f"Using args.port:{args.port}")
    logger.info(f"Using args.configuration:{args.configuration}")
    logger.info(f"Using current working directory:{os.getcwd()}")
    logger.info(f"Contents of current working directory:{os.listdir()}")

    # Read the configuration file
    configuration = None
    with open(args.configuration, 'r') as file:
        configuration = yaml.safe_load(file)
    logger.info(f"Configuration:{configuration}")
    state.gstate(STATE_CONFIGURATION, configuration)

    addresses = {
        SERVICE_PROXY: "/api/proxy",
        SERVICE_REGISTRAR: "/api/registrar",
        SERVICE_SEARCH: "/api/search",
    }
    state.gstate(STATE_ADDRESSES, addresses)

    health = {
        SERVICE_PROXY: "UNKNOWN",
        SERVICE_REGISTRAR: "UNKNOWN",
        SERVICE_SEARCH: "UNKNOWN",
    }
    state.gstate(STATE_HEALTH, health)

    metrics = {
        SERVICE_PROXY: {},
        SERVICE_REGISTRAR: {},
        SERVICE_SEARCH: {},
    }
    state.gstate(STATE_METRICS, metrics)

    # Start the server
    try:
        logger.info(f"Startingservice on host:{args.host} port:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    except Exception as e:
        logger.info(f"Stopping service, exception:{e}")
    finally:
        logger.info(f"Terminating service")
