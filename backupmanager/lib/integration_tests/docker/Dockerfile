FROM alpine:3.13.1
RUN apk add --no-cache \
    openssh \
    rsync \
    # Ensure that we can passwordlessly ssh to this host
    && sed -i '/PermitRootLogin/d' /etc/ssh/sshd_config
    && echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]

