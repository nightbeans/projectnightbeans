-- MOPO scoreboard data queries
--
-- Run by the Monday-morning Claude agent against MOPO Databot. Each query is
-- wrapped in a name=... block. The agent splits these and executes them one
-- at a time via the MCP execute_query tool.
--
-- All queries validated against live Databot 2026-05-01.
--
-- Conventions:
--   - DRR (USD) = SUM(rental_income / crh.rate_usd) / SUM(available)
--     joining currency_rates_history with is_parallel_rate = 0
--   - Country scope: country_code='NG', product_type=1, is_test_hub=0
--   - "This week" = last 7 days ending yesterday; "prior week" = the 7 days before that
--   - Tenure threshold for lead measures: > 14 days in role
--
-- Note: lead_earnings (regional P25 floor) is left as a placeholder pending
-- access to the Apr 2026 baseline floor table. Scoreboard will show a
-- placeholder value for that card until the SQL is filled in.


-- name=country_drr
-- Returns: ONE row {drr_current, drr_prior}
SELECT
  ROUND(SUM(CASE WHEN week='current' THEN rev_usd END) / NULLIF(SUM(CASE WHEN week='current' THEN available END), 0), 4) AS drr_current,
  ROUND(SUM(CASE WHEN week='prior' THEN rev_usd END) / NULLIF(SUM(CASE WHEN week='prior' THEN available END), 0), 4) AS drr_prior
FROM (
  SELECT
    CASE
      WHEN aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY) THEN 'current'
      WHEN aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND DATE_SUB(CURDATE(), INTERVAL 8 DAY) THEN 'prior'
    END AS week,
    aprd.rental_income / NULLIF(crh.rate_usd, 0) AS rev_usd,
    aprd.available
  FROM agent_performance_rollups_daily aprd
  JOIN hubs h ON aprd.hub_id = h.hub_id
  JOIN hub_business_policies bp ON h.hub_business_policy_id = bp.hub_business_policy_id
  JOIN currencies cur ON bp.currency_code = cur.currency_code
  JOIN currency_rates_history crh ON crh.currency_id = cur.id AND crh.date = aprd.date AND crh.is_parallel_rate = 0
  WHERE h.country_code = 'NG' AND h.product_type = 1 AND h.is_test_hub = 0
    AND aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
) weekly;


-- name=regions
-- Returns: rows of {region, hubs, drr_usd, prior_drr_usd}
SELECT
  r.name AS region,
  hub_count.hubs,
  ROUND(SUM(CASE WHEN week='current' THEN rev_usd END) / NULLIF(SUM(CASE WHEN week='current' THEN available END), 0), 4) AS drr_usd,
  ROUND(SUM(CASE WHEN week='prior' THEN rev_usd END) / NULLIF(SUM(CASE WHEN week='prior' THEN available END), 0), 4) AS prior_drr_usd
FROM (
  SELECT
    h.region_id,
    CASE
      WHEN aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY) THEN 'current'
      WHEN aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND DATE_SUB(CURDATE(), INTERVAL 8 DAY) THEN 'prior'
    END AS week,
    aprd.rental_income / NULLIF(crh.rate_usd, 0) AS rev_usd,
    aprd.available
  FROM agent_performance_rollups_daily aprd
  JOIN hubs h ON aprd.hub_id = h.hub_id
  JOIN hub_business_policies bp ON h.hub_business_policy_id = bp.hub_business_policy_id
  JOIN currencies cur ON bp.currency_code = cur.currency_code
  JOIN currency_rates_history crh ON crh.currency_id = cur.id AND crh.date = aprd.date AND crh.is_parallel_rate = 0
  WHERE h.country_code = 'NG' AND h.product_type = 1 AND h.is_test_hub = 0
    AND aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
) weekly
JOIN region r ON r.id = weekly.region_id
JOIN (
  SELECT region_id, COUNT(DISTINCT hub_id) AS hubs
  FROM hubs
  WHERE country_code = 'NG' AND product_type = 1 AND is_test_hub = 0
  GROUP BY region_id
) hub_count ON hub_count.region_id = weekly.region_id
GROUP BY r.name, hub_count.hubs
ORDER BY drr_usd DESC;


-- name=lead_relative
-- Returns: ONE row {total_agents, above_threshold, flagged_agents}
-- Flagged = agent DRR < 35% of their hub's best DRR (>14 day tenure)
SELECT
  COUNT(*) AS total_agents,
  SUM(CASE WHEN ad.drr_usd >= 0.35 * hb.best_drr THEN 1 ELSE 0 END) AS above_threshold,
  SUM(CASE WHEN ad.drr_usd < 0.35 * hb.best_drr THEN 1 ELSE 0 END) AS flagged_agents
FROM (
  SELECT aprd.agent_id, aprd.hub_id,
    SUM(aprd.rental_income / NULLIF(crh.rate_usd, 0)) / NULLIF(SUM(aprd.available), 0) AS drr_usd
  FROM agent_performance_rollups_daily aprd
  JOIN hubs h ON aprd.hub_id = h.hub_id
  JOIN hub_business_policies bp ON h.hub_business_policy_id = bp.hub_business_policy_id
  JOIN currencies cur ON bp.currency_code = cur.currency_code
  JOIN currency_rates_history crh ON crh.currency_id = cur.id AND crh.date = aprd.date AND crh.is_parallel_rate = 0
  JOIN agent_hub_assignment_history ahah ON ahah.agent_id = aprd.agent_id AND ahah.hub_id = aprd.hub_id AND ahah.deleted_at IS NULL
  WHERE h.country_code = 'NG' AND h.product_type = 1 AND h.is_test_hub = 0
    AND aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
    AND DATEDIFF(CURDATE(), ahah.created_at) > 14
  GROUP BY aprd.agent_id, aprd.hub_id
) ad
JOIN (
  SELECT inner_ad.hub_id, MAX(inner_ad.drr_usd) AS best_drr
  FROM (
    SELECT aprd2.agent_id, aprd2.hub_id,
      SUM(aprd2.rental_income / NULLIF(crh2.rate_usd, 0)) / NULLIF(SUM(aprd2.available), 0) AS drr_usd
    FROM agent_performance_rollups_daily aprd2
    JOIN hubs h2 ON aprd2.hub_id = h2.hub_id
    JOIN hub_business_policies bp2 ON h2.hub_business_policy_id = bp2.hub_business_policy_id
    JOIN currencies cur2 ON bp2.currency_code = cur2.currency_code
    JOIN currency_rates_history crh2 ON crh2.currency_id = cur2.id AND crh2.date = aprd2.date AND crh2.is_parallel_rate = 0
    WHERE h2.country_code = 'NG' AND h2.product_type = 1 AND h2.is_test_hub = 0
      AND aprd2.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
    GROUP BY aprd2.agent_id, aprd2.hub_id
  ) inner_ad
  GROUP BY inner_ad.hub_id
) hb ON hb.hub_id = ad.hub_id;


-- name=lead_earnings
-- Placeholder until the regional P25 floor table is wired in. Returns the same
-- total_agents as lead_relative with above_floor = total and below_floor = 0.
-- The Monday agent will surface a card showing 0% flagged for earnings until
-- this is replaced with a real query against the Apr 2026 P25 floor reference.
SELECT
  COUNT(*) AS total_agents,
  COUNT(*) AS above_floor,
  0 AS below_floor
FROM (
  SELECT aprd.agent_id, aprd.hub_id
  FROM agent_performance_rollups_daily aprd
  JOIN hubs h ON aprd.hub_id = h.hub_id
  JOIN agent_hub_assignment_history ahah ON ahah.agent_id = aprd.agent_id AND ahah.hub_id = aprd.hub_id AND ahah.deleted_at IS NULL
  WHERE h.country_code = 'NG' AND h.product_type = 1 AND h.is_test_hub = 0
    AND aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
    AND DATEDIFF(CURDATE(), ahah.created_at) > 14
  GROUP BY aprd.agent_id, aprd.hub_id
) agents_observed;


-- name=flagged_agents
-- Returns: rows of {hub_name, region, hub_drr, agent_name, agent_drr, rel_perf, hub_best_drr, weekly_ngn, days_in_role}
-- Limited to 60 rows (worst-performing first) — the dashboard's focus list shows the priority hubs.
SELECT
  h.name AS hub_name,
  r.name AS region,
  ROUND(hub_drr_calc.hub_drr, 4) AS hub_drr,
  a.name AS agent_name,
  ROUND(ad.drr_usd, 4) AS agent_drr,
  ROUND(100 * ad.drr_usd / NULLIF(hb.best_drr, 0), 0) AS rel_perf,
  ROUND(hb.best_drr, 4) AS hub_best_drr,
  ROUND(ad.weekly_ngn, 0) AS weekly_ngn,
  DATEDIFF(CURDATE(), MIN(ahah.created_at)) AS days_in_role
FROM (
  SELECT aprd.agent_id, aprd.hub_id,
    SUM(aprd.rental_income / NULLIF(crh.rate_usd, 0)) / NULLIF(SUM(aprd.available), 0) AS drr_usd,
    SUM(aprd.rental_income) AS weekly_ngn
  FROM agent_performance_rollups_daily aprd
  JOIN hubs h2 ON aprd.hub_id = h2.hub_id
  JOIN hub_business_policies bp ON h2.hub_business_policy_id = bp.hub_business_policy_id
  JOIN currencies cur ON bp.currency_code = cur.currency_code
  JOIN currency_rates_history crh ON crh.currency_id = cur.id AND crh.date = aprd.date AND crh.is_parallel_rate = 0
  WHERE h2.country_code = 'NG' AND h2.product_type = 1 AND h2.is_test_hub = 0
    AND aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
  GROUP BY aprd.agent_id, aprd.hub_id
) ad
JOIN (
  SELECT inner_ad.hub_id, MAX(inner_ad.drr_usd) AS best_drr
  FROM (
    SELECT aprd2.agent_id, aprd2.hub_id,
      SUM(aprd2.rental_income / NULLIF(crh2.rate_usd, 0)) / NULLIF(SUM(aprd2.available), 0) AS drr_usd
    FROM agent_performance_rollups_daily aprd2
    JOIN hubs h3 ON aprd2.hub_id = h3.hub_id
    JOIN hub_business_policies bp2 ON h3.hub_business_policy_id = bp2.hub_business_policy_id
    JOIN currencies cur2 ON bp2.currency_code = cur2.currency_code
    JOIN currency_rates_history crh2 ON crh2.currency_id = cur2.id AND crh2.date = aprd2.date AND crh2.is_parallel_rate = 0
    WHERE h3.country_code = 'NG' AND h3.product_type = 1 AND h3.is_test_hub = 0
      AND aprd2.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
    GROUP BY aprd2.agent_id, aprd2.hub_id
  ) inner_ad
  GROUP BY inner_ad.hub_id
) hb ON hb.hub_id = ad.hub_id
JOIN (
  SELECT aprd3.hub_id,
    SUM(aprd3.rental_income / NULLIF(crh3.rate_usd, 0)) / NULLIF(SUM(aprd3.available), 0) AS hub_drr
  FROM agent_performance_rollups_daily aprd3
  JOIN hubs h4 ON aprd3.hub_id = h4.hub_id
  JOIN hub_business_policies bp3 ON h4.hub_business_policy_id = bp3.hub_business_policy_id
  JOIN currencies cur3 ON bp3.currency_code = cur3.currency_code
  JOIN currency_rates_history crh3 ON crh3.currency_id = cur3.id AND crh3.date = aprd3.date AND crh3.is_parallel_rate = 0
  WHERE h4.country_code = 'NG' AND h4.product_type = 1 AND h4.is_test_hub = 0
    AND aprd3.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
  GROUP BY aprd3.hub_id
) hub_drr_calc ON hub_drr_calc.hub_id = ad.hub_id
JOIN hubs h ON h.hub_id = ad.hub_id
JOIN region r ON r.id = h.region_id
JOIN agents a ON a.agent_id = ad.agent_id
JOIN agent_hub_assignment_history ahah ON ahah.agent_id = ad.agent_id AND ahah.hub_id = ad.hub_id AND ahah.deleted_at IS NULL
WHERE ad.drr_usd < 0.35 * hb.best_drr
  AND DATEDIFF(CURDATE(), ahah.created_at) > 14
GROUP BY h.name, r.name, hub_drr_calc.hub_drr, a.name, ad.drr_usd, hb.best_drr, ad.weekly_ngn
ORDER BY hub_drr ASC, rel_perf ASC
LIMIT 60;


-- name=new_agents
-- Returns: rows of {region, new_agents, avg_drr_usd, above_target, progressing, below_baseline}
-- Validated query (the Fix 4 corrected version).
SELECT
  r.name AS region,
  COUNT(DISTINCT ahah.agent_id) AS new_agents,
  ROUND(AVG(agent_drr.drr_usd), 2) AS avg_drr_usd,
  SUM(CASE WHEN agent_drr.drr_usd >= 0.18 THEN 1 ELSE 0 END) AS above_target,
  SUM(CASE WHEN agent_drr.drr_usd >= 0.13 AND agent_drr.drr_usd < 0.18 THEN 1 ELSE 0 END) AS progressing,
  SUM(CASE WHEN agent_drr.drr_usd < 0.13 THEN 1 ELSE 0 END) AS below_baseline
FROM agent_hub_assignment_history ahah
JOIN hubs h ON h.hub_id = ahah.hub_id
JOIN region r ON h.region_id = r.id
JOIN (
  SELECT
    aprd.agent_id, aprd.hub_id,
    ROUND(SUM(aprd.rental_income / NULLIF(crh.rate_usd, 0)) / NULLIF(SUM(aprd.available), 0), 4) AS drr_usd
  FROM agent_performance_rollups_daily aprd
  JOIN hubs h2 ON aprd.hub_id = h2.hub_id
  JOIN hub_business_policies bp ON h2.hub_business_policy_id = bp.hub_business_policy_id
  JOIN currencies cur ON bp.currency_code = cur.currency_code
  JOIN currency_rates_history crh
    ON crh.currency_id = cur.id AND crh.date = aprd.date AND crh.is_parallel_rate = 0
  WHERE h2.country_code = 'NG' AND h2.product_type = 1 AND h2.is_test_hub = 0
    AND aprd.date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
  GROUP BY aprd.agent_id, aprd.hub_id
) agent_drr ON agent_drr.agent_id = ahah.agent_id AND agent_drr.hub_id = ahah.hub_id
WHERE h.country_code = 'NG' AND h.product_type = 1 AND h.is_test_hub = 0
  AND ahah.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
  AND ahah.deleted_at IS NULL
  AND DATEDIFF(CURDATE(), ahah.created_at) BETWEEN 7 AND 30
GROUP BY r.name
ORDER BY avg_drr_usd DESC;


-- name=window_dates
-- Returns: ONE row {window_start, window_end}
SELECT
  DATE_SUB(CURDATE(), INTERVAL 7 DAY) AS window_start,
  DATE_SUB(CURDATE(), INTERVAL 1 DAY) AS window_end;
