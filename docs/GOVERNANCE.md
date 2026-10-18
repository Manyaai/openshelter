# Governance

- **Steering**: 3-seat technical committee elected by active maintainers; one
  seat reserved for a representative of a public-sector code-profile owner
  (this keeps the project aligned with its funders without capture).
- **Code profiles**: content OWNED by submitting authority; core team merges
  after automated validation (`tools/new_code_profile.py --check`) plus one
  human review. Disagreements about legal values go to the profile owner, not
  upstream — upstream only enforces schema correctness.
- **Decision records**: all policy decisions live as ADRs in docs/adr/.
- **Trademark**: "OpenShelter" held by a neutral foundation/legal entity;
  dual-licence revenue funds it.
- **Anti-fork trap**: everything that could be captured (data, profiles,
  roadmap templates) is federated; only the engine core is central.
