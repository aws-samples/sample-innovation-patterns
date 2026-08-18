# internal/

Maintainer-only tooling for this repository — the release machinery under `release/`,
the integration-test harness under `integration-tests/`, and the hand-installed AWS
infrastructure that runs that harness off a laptop under `infra/`. Nothing here is part
of what IPA delivers to a customer, and none of it is needed to use the generated
`scripts/*.mk`.

`infra/` is deliberately separate from the customer-facing `infra/cfn/` at the repository
root: those templates are shipped and composed by `/ipa-compose`, so pointing maintainer
CI at them would make a change made for the harness a breaking change for customers. See
`infra/README.md`.

**This directory is excluded from the public GitHub mirror.** `internal` is one of the
seven paths filtered by `internal/release/publish-github.sh`, so these files exist on
`code.aws.dev` only.

One exception, and it matters: **`internal/release/templates/` is public interface
despite living here.** It is the portable release standard, copied into customer
projects, so `CLAUDE.md`'s public/internal split treats a breaking change to it as
breaking. Everything else under `internal/` is internal interface, where no `!` applies
however sweeping the change.
