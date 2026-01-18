# [0.1.0](https://github.com/antonbabenko/terraform-skill/compare/v2.0.0...v0.1.0) (2026-01-18)


### Bug Fixes

* **claude-plugin:** Update marketplace.json version and source structure ([2bca71c](https://github.com/antonbabenko/terraform-skill/commit/2bca71c90817c9b29da161fd4339d2acf4abdaeb))



# [2.0.0](https://github.com/antonbabenko/terraform-skill/compare/v1.1.0...v2.0.0) (2026-01-17)


* feat!: migrate to marketplace-only architecture ([f32de12](https://github.com/antonbabenko/terraform-skill/commit/f32de1253af5e62c159c85c5016afa4557978d67))


### BREAKING CHANGES

* Removed plugin.json in favor of marketplace.json.

Changes:
- Migrate source type from 'local' to 'github'
- Add version synchronization (marketplace, plugin, git ref)
- Update workflows for marketplace.json validation and releases
- Update documentation references

Users must reinstall:
  /plugin marketplace remove terraform-skill
  /plugin marketplace add antonbabenko/terraform-skill



# [1.1.0](https://github.com/antonbabenko/terraform-skill/compare/4f1a017efb63283fc4499dc5328505d4a7829671...v1.1.0) (2026-01-17)


### Features

* initial release of terraform-skill v1.0.0 ([4f1a017](https://github.com/antonbabenko/terraform-skill/commit/4f1a017efb63283fc4499dc5328505d4a7829671))



