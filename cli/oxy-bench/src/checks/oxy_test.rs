use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::Path;
use std::process::Command;

pub struct CaseFailure {
    pub prompt: String,
    pub passed: usize,
    pub total: usize,
    pub failed_runs: Vec<FailedRun>,
}

pub struct FailedRun {
    pub cot: String,
    pub actual_output: String,
}

/// Run `oxy test <test_file> --format json` and return the average score (0.0–1.0).
/// Works for both .test.yml correctness files and .agent.yml files with embedded tests.
pub fn check(dir: &Path, test_file: &Path, db_url: Option<&str>, verbose: bool, show_failures: bool) -> Result<f32> {
    let mut cmd = Command::new("oxy");
    cmd.arg("test")
        .arg(test_file)
        .arg("--format")
        .arg("json");
    if verbose {
        cmd.arg("--verbose");
    }
    cmd.current_dir(dir);
    if let Some(url) = db_url {
        cmd.env("OXY_DATABASE_URL", url);
    }
    let output = cmd.output().context("Failed to run oxy test")?;

    let stderr = String::from_utf8_lossy(&output.stderr);
    if !stderr.trim().is_empty() {
        eprintln!("[oxy test] {}", stderr.trim());
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    if verbose {
        eprintln!("[oxy test output]\n{}", stdout.trim());
    }

    let (score, failures) = parse_results(&stdout)?;

    if show_failures && !failures.is_empty() {
        print_failures(&failures);
    }

    Ok(score)
}

fn print_failures(failures: &[CaseFailure]) {
    eprintln!("\n── Failed Cases ──────────────────────────────────────────");
    for (i, case) in failures.iter().enumerate() {
        eprintln!(
            "\n[{}] {}/{} runs passed  \"{}\"",
            i + 1,
            case.passed,
            case.total,
            truncate(&case.prompt, 120),
        );
        for (j, run) in case.failed_runs.iter().enumerate() {
            eprintln!("\n  Run {} — Judge reasoning:", j + 1);
            for line in case.failed_runs[j].cot.lines() {
                eprintln!("    {}", line);
            }
            eprintln!("\n  Agent response:");
            for line in run.actual_output.lines().take(20) {
                eprintln!("    {}", line);
            }
            if run.actual_output.lines().count() > 20 {
                eprintln!("    ... (truncated)");
            }
        }
    }
    eprintln!("\n──────────────────────────────────────────────────────────");
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() <= max {
        s.to_string()
    } else {
        format!("{}…", &s[..max])
    }
}

fn parse_results(raw: &str) -> Result<(f32, Vec<CaseFailure>)> {
    let stripped = strip_ansi(raw);
    let json = match stripped.find('[') {
        Some(pos) => &stripped[pos..],
        None => {
            if stripped.trim().is_empty() {
                return Ok((0.0, vec![]));
            }
            anyhow::bail!("oxy test output contained no JSON array. stdout: {}", &stripped.chars().take(200).collect::<String>());
        }
    };

    let results: Vec<EvalResult> = serde_json::from_str(json).with_context(|| {
        let preview: String = json.chars().take(200).collect();
        format!("Could not parse oxy test JSON output. stdout preview:\n{preview}")
    })?;

    let mut scores: Vec<f32> = Vec::new();
    let mut failures: Vec<CaseFailure> = Vec::new();

    for result in results {
        if let Some(metric) = result.metrics.into_iter().next() {
            scores.push(metric.score);

            if metric.score < 1.0 && !metric.records.is_empty() {
                let total = metric.records.len();
                let failed_runs: Vec<FailedRun> = metric.records.iter()
                    .filter(|r| r.choice.to_uppercase() != "PASS")
                    .map(|r| FailedRun {
                        cot: r.cot.clone(),
                        actual_output: r.actual_output.clone(),
                    })
                    .collect();
                let passed = total - failed_runs.len();
                let prompt = metric.records[0].prompt.clone();

                failures.push(CaseFailure { prompt, passed, total, failed_runs });
            }
        }
    }

    let score = if scores.is_empty() {
        0.0
    } else {
        scores.iter().sum::<f32>() / scores.len() as f32
    };

    Ok((score, failures))
}

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
                chars.next();
                loop {
                    match chars.next() {
                        Some('\x07') | None => break,
                        Some('\x1b') => { chars.next(); break; }
                        _ => {}
                    }
                }
            }
            Some(&'[') => {
                chars.next();
                loop {
                    match chars.next() {
                        Some(c) if c.is_ascii_alphabetic() => break,
                        None => break,
                        _ => {}
                    }
                }
            }
            _ => { chars.next(); }
        }
    }
    out
}

#[derive(Deserialize)]
struct EvalResult {
    metrics: Vec<Metric>,
}

#[derive(Deserialize)]
struct Metric {
    score: f32,
    #[serde(default)]
    records: Vec<Record>,
}

#[derive(Deserialize)]
struct Record {
    #[serde(default)]
    cot: String,
    #[serde(default)]
    choice: String,
    #[serde(default)]
    prompt: String,
    #[serde(default)]
    actual_output: String,
}
