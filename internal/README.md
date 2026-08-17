# internal/

Maintainer-only tooling for this repository — the release machinery under `release/`
and the integration-test harness under `integration-tests/`. Nothing here is part of
what IPA delivers to a customer, and none of it is needed to use the generated
`scripts/*.mk`.

**This directory is excluded from the public GitHub mirror.** `internal` is one of the
seven paths filtered by `internal/release/publish-github.sh`, so these files exist on
`code.aws.dev` only.

One exception, and it matters: **`internal/release/templates/` is public interface
despite living here.** It is the portable release standard, copied into customer
projects, so `CLAUDE.md`'s public/internal split treats a breaking change to it as
breaking. Everything else under `internal/` is internal interface, where no `!` applies
however sweeping the change.
