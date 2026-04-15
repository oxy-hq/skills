use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::Path;

/// Top-level .build-bench.yml structure.
/// The CLI only reads the fields it needs for hard checks — build_prompt and
/// builders are used by the skill and ignored here.
#[derive(Debug, Deserialize)]
pub struct Spec {
    pub name: String,
    pub database: String,
    pub connection_env: String,
    #[serde(default)]
    pub required_artifacts: Vec<ArtifactRequirement>,
    #[serde(default)]
    pub required_semantics: Vec<SemanticRequirement>,
}

/// One entry under required_artifacts — e.g. { type: topic }
#[derive(Debug, Deserialize)]
pub struct ArtifactRequirement {
    #[serde(rename = "type")]
    pub artifact_type: String, // "topic", "agent", "view"
}

/// One entry under required_semantics — topic to smoke-test and measures to check
#[derive(Debug, Deserialize)]
pub struct SemanticRequirement {
    pub topic_contains: String,
    #[serde(default)]
    pub must_have_measures: Vec<String>,
}

pub fn load(path: &Path) -> Result<Spec> {
    let contents = std::fs::read_to_string(path)
        .with_context(|| format!("Could not read spec file: {}", path.display()))?;
    let spec: Spec = serde_yaml::from_str(&contents)
        .with_context(|| format!("Could not parse spec file: {}", path.display()))?;
    Ok(spec)
}
