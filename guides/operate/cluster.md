# Prepare a cluster for Nereus

Make a cluster that offers what Nereus needs, by hand, for [Install with Helm](helm.md); `nereus init --create-cluster` does the same for you.

## Before you start

What any cluster must offer, and how k3d and AKS meet it. AKS is there to compare and is **not tested**: no installation has run on it yet.

| Need | k3d | AKS (not tested) |
|---|---|---|
| Tools | Docker 20.10.5+, k3d 5.0.0+, Helm 4.0.0+ | `az`, Helm 4.0.0+ |
| Host | `fs.inotify.max_user_instances=1024` | the nodes are Azure's |
| Entrance: Gateway API kinds, a way to the Gateway | no Traefik; `127.0.0.1:8080` to the load balancer's port 80 | a `LoadBalancer` Service with a public IP, DNS and TLS in front |
| Images | the local registry, or `ghcr.io/getnereus/nereus` | `ghcr.io`, or a copy in an Azure Container Registry |
| Registry trust: every node trusts the local registry's CA | the CA's certificate mounted on every node | not needed: the nodes pull from a container registry such as ACR or `ghcr.io`, with credentials |
| The [registry reef](../reefs/registry.md): a registry in the cluster | its CA is the one of step 2, which every node trusts | [planned]: the nodes would have to trust its CA |
| API server: anonymous reads of the issuer's discovery only | an `AuthenticationConfiguration` on the server | `--enable-oidc-issuer`; the anonymous read is still to check |

On a machine that already has a k3d cluster named `nereus`, such as one kept for daily work, pick another name and port: replace `nereus` in the commands of step 5 and Clean up, and `8080` in `--port`.
| Storage: a default StorageClass | `local-path` | `managed-csi` |
| Network: NetworkPolicy enforced | k3s enforces it | `--network-policy azure`, `calico` or `cilium` |

## Steps

The steps make a k3d cluster; the registry CA of steps 2 and 3 is for its local registry. AKS follows after step 5.

### 1. Raise the host's inotify limit

With Ubuntu's default of 128, a second k3d cluster never starts. Raise it once per machine.

```bash
echo "fs.inotify.max_user_instances=1024" \
  | sudo tee /etc/sysctl.d/99-k3d-inotify.conf
sudo sysctl --system
```

### 2. Make the registry CA

A Registry answers only over TLS, with a certificate from one CA every node trusts. Its name constraints allow only `localhost` and names under `svc.cluster.local`, so trusting it trusts nothing else. Keep its files in a folder of your own, `nereus/`.

```bash
mkdir --parents nereus/registry
(umask 077 && openssl ecparam -name prime256v1 -genkey -noout -out nereus/ca.key)
openssl req -new -x509 -sha256 -days 3650 \
  -key nereus/ca.key \
  -out nereus/registry/ca.crt \
  -subj "/CN=Nereus registry CA" \
  -addext "basicConstraints=critical,CA:true,pathlen:0" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -addext "nameConstraints=critical,permitted;DNS:localhost,permitted;DNS:svc.cluster.local,excluded;IP:0.0.0.0/0.0.0.0,excluded;IP:::/::"
chmod 0755 nereus nereus/registry
chmod 0644 nereus/registry/ca.crt
```

### 3. Trust it for every registry

`nereus/registries.yaml` adds the CA to the roots of every registry the nodes pull from.

```yaml
configs:
  "*":
    tls:
      ca_file: /etc/nereus/registry/ca.crt
```

### 4. Open the issuer's discovery

zot reads the cluster issuer's discovery and keys with no token, to check a build's push token. k3s turns anonymous requests off; `nereus/authentication-config.yaml` lets them in on those two paths only.

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AuthenticationConfiguration
anonymous:
  enabled: true
  conditions:
    - path: /.well-known/openid-configuration
    - path: /openid/v1/jwks
```

### 5. Create the cluster

No load balancer, since k3d's is nginx, and the API on the loopback only (#2152); no Traefik, since the profile brings Istio's Gateway; the Gateway on port 8080 of the loopback; the CA on every node and the configuration on the server. Docker mounts absolute paths.

```bash
k3d cluster create nereus \
  --no-lb \
  --api-port "127.0.0.1:random" \
  --k3s-arg "--disable=traefik@server:*" \
  --port "127.0.0.1:8080:80@server:0:direct" \
  --registry-config nereus/registries.yaml \
  --volume "${PWD}/nereus/registry:/etc/nereus/registry@all" \
  --volume "${PWD}/nereus/authentication-config.yaml:/etc/rancher/nereus/authentication-config.yaml@server:*" \
  --k3s-arg "--kube-apiserver-arg=authentication-config=/etc/rancher/nereus/authentication-config.yaml@server:*" \
  --wait
```

Keep `nereus/`: the nodes mount it, the API server reads its file on every restart, and the chart `nereus` takes the CA from it.

On AKS, the same rows are flags of `az aks create`: `--network-plugin azure --network-policy azure`, `--enable-oidc-issuer` and `--enable-workload-identity`; a build pool is a node pool labelled and tainted `build.getnereus.dev/pool=build`.

## Check it worked

`kubectl get storageclass` shows `local-path` as the default, and `kubectl get nodes` shows every node Ready. After the install, [`nereus doctor`](../../specs/cli/core.html#doctor) says when the issuer's discovery is closed.

## Clean up

Delete the cluster with `k3d cluster delete nereus` and its folder with `rm -r nereus`.

## Next

- [Install with Helm](helm.md) on this cluster.

## Learn more

- [Runtime and profiles](../../concepts/runtime-and-profiles.md): what the profile installs on the cluster.
