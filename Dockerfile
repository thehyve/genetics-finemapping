FROM continuumio/miniconda:4.6.14

# Conda and the envirounment dependencies
COPY ./environment.yaml /finemapping/
WORKDIR /finemapping
RUN conda env create -n finemapping --file environment.yaml
RUN echo "source activate finemapping" > ~/.bashrc
ENV PATH /opt/conda/envs/finemapping/bin:$PATH

# Install OpenJDK-8
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk && \
    apt-get install -y ant && \
    apt-get clean;

# Fix certificate issues
RUN apt-get update && \
    apt-get install ca-certificates-java && \
    apt-get clean && \
    update-ca-certificates -f;

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

# Install GCTA
RUN apt-get install unzip
RUN wget https://cnsgenomics.com/software/gcta/bin/gcta_1.92.3beta3.zip -P /software/gcta
RUN unzip /software/gcta/gcta_1.92.3beta3.zip -d /software/gcta
RUN rm /software/gcta/gcta_1.92.3beta3.zip
ENV PATH="/software/gcta/gcta_1.92.3beta3:${PATH}"

RUN apt install -yf parallel

# Google Cloud SDK
RUN curl https://sdk.cloud.google.com | bash

# Default command
CMD ["/bin/bash"]

# Copy the v2d project
COPY ./ /finemapping