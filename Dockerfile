FROM ubuntu:22.04

# Avoid tzdata interactive prompt during build
ENV DEBIAN_FRONTEND=noninteractive

# Update apt and install dependencies required to add the deadsnakes PPA
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    git \
    build-essential \
    ffmpeg \
    espeak-ng \
    libsndfile1 \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# Add the deadsnakes PPA to get modern Python versions
RUN add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000 (Required for HuggingFace Spaces)
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set working directory
WORKDIR $HOME/app

# Copy application files and change ownership
COPY --chown=user . $HOME/app

# Run the setup script to construct both virtual environments
RUN chmod +x setup.sh && ./setup.sh

# Expose HuggingFace Spaces default port
EXPOSE 7860

# Run the application using the main environment
CMD [".venv/bin/python", "-m", "streamlit", "run", "app/main.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.fileWatcherType=none"]
