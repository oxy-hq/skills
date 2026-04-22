use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::Path;
use std::process::Command;

/// Run `oxy test <test_file> --format json` and return the average score (0.0–1.0).
/// Works for both .test.yml correctness files and .agent.yml files with embedded tests.
pub fn check(dir: &Path, test_file: &Path, db_url: Option<&str>) -> Result<f32> {
    let mut cmd = Command::new("oxy");
    cmd.arg("test")
        .arg(test_file)
        .arg("--format")
        .arg("json")
        .current_dir(dir);
    if let Some(url) = db_url {
        cmd.env("OXY_DATABASE_URL", url);
    }
    let output = cmd.output().context("Failed to run oxy test")?;

    // oxy test writes results JSON to stdout
    let stdout = String::from_utf8_lossy(&output.stdout);
    parse_score(&stdout)
}

/// Parse the average score from `oxy test --format json` output.
///
/// Expected shape — array of per-case results:
/// [{ "metrics": [{ "type": "Similarity"|"Correctness"|"Consistency", "score": 0.82, ... }] }]
///
/// Each entry corresponds to one test case. We average the first metric's score
/// across all cases (ignoring entries with no metrics).
/// Strip ANSI/VT escape sequences from a string.
/// Handles OSC (\x1b]...\x07 or \x1b]\x1b\\) and CSI (\x1b[...letter) sequences.
fn strip_ansi(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let mut chars = input.chars().peekable();
    while let Some(ch) = chars.next() {
        if ch != '\x1b' {
            out.push(ch);
            continue;
        }
        match chars.peek() {
            Some(&']') => {
                // OSC: \x1b] ... \x07  or  \x1b] ... \x1b\
                chars.next();
                loop {
                    match chars.next() {
                        Some('\x07') | None => break,
                        Some('\x1b') => { chars.next(); break; } // consume the \
                        _ => {}
                    }
                }
            }
            Some(&'[') => {
                // CSI: \x1b[ ... <letter>
                chars.next();
                loop {
                    match chars.next() {
                        Some(c) if c.is_ascii_alphabetic() => break,
                        None => break,
                        _ => {}
                    }
                }
            }
            _ => { chars.next(); } // skip single-char escape
        }
    }
    out
}

fn parse_score(raw: &str) -> Result<f32> {
    // oxy test emits terminal escape sequences before the JSON array — strip them first.
    let stripped = strip_ansi(raw);
    let json = match stripped.find('[') {
        Some(pos) => &stripped[pos..],
        None => {
            if stripped.trim().is_empty() {
                return Ok(0.0);
            }
            anyhow::bail!("oxy test output contained no JSON array. stdout: {}", &stripped.chars().take(200).collect::<String>());
        }
    };

    let results: Vec<EvalResult> = serde_json::from_str(json).with_context(|| {
        let preview: String = json.chars().take(200).collect();
        format!("Could not parse oxy test JSON output. stdout preview:\n{preview}")
    })?;

    let scores: Vec<f32> = results
        .into_iter()
        .filter_map(|r| r.metrics.into_iter().next())
        .map(|m| m.score)
        .collect();

    if scores.is_empty() {
        return Ok(0.0);
    }

    Ok(scores.iter().sum::<f32>() / scores.len() as f32)
}

#[derive(Deserialize)]
struct EvalResult {
    metrics: Vec<Metric>,
}

#[derive(Deserialize)]
struct Metric {
    score: f32,
}
