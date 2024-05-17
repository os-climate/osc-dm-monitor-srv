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
import state
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
DEFAULT_CONFIGURATION="./config/config.yaml"

STATE_CONFIGURATION="state-configuration"
STATE_STATISTICS="state-statistics"

SERVICE_REGISTRAR="osc-dm-registrar-srv"
SERVICE_SEARCH="osc-dm-search-srv"
SERVICE_PROXY="osc-dm-proxy-srv"

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
    await _task(param1, param2)  # Immediate invocation at startup
    asyncio.create_task(_repeat_every(configuration["monitor"]["interval_seconds"], _task, param1, param2))  # Periodic invocation


#####
# ENDPOINTS
#####


@app.get(ENDPOINT_PREFIX + "/health")
async def health_get():
    """
    Return health information
    """
    statistics = state.gstate(STATE_STATISTICS)
    return statistics


@app.get(ENDPOINT_PREFIX + "/metrics")
async def health_get():
    """
    Return health information
    """
    statistics = state.gstate(STATE_STATISTICS)
    return statistics


#####
# INTERNAL
#####


async def _task(param1, param2):
    """
    Load data from registrar
    """
    logger.info(f"Executing task param1:{param1} param2:{param2}")

    statistics = state.gstate(STATE_STATISTICS)

    configuration = state.gstate(STATE_CONFIGURATION)
    host = configuration["proxy"]["host"]
    port = configuration["proxy"]["port"]
    service = "/api/registrar/products"
    method = "GET"

    # Get all known products from registrar
    response = None
    try:
        logger.info("Get products")
        response = await utilities.httprequest(host, port, service, method)
        logger.info("Get products SUCCESS")
    except Exception as e:
        logger.error(f"Error getting product information, exception:{e}")

    # Get addresses for all products and add to
    if response:
        products = response
        for product in products:
            logger.info(f"Using product:{product}")
            address = product["address"]
            uuid = product["uuid"]
            endpoint = f"/api/dataproducts/uuid/{uuid}"
            statistics[address] = { "endpoint": endpoint, "health": "UNKNOWN"}

    # Get info (health and metrics) from each service and data product
    logger.info(f"Current statistics:{statistics}")
    for name in statistics:
        try:
            logger.info(f"Getting status name:{name} info:{statistics[name]}")
            service = statistics[name]["endpoint"]
            method = "GET"
            response = await utilities.httprequest(host, port, service, method)
            statistics[name]["health"] = "OK"
            logger.info(f"Getting status name:{name} SUCCESS (UP)")
        except Exception as e:
            logger.error(f"Error getting status name:{name} info:{statistics[name]}, exception:{e}")
            statistics[name]["health"] = "NOT-OK"
    logger.info(f"Full statistics:{statistics}")


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

    statistics = {
        SERVICE_PROXY: {"endpoint": "/api/proxy/health", "health": "UNKNOWN" },
        SERVICE_REGISTRAR: {"endpoint": "/api/registrar/health", "health": "UNKNOWN" },
        SERVICE_SEARCH: {"endpoint": "/api/search/health", "health": "UNKNOWN" }
    }
    state.gstate(STATE_STATISTICS, statistics)


    # Start the server
    try:
        logger.info(f"STARTING service on host:{args.host} port:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    except Exception as e:
        logger.info(f"STOPPING service, exception:{e}")
    finally:
        logger.info(f"TERMINATING service on host:{args.host} port:{args.port}")
