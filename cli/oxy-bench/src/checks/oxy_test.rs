use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::Path;
use std::process::Command;

/// Run `oxy test <test_file> --output-json` and return the overall score (0.0–1.0).
/// Works for both consistency and test_case eval files.
pub fn check(dir: &Path, test_file: &Path, db_url: &str) -> Result<f32> {
    let output = Command::new("oxy")
        .arg("test")
        .arg(test_file)
        .arg("--output-json")
        .current_dir(dir)
        .env("OXY_DATABASE_URL", db_url)
        .output()
        .context("Failed to run oxy test")?;

    // oxy test writes results JSON to stdout
    let stdout = String::from_utf8_lossy(&output.stdout);
    parse_score(&stdout)
}

/// Parse the overall score out of the oxy test --output-json output.
///
/// Expected shape (array of EvalResult):
/// [{ "metrics": [{ "type": "Consistency"|"Correctness", "score": 0.82, ... }] }]
fn parse_score(json: &str) -> Result<f32> {
    let results: Vec<EvalResult> = serde_json::from_str(json)
        .context("Could not parse oxy test JSON output")?;

    // Take the score from the first metric of the first result
    let score = results
        .into_iter()
        .next()
        .and_then(|r| r.metrics.into_iter().next())
        .map(|m| m.score)
        .unwrap_or(0.0);

    Ok(score)
}

#[derive(Deserialize)]
struct EvalResult {
    metrics: Vec<Metric>,
}

#[derive(Deserialize)]
struct Metric {
    score: f32,
}
