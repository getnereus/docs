# The notifications reef

Every command that tells a person something and the devices that receive it.

## Commands

- [`nereus notify "Deploy k3d-nereus?"`](../../specs/cli/reefs/notifications.html#notify) notify is the short form agents use
- [`nereus notifications notification create`](../../specs/cli/reefs/notifications.html#notification-create) create builds a Notification from flags
- [`nereus notifications notification list`](../../specs/cli/reefs/notifications.html#notification-list) list shows what was delivered of what was asked
- [`nereus notifications subscription create`](../../specs/cli/reefs/notifications.html#subscription-create) create subscribes one of your devices from the file its browser gave
- [`nereus notifications subscription list`](../../specs/cli/reefs/notifications.html#subscription-list) list shows your own devices, never their endpoints

## Examples

### notify

Tell alice, in one line.

```bash
nereus notify "Deploy k3d-nereus?" \
  --to user/alice
```

``` { .text .output title="output" }
✓ notification n-20261122-0001 created for user/alice (kind note)

Next steps:

  nereus notifications notification get n-20261122-0001
```

### notification-create

A decision, with a title and the page it leads to.

```bash
nereus notifications notification create \
  --to user/alice \
  --title "#2078 merged" \
  --text "Deploy k3d-nereus?" \
  --kind decision \
  --url https://portal.example.com/
```

``` { .text .output title="output" }
✓ notification n-20261122-0002 created for user/alice (kind decision)

Next steps:

  nereus notifications notification get n-20261122-0002
```

### notification-list

alice's notifications: delivered over the devices it went to.

```bash
nereus notifications notification list \
  --to user/alice
```

``` { .text .output title="output" }
NAME             KIND      TITLE         DELIVERED  AGE
n-20261122-0001  note      -             0/1        5s
n-20261122-0002  decision  #2078 merged  1/1        1m
```

### subscription-create

The PushSubscription JSON, read from a file: the endpoint is never on a command line.

```bash
nereus notifications subscription create \
  --from-file push.json \
  --agent "Chrome on Android"
```

``` { .text .output title="output" }
✓ subscription s-3f2a9c created

Next steps:

  nereus notifications subscription list
```

### subscription-list

The caller's own devices.

```bash
nereus notifications subscription list
```

``` { .text .output title="output" }
NAME       USER        AGENT              AGE
s-3f2a9c   user/alice  Chrome on Android  2d
```
