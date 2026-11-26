# The build reef

Every command that builds an image from a Workload's source inside the cluster.

## Commands

- [`nereus build create hello-1`](../../specs/cli/reefs/build.html#build-create) create builds a Workload at the commit its Nereid read
- [`nereus build get hello-1`](../../specs/cli/reefs/build.html#build-get) get shows the digest the registry answered
- [`nereus build list`](../../specs/cli/reefs/build.html#build-list) list shows every build, a line each
- [`nereus build get app-1`](../../specs/cli/reefs/build.html#build-private) A private repository is fetched with a token for that build alone
- [`nereus build delete hello-1`](../../specs/cli/reefs/build.html#build-delete) delete removes the Build and its Job, never the image
- [`nereus build trigger create triton`](../../specs/cli/reefs/build.html#trigger-create) trigger create builds a Workload on each new commit of its Mirror
- [`nereus build trigger list`](../../specs/cli/reefs/build.html#trigger-list) trigger list shows the commit each one saw and its last Build
- [`nereus build trigger get triton`](../../specs/cli/reefs/build.html#trigger-get) trigger get shows the Mirror it follows and the commit it saw
- [`nereus build trigger delete triton`](../../specs/cli/reefs/build.html#trigger-delete) trigger delete stops new Builds and leaves the ones it made

## Examples

### build-create

Two Jobs in the namespace builds: fetch, then build and push.

```bash
nereus build create hello-1 \
  --workload hello
```

``` { .text .output title="output" }
build/builds/hello-1 created (mandate: buildkit, nereid: buildkit)

Next steps:

  nereus build get hello-1
```

### build-get

Its phase, image and digest.

```bash
nereus build get hello-1
```

``` { .text .output title="output" }
Name:      hello-1
Workload:  hello
Commit:    a1b2c3d4e5f60718293a4b5c6d7e8f9012345678
Owner:     -
Mandate:   -
Nereid:    buildkit
Phase:     Succeeded
Image:     localhost:31874/hello:hello-1
Digest:    sha256:3517762d3517762d3517762d3517762d3517762d3517762d3517762d3517762d
Job:       hello-1
```

### build-list

The Workload, the commit, the phase and the digest.

```bash
nereus build list
```

``` { .text .output title="output" }
BUILD    WORKLOAD  COMMIT   STATUS     DIGEST
hello-1  hello     a1b2c3d  Succeeded  sha256:3517762d3517
hello-2  hello     -        Pending    -
```

### build-private

An allow line for builds on the App's Mandate, then the Build.

```bash
nereus build get app-1
```

``` { .text .output title="output" }
Name:      app-1
Workload:  app
Phase:     Running
Message:   source fetched at a1b2c3d from https://github.com/example/app with a token for example/app (contents=read)
```

### build-delete

The image it pushed stays in its Repository.

```bash
nereus build delete hello-1
```

``` { .text .output title="output" }
build/builds/hello-1 deleted

Next steps:

  nereus build list
```

### trigger-create

The Mirror nereus copies the source of the Workload triton.

```bash
nereus build trigger create triton \
  --workload triton
```

``` { .text .output title="output" }
build/triggers/triton created (mandate: buildkit, nereid: buildkit)

Next steps:

  nereus build trigger get triton
```

### trigger-list

After a push, once the Mirror pulled it.

```bash
nereus build trigger list
```

``` { .text .output title="output" }
TRIGGER  WORKLOAD  MIRROR  COMMIT   LAST BUILD      STATUS
triton   triton    nereus  a1b2c3d  triton-a1b2c3d  Ready
```

### trigger-get

Its Mirror, branch, commit and last Build.

```bash
nereus build trigger get triton
```

``` { .text .output title="output" }
Name:        triton
Workload:    triton
Owner:       project/triton
Mandate:     -
Nereid:      buildkit
Mirror:      nereus
Branch:      main
Commit:      a1b2c3d4e5f60718293a4b5c6d7e8f9012345678
Last Build:  triton-a1b2c3d
Status:      Ready
```

### trigger-delete

No new Build of triton; triton-a1b2c3d stays.

```bash
nereus build trigger delete triton
```

``` { .text .output title="output" }
build/triggers/triton deleted; the Builds it created stay

Next steps:

  nereus build trigger list
```
