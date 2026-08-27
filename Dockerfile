# The devcontainer should use the developer target and run as root with podman
# or docker with user namespaces.
FROM ghcr.io/diamondlightsource/ubuntu-devcontainer:noble AS developer

# Add any system dependencies for the developer/build environment here
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl-dev libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 \
    libqt6gui6 libgl1 libxcb-cursor0 libgles2-mesa-dev graphviz \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get dist-clean

# The build stage installs the context into the venv
FROM developer AS build

# Change the working directory to the `app` directory
# and copy in the project
WORKDIR /app
COPY . /app
RUN chmod o+wrX .

# Tell uv sync to install python in a known location so we can copy it out later
ENV UV_PYTHON_INSTALL_DIR=/python

# Sync the project without its dev dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev --managed-python

# The runtime stage copies the built venv into a runtime container
FROM ubuntu:resolute AS runtime

# Add apt-get system dependecies for runtime here if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl-dev libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 \
    libqt6gui6 libgl1 libxcb-cursor0 libgles2-mesa-dev graphviz \
    && apt-get dist-clean

# Copy the python installation from the build stage
COPY --from=build /python /python

# Copy the environment, but not the source code
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH

# change this entrypoint if it is not the same as the repo
ENTRYPOINT ["dls-bba-gui"]
CMD ["--version"]
