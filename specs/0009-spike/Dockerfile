# A hostile build for the gVisor spike of #1117: it only looks, and prints what it sees.
FROM busybox:1.37@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
RUN echo "== uname"; uname -a; \
    echo "== /proc/version"; cat /proc/version; \
    echo "== dmesg"; dmesg 2>&1 | head -5; \
    echo "== id"; id; \
    echo "== /proc"; ls /proc | tr '\n' ' '; echo; \
    echo "== unshare"; unshare --user --map-root-user --mount sh -c 'mount -t tmpfs none /mnt && echo mounted' 2>&1; \
    echo "== mount"; mount -t tmpfs none /mnt 2>&1 && echo mounted; \
    gateway="$(ip route | awk '/default/ {print $3}')"; echo "== gateway ${gateway}"; \
    for port in 6443 10250; do nc -z -w 3 "${gateway}" "${port}" && echo "node ${port} open" || echo "node ${port} closed"; done; \
    nc -z -w 3 10.43.0.1 443 && echo "kubernetes service open" || echo "kubernetes service closed"
