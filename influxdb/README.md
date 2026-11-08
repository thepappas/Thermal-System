# InfluxDB

The stack initializes InfluxDB v2 with organization `hvac` and bucket `hvac`.
The Node-RED flow writes measurement `hvac`, numeric fields named in
`nodered/README.md` and the flow, with millisecond timestamps and no tags.
The bucket has InfluxDB's default infinite retention; size storage and choose
retention deliberately. Token setup and backup are in `docs/operations.md`.
