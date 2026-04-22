mod build;
mod files;
pub mod oxy_test;
mod smoke;
mod validate;

use crate::spec::Spec;
use anyhow::Result;
use serde::Serialize;
use std::path::Path;

/// Results of all hard checks for one builder directory.
/// smoke and oxy_test_score are None if oxy build failed.
#[derive(Debug, Serialize)]
pub struct CheckResults {
    pub file_presence: FilePresenceResult,
    pub validate: PassFail,
    pub build: PassFail,
    pub smoke: Option<SmokeResult>,
    pub oxy_test_score: Option<f32>,
}

#[derive(Debug, Serialize)]
pub struct FilePresenceResult {
    pub pass: bool,
    pub counts: Vec<(String, usize)>, // e.g. [("topic", 2), ("agent", 1), ("view", 8)]
}

#[derive(Debug, Serialize, Clone, Copy, PartialEq)]
pub enum PassFail {
    Pass,
    Fail,
    Skipped,
}

#[derive(Debug, Serialize)]
pub struct SmokeResult {
    pub passing: usize,
    pub total: usize,
    pub score: f32,
}

/// Run all hard checks against the given directory.
/// test_file: path to the bench_consistency.test.yml or bench_eval.test.yml written by the skill.
/// If oxy build fails, smoke and oxy test are skipped.
pub fn run_all(dir: &Path, spec: &Spec, test_file: Option<&Path>) -> Result<CheckResults> {
    // OXY_DATABASE_URL is the PostgreSQL URL for oxy's internal state — read it directly
    // from the environment (it's already set by `oxy start --enterprise`).
    // spec.connection_env holds the Snowflake creds env var, which is unrelated.
    let db_url = std::env::var("OXY_DATABASE_URL").ok();
    let db_url_str = db_url.as_deref().unwrap_or_default();

    let file_presence = files::check(dir, &spec.required_artifacts)?;
    let validate = validate::check(dir)?;
    let build = build::check(dir, db_url_str)?;

    let (smoke, oxy_test_score) = if build == PassFail::Pass {
        let smoke = Some(smoke::check(dir, &spec.required_semantics, db_url_str)?);
        let oxy_test_score = match test_file {
            Some(tf) => Some(oxy_test::check(dir, tf, db_url.as_deref())?),
            None => None,
        };
        (smoke, oxy_test_score)
    } else {
        (None, None)
    };

    Ok(CheckResults {
        file_presence,
        validate,
        build,
        smoke,
        oxy_test_score,
    })
}
