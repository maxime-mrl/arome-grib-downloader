FROM ubuntu:22.04

# Install dependencies required for GDAL and repository management
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    software-properties-common \
    build-essential \
    lsb-release \
    python3 \
    python3-pip \
    python3-dev \
    git \
    # Add dependencies for wgrib2
    gcc \
    make \
    gfortran \
    cmake \
    #
    libnetcdf-dev \
    libpng-dev \
    zlib1g-dev \
    libopenjp2-7-dev \
    #
    && apt-get clean

# Add UbuntuGIS repository and key
RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable

# Update package list and install GDAL and its dependencies
RUN rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    gdal-bin \
    libgdal-dev \
    python3-gdal

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Download and build wgrib2 with USE_IPOLATES=1 and a patch for Fortran compilation
ENV FC=gfortran
ENV CC=gcc
RUN cd /tmp && \
    wget https://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz && \
    tar -xzf wgrib2.tgz && \
    cd grib2 && \
    sed -i 's/USE_IPOLATES=0/USE_IPOLATES=1/' makefile && \
    make && \
    cp wgrib2/wgrib2 /usr/local/bin/ && \
    chmod +x /usr/local/bin/wgrib2 && \
    cd /tmp && \
    rm -rf grib2 wgrib2.tgz

# Create working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy your Python files
COPY . .

# Default command (can be overridden)
CMD ["python3"]
