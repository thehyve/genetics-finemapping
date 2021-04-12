FROM continuumio/miniconda:4.6.14

# create non-root user
RUN useradd -ms /bin/bash my-user
USER my-user

# Conda and the envirounment dependencies
COPY ./environment.yaml /home/my-user/finemapping/
WORKDIR /home/my-user/finemapping
RUN conda env create -n finemapping --file environment.yaml
RUN echo "source activate finemapping" > ~/.bashrc
ENV PATH /home/my-user/.conda/envs/finemapping/bin:$PATH

# Install OpenJDK-8 (as root)
USER root
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk && \
    apt-get install -y ant && \
    apt-get clean;

# Fix certificate issues (as root)
RUN apt-get update && \
    apt-get install ca-certificates-java && \
    apt-get clean && \
    update-ca-certificates -f;
USER my-user

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

# Install GCTA
USER root
RUN apt-get install unzip
RUN wget https://cnsgenomics.com/software/gcta/bin/gcta_1.92.3beta3.zip -P /software/gcta
RUN chown -R my-user:my-user /software/gcta
USER my-user
RUN unzip /software/gcta/gcta_1.92.3beta3.zip -d /software/gcta
RUN rm /software/gcta/gcta_1.92.3beta3.zip
ENV PATH="/software/gcta/gcta_1.92.3beta3:${PATH}"

# Install parallel
USER root
RUN apt install -yf parallel
USER my-user

# Google Cloud SDK
RUN curl https://sdk.cloud.google.com | bash

# Default command
CMD ["/bin/bash"]

# Copy the v2d project
COPY ./ /home/my-user/finemapping

# Make all files in finemapping owned by the non-root user
USER root
RUN chown -R my-user:my-user /home/my-user/finemapping

# Run container as non-root user
USER my-use
