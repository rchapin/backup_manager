FROM alpine:3.13.1

ARG root_passwd

RUN apk add --no-cache \
    openssh \
    rsync \
    # Ensure that we can passwordlessly ssh to this host
    && sed -i '/PermitRootLogin/d' /etc/ssh/sshd_config \
    && echo "PermitRootLogin yes" >> /etc/ssh/sshd_config \
    # Generate keys for the ssh server
    && ssh-keygen -A \
    # Create a known password for the root user
    && echo "root:$root_passwd" | chpasswd

EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]

