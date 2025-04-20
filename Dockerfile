FROM ubuntu:22.04

RUN apt update && \
    apt install -y openssh-server sudo && \
    mkdir /var/run/sshd && \
    echo 'root:root' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/Port 22/Port 22\nPort 443\nPort 80\nPort 8080\nPort 2022\nPort 5080\nPort 3001/' /etc/ssh/sshd_config && \
    echo "PermitEmptyPasswords no" >> /etc/ssh/sshd_config

EXPOSE 22 443 80 8080 2022 5080 3001

CMD ["/usr/sbin/sshd", "-D"]
