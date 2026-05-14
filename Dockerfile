# The devcontainer should use the developer target and run as root with podman
# or docker with user namespaces.
ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION} AS developer

# Add any system dependencies for the developer/build environment here
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl-dev libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 \
    libqt6gui6 libgl1 libxcb-cursor0 libgles2-mesa-dev graphviz \
    && rm -rf /var/lib/apt/lists/*

# Set up a virtual environment and put it in PATH
RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH

# The build stage installs the context into the venv
FROM developer AS build
# Requires buildkit 0.17.0
RUN ls -l
COPY --chmod=777 . /workspaces/dls-bba
WORKDIR /workspaces/dls-bba
RUN touch dev-requirements.txt && pip install -c dev-requirements.txt .


# The runtime stage copies the built venv into a slim runtime container
FROM python:${PYTHON_VERSION}-slim AS runtime
# Add apt-get system dependecies for runtime here if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl-dev libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 \
    libqt6gui6 libgl1 libxcb-cursor0 libgles2-mesa-dev graphviz
COPY --from=build /venv/ /venv/
ENV PATH=/venv/bin:$PATH

# change this entrypoint if it is not the same as the repo
ENTRYPOINT ["dls-bba-gui"]
CMD ["--version"]
