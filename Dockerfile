FROM ubuntu:22.04

MAINTAINER jozo <hi@jozo.io>

ENV DEBIAN_FRONTEND=noninteractive

# Add user
RUN adduser --quiet --disabled-password qtuser && usermod -a -G audio qtuser

# This fix: libGL error: No matching fbConfigs or visuals found
ENV LIBGL_ALWAYS_INDIRECT=1

# Install Python 3, PyQt5
RUN apt-get update && apt-get install -y python3-pyqt5 python3-pip ssh

RUN sed -i 's/ForwardX11 no/ForwardX11 yes/g' /etc/ssh/ssh_config

RUN pip install pandas numpy pycoingecko web3==5.31.1 PyQt5 azure-identity msgraph-core

RUN pip install pyyaml matplotlib

COPY . /

#ENV QT_DEBUG_PLUGINS=1

#RUN export QT_DEBUG_PLUGINS=1

RUN export QT_X11_NO_MITSHM=1

CMD ["python3", "/main.py"]