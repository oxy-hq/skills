mod checks;
mod regress;
mod report;
mod score;
mod spec;

use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "oxy-bench", about = "Benchmark and regression-test Oxy instances")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Evaluate a freshly built Oxy instance: hard checks + oxy test + composite score.
    /// Used by the oxy-build-bench skill after running a builder.
    Eval {
        /// Path to the built Oxy instance directory
        #[arg(long)]
        dir: PathBuf,

        /// Path to the .build-bench.yml spec file
        #[arg(long)]
        spec: PathBuf,

        /// Path to the bench_consistency.test.yml or bench_eval.test.yml written by the skill.
        /// If omitted, oxy test is skipped and consistency score will be 0.
        #[arg(long)]
        test_file: Option<PathBuf>,

        /// Output format: "pretty" (default) or "json"
        #[arg(long, default_value = "pretty")]
        format: String,

        /// Exit with code 1 if composite score is below this threshold (0.0–1.0)
        #[arg(long)]
        min_accuracy: Option<f32>,
    },

    /// Run oxy test against an existing instance and existing test file.
    /// Skips all build checks — use for CI/CD regression testing of live instances.
    Regress {
        /// Path to the existing Oxy instance directory
        #[arg(long)]
        dir: PathBuf,

        /// Path to the existing .test.yml file to run
        #[arg(long)]
        test_file: PathBuf,

        /// Output format: "pretty" (default) or "json"
        #[arg(long, default_value = "pretty")]
        format: String,

        /// Exit with code 1 if score is below this threshold (0.0–1.0)
        #[arg(long)]
        min_accuracy: Option<f32>,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Command::Eval { dir, spec, test_file, format, min_accuracy } => {
            let spec = spec::load(&spec)?;
            let result = checks::run_all(&dir, &spec, test_file.as_deref())?;
            let composite = score::composite(&result, &spec);

            if format == "json" {
                println!("{}", serde_json::to_string_pretty(&composite)?);
            } else {
                report::print(&result, &composite, &spec);
            }

            if let Some(threshold) = min_accuracy {
                if composite.score < threshold {
                    std::process::exit(1);
                }
            }
        }

        Command::Regress { dir, test_file, format, min_accuracy } => {
            let result = regress::run(&dir, &test_file)?;

            if format == "json" {
                println!("{}", serde_json::to_string_pretty(&result)?);
            } else {
                regress::print(&result);
            }

            if let Some(threshold) = min_accuracy {
                if result.score < threshold {
                    std::process::exit(1);
                }
            }
        }
    }

    Ok(())
}
