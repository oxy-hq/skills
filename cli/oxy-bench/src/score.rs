use crate::checks::{CheckResults, PassFail};
use crate::spec::Spec;
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct CompositeScore {
    pub score: f32,
    pub level: u8,
    pub structural: f32,
    pub smoke: f32,
    pub consistency: f32,
    pub ask_quality: Option<f32>, // Level 2 only
}

/// Compute the composite score from check results.
///
/// Level 1 weights:  structural 20%, smoke 30%, consistency 50%
/// Level 2 weights:  structural 15%, smoke 20%, consistency 15%, ask_quality 50%
pub fn composite(results: &CheckResults, _spec: &Spec) -> CompositeScore {
    let structural = structural_score(results);
    let smoke = results.smoke.as_ref().map(|s| s.score).unwrap_or(0.0);
    let consistency = results.oxy_test_score.unwrap_or(0.0);
    let ask_quality = None::<f32>; // Level 2 not yet implemented

    let (score, level) = if ask_quality.is_some() {
        let s = 0.15 * structural + 0.20 * smoke + 0.15 * consistency + 0.50 * ask_quality.unwrap();
        (s, 2u8)
    } else {
        let s = 0.20 * structural + 0.30 * smoke + 0.50 * consistency;
        (s, 1u8)
    };

    CompositeScore { score, level, structural, smoke, consistency, ask_quality }
}

fn structural_score(results: &CheckResults) -> f32 {
    let file = if results.file_presence.pass { 1.0 } else { 0.0 };
    let validate = pass_to_f32(results.validate);
    let build = pass_to_f32(results.build);
    (file + validate + build) / 3.0
}

fn pass_to_f32(p: PassFail) -> f32 {
    match p {
        PassFail::Pass => 1.0,
        PassFail::Fail | PassFail::Skipped => 0.0,
    }
}
