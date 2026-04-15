use crate::checks::oxy_test;
use anyhow::Result;
use serde::Serialize;
use std::path::Path;

#[derive(Debug, Serialize)]
pub struct RegressionResult {
    pub test_file: String,
    pub score: f32,
}

/// Run oxy test against an existing test file in an existing instance directory.
/// No build checks — the instance is assumed to already be built and running.
pub fn run(dir: &Path, test_file: &Path) -> Result<RegressionResult> {
    let db_url = std::env::var("OXY_DATABASE_URL").unwrap_or_default();
    let score = oxy_test::check(dir, test_file, &db_url)?;

    Ok(RegressionResult {
        test_file: test_file.display().to_string(),
        score,
    })
}

pub fn print(result: &RegressionResult) {
    println!("\n## Regression Check");
    println!("Test file:  {}", result.test_file);
    println!("Score:      {:.0}%", result.score * 100.0);
    println!();
}
