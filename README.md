<!-- markdownlint-disable -->
<!-- prettier-ignore-start -->
> [!IMPORTANT]
> On June 26 2024, Linux Foundation announced the merger of its financial services umbrella, the Fintech Open Source Foundation ([FINOS](https://finos.org)), with OS-Climate, an open source community dedicated to building data technologies, modeling, and analytic tools that will drive global capital flows into climate change mitigation and resilience; OS-Climate projects are in the process of transitioning to the [FINOS governance framework](https://community.finos.org/docs/governance); read more on [finos.org/press/finos-join-forces-os-open-source-climate-sustainability-esg](https://finos.org/press/finos-join-forces-os-open-source-climate-sustainability-esg)
<!-- prettier-ignore-end -->
<!-- markdownlint-enable -->

# osc-dm-monitor-srv - Ecosystem Platform Monitor

Ecosystem Platform Monitor is a service for to monitor
components in Broda Group Software's Ecosystem Platform.

Full documentation is available in in the
[osc-dm-mesh-doc](https://github.com/brodagroupsoftware/osc-dm-mesh-doc)
repo.

This application interacts with other applications. You can run
the full set of applications by following instructions in the
[osc-dm-mesh-doc](https://github.com/brodagroupsoftware/osc-dm-mesh-doc)
repo.

The remaining sections explain how to Dockerize the application
as well as providing a few developer notes.

## Prerequisites

Python must be available, preferably in a virtual environment (venv).

## Setting up your Environment

Some environment variables are used by various source code and scripts.
Setup your environment as follows (note that "source" is used)

```console
source ./bin/environment.sh
```

It is recommended that a Python virtual environment be created.
We have provided several convenience scripts to create and activate
a virtual environment. To create a new virtual environment using
these convenience scripts, execute the following (this will
create a directory called "venv" in your current working directory):

```console
$PROJECT_DIR/bin/venv.sh
```

Once your virtual enviornment has been created, it can be activated
as follows (note: you _must_ activate the virtual environment
for it to be used, and the command requires "source" to ensure
environment variables to support venv are established correctly):

```console
source $PROJECT_DIR/bin/vactivate.sh
```

Install the required libraries as follows:

```console
pip install -r requirements.txt
```

Note that if you wish to run test cases then you will need
to also install "pytest" (it is not installed by default as
it is a development rather than product dependency).

```console
pip install pytest
```

## Creating a Docker Image

A Dockefile is provided for this service. A docker image for this
service can be creating using the following script:

```console
$PROJECT_DIR/bin/dockerize.sh
```

## Starting the Service

This service is designed to work with other services and
can be started with the full set of Data Mesh components.
Information about starting the full set of components
can be found [here](https://github.com/brodagroupsoftware/osc-dm-mesh-srv)

A standalone server can be started for testing purposes
using the following command:

```console
$PROJECT_DIR/app/start.sh
```
