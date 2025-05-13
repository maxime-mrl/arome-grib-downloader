FROM ubuntu:22.04

# Set the locale for deps which require it
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

RUN apt-get update && \
    apt-get install -y --no-install-recommends locales && \
    sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

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
    
# install miniconda
ENV PATH=/opt/conda/bin:$PATH \
CONDA_AUTO_UPDATE_CONDA=false
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
-O /tmp/miniconda.sh && \
bash /tmp/miniconda.sh -b -p /opt/conda && \
rm /tmp/miniconda.sh
# install xaray and cfgrib and xesmf
RUN conda install -y -c conda-forge xarray cfgrib xesmf gdal && \
conda clean -afy

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

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
