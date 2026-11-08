# Deployment and safety

This release is a reference implementation for monitoring and advisory use,
not a certified safety controller. Review the bundled safety and commissioning
documentation before installation; do not connect actuators without a
qualified, site-specific design and independent safety interlocks.

The `thermal-system-*.tar.gz` bundle contains the tracked deployment
configuration, templates, documentation, and tools for this tag. Verify it
against `SHA256SUMS` before use. Firmware binaries are not included: customize
the ESPHome templates and build locally with your own credentials and sensor
addresses. See `esphome/README.md` and `docs/operations.md` in the bundle.
